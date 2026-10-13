#!/usr/bin/env python3
"""
Gera legenda SRT a partir de um video ou audio, sem alterar nenhuma palavra do que foi dito.

O script extrai o audio com ffmpeg, transcreve com faster-whisper (large-v3 por padrao)
e monta as legendas respeitando limites de leitura: no maximo 2 linhas, 42 caracteres
por linha e 6 segundos por legenda. As quebras seguem o fim das frases.

Uso:
    python3 scripts/transcrever.py videos/meu-video.mp4
    python3 scripts/transcrever.py videos/meu-video.mp4 --termos "Cratheon, HeyGen"
    python3 scripts/transcrever.py videos/meu-video.mp4 --salvar-palavras revisao.json
    python3 scripts/transcrever.py videos/meu-video.mp4 --palavras revisao.json
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

MAX_CARACTERES_LINHA = 42
MAX_LINHAS = 2
MAX_CARACTERES_LEGENDA = MAX_CARACTERES_LINHA * MAX_LINHAS
MAX_DURACAO = 6.0
MIN_DURACAO = 1.0
PAUSA_QUE_QUEBRA = 0.8
TAMANHO_DE_LEGENDA_CURTA = 24

FIM_DE_FRASE = (".", "!", "?", "…")
PAUSA_INTERNA = (",", ";", ":")

# Terminar a legenda em artigo, preposicao ou conjuncao separa palavras que se leem
# juntas, entao estas vao para a legenda seguinte quando caem no fim de uma quebra.
PALAVRAS_QUE_NAO_FECHAM_LEGENDA = frozenset(
    """
    a an the and or of to in on at by for with that this as but from into
    o os as um uma uns umas de do da dos das em no na nos nas e ou que para
    com por ao aos num numa pelo pela seu sua meu minha
    """.split()
)


@dataclass
class Palavra:
    texto: str
    inicio: float
    fim: float


@dataclass
class Legenda:
    palavras: list[Palavra] = field(default_factory=list)

    @property
    def inicio(self) -> float:
        return self.palavras[0].inicio

    @property
    def fim(self) -> float:
        return self.palavras[-1].fim

    @property
    def texto(self) -> str:
        return " ".join(p.texto for p in self.palavras)


# ----------------------------------------------------------------------------- audio


def extrair_audio(entrada: Path, destino: Path) -> None:
    comando = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(entrada),
        "-vn", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(destino),
    ]
    subprocess.run(comando, check=True)


def duracao_do_arquivo(caminho: Path) -> float:
    comando = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(caminho),
    ]
    saida = subprocess.run(comando, check=True, capture_output=True, text=True).stdout.strip()
    try:
        return float(saida)
    except ValueError:
        return 0.0


def ler_wav(caminho: Path):
    """Le um WAV mono de 16 kHz e 16 bits como vetor float32 entre -1 e 1.

    Passar o vetor pronto para o faster-whisper evita a decodificacao interna via PyAV,
    cuja interface muda entre versoes.
    """
    import wave

    import numpy as np

    with wave.open(str(caminho), "rb") as arquivo:
        if arquivo.getnchannels() != 1 or arquivo.getsampwidth() != 2 or arquivo.getframerate() != 16000:
            raise ValueError("o audio precisa ser WAV mono, 16 bits e 16 kHz")
        quadros = arquivo.readframes(arquivo.getnframes())

    return np.frombuffer(quadros, dtype=np.int16).astype("float32") / 32768.0


# ----------------------------------------------------------------------------- transcricao


def montar_prompt(idioma: str, termos: str) -> str:
    """Monta a dica de vocabulario no mesmo idioma da fala.

    Um prompt em idioma diferente do audio atrapalha a decodificacao, por isso o
    texto acompanha o idioma reconhecido.
    """
    if idioma.startswith("pt"):
        return f"Termos e nomes proprios que aparecem neste audio: {termos}."
    if idioma.startswith("es"):
        return f"Terminos y nombres propios que aparecen en este audio: {termos}."
    return f"Names and technical terms spoken in this audio: {termos}."


def transcrever(audio: Path, modelo: str, idioma: str, termos: str | None) -> list[Palavra]:
    from faster_whisper import WhisperModel

    whisper = WhisperModel(modelo, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)
    som = ler_wav(audio)

    if idioma == "auto":
        idioma, confianca, _ = whisper.detect_language(audio=som)
        print(f"idioma reconhecido: {idioma} (confianca {confianca:.2f})", file=sys.stderr)
    else:
        print(f"idioma informado: {idioma}", file=sys.stderr)

    segmentos, _ = whisper.transcribe(
        som,
        language=idioma,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
        condition_on_previous_text=False,
        initial_prompt=montar_prompt(idioma, termos) if termos else None,
    )

    palavras: list[Palavra] = []
    for segmento in segmentos:
        for palavra in segmento.words or ():
            texto = palavra.word.strip()
            if texto:
                palavras.append(Palavra(texto=texto, inicio=palavra.start, fim=palavra.end))
        print(f"  [{segmento.start:7.2f} - {segmento.end:7.2f}] {segmento.text.strip()}", file=sys.stderr)

    return palavras


def remover_repeticoes_de_borda(palavras: list[Palavra]) -> list[Palavra]:
    """Descarta palavras repetidas na emenda entre dois segmentos.

    O decodificador as vezes repete as ultimas palavras de um segmento no inicio
    do seguinte. A copia chega com duracao praticamente zero, o que a distingue de
    uma repeticao real da fala.
    """
    limpas: list[Palavra] = []
    indice = 0

    while indice < len(palavras):
        repetiu = False
        for tamanho in range(1, 6):
            fim_primeira = indice + tamanho
            fim_segunda = indice + 2 * tamanho
            if fim_segunda > len(palavras):
                break

            primeira = palavras[indice:fim_primeira]
            segunda = palavras[fim_primeira:fim_segunda]
            if [p.texto for p in primeira] != [p.texto for p in segunda]:
                continue

            duracao_da_copia = sum(p.fim - p.inicio for p in segunda)
            if duracao_da_copia <= 0.05:
                limpas.extend(primeira)
                indice = fim_segunda
                repetiu = True
                break

        if not repetiu:
            limpas.append(palavras[indice])
            indice += 1

    descartadas = len(palavras) - len(limpas)
    if descartadas:
        print(f"{descartadas} palavra(s) repetida(s) na emenda de segmentos foram descartadas", file=sys.stderr)

    return limpas


def salvar_palavras(palavras: list[Palavra], destino: Path) -> None:
    dados = [{"texto": p.texto, "inicio": round(p.inicio, 3), "fim": round(p.fim, 3)} for p in palavras]
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def carregar_palavras(origem: Path) -> list[Palavra]:
    dados = json.loads(origem.read_text(encoding="utf-8"))
    return [Palavra(texto=item["texto"], inicio=float(item["inicio"]), fim=float(item["fim"])) for item in dados]


# ----------------------------------------------------------------------------- quebra de linha


def quebrar_em_duas_linhas(texto: str) -> list[str] | None:
    """Divide o texto em duas linhas de ate 42 caracteres, ou devolve None se nao couber.

    Entre as divisoes possiveis, prefere cortar depois de ponto final, depois de
    virgula e, por ultimo, a que deixa as duas linhas mais parecidas em tamanho.
    """
    palavras = texto.split()
    if len(palavras) < 2:
        return None

    melhor_corte = None
    melhor_pontuacao = None
    for corte in range(1, len(palavras)):
        linha_um = " ".join(palavras[:corte])
        linha_dois = " ".join(palavras[corte:])
        if len(linha_um) > MAX_CARACTERES_LINHA or len(linha_dois) > MAX_CARACTERES_LINHA:
            continue

        pontuacao = abs(len(linha_um) - len(linha_dois))
        if linha_um.endswith(FIM_DE_FRASE):
            pontuacao -= 30
        elif linha_um.endswith(PAUSA_INTERNA):
            pontuacao -= 15

        if melhor_pontuacao is None or pontuacao < melhor_pontuacao:
            melhor_pontuacao = pontuacao
            melhor_corte = corte

    if melhor_corte is None:
        return None

    return [" ".join(palavras[:melhor_corte]), " ".join(palavras[melhor_corte:])]


def cabe_na_legenda(texto: str) -> bool:
    if len(texto) <= MAX_CARACTERES_LINHA:
        return True
    if len(texto) > MAX_CARACTERES_LEGENDA:
        return False
    return quebrar_em_duas_linhas(texto) is not None


def dividir_em_linhas(texto: str) -> list[str]:
    if len(texto) <= MAX_CARACTERES_LINHA:
        return [texto]

    linhas = quebrar_em_duas_linhas(texto)
    if linhas is not None:
        return linhas

    palavras = texto.split()
    meio = len(palavras) // 2 or 1
    return [" ".join(palavras[:meio]), " ".join(palavras[meio:])]


# ----------------------------------------------------------------------------- legendas


def agrupar_em_frases(palavras: list[Palavra]) -> list[list[Palavra]]:
    frases: list[list[Palavra]] = []
    atual: list[Palavra] = []

    for palavra in palavras:
        atual.append(palavra)
        if palavra.texto.endswith(FIM_DE_FRASE):
            frases.append(atual)
            atual = []

    if atual:
        frases.append(atual)

    return frases


def recuar_para_pontuacao(palavras: list[Palavra]) -> int:
    """Devolve quantas palavras finais devem ir para a proxima legenda.

    Quando uma legenda fica cheia no meio de uma frase, cortar logo depois de uma
    virgula le melhor do que cortar na palavra onde o espaco acabou.
    """
    for indice in range(len(palavras) - 2, max(len(palavras) // 2 - 1, 0), -1):
        if palavras[indice].texto.endswith(PAUSA_INTERNA):
            return len(palavras) - indice - 1
    return 0


def adiar_palavras_de_ligacao(palavras: list[Palavra]) -> int:
    """Conta as palavras de ligacao no fim da legenda que devem passar para a seguinte."""
    adiadas = 0
    while len(palavras) - adiadas > 1:
        candidata = palavras[len(palavras) - adiadas - 1].texto
        limpa = candidata.strip(".,;:!?…\"'()").lower()
        if limpa in PALAVRAS_QUE_NAO_FECHAM_LEGENDA and not candidata.endswith(FIM_DE_FRASE + PAUSA_INTERNA):
            adiadas += 1
            continue
        break
    return adiadas


def dividir_frase(frase: list[Palavra]) -> list[Legenda]:
    legendas: list[Legenda] = []
    atual = Legenda()

    for palavra in frase:
        if atual.palavras:
            projetado = f"{atual.texto} {palavra.texto}"
            estourou = (
                not cabe_na_legenda(projetado)
                or palavra.fim - atual.inicio > MAX_DURACAO
                or palavra.inicio - atual.fim >= PAUSA_QUE_QUEBRA
            )
            if estourou:
                sobra = recuar_para_pontuacao(atual.palavras)
                if not sobra:
                    sobra = adiar_palavras_de_ligacao(atual.palavras)
                if sobra:
                    corte = len(atual.palavras) - sobra
                    adiadas = atual.palavras[corte:]
                    atual.palavras = atual.palavras[:corte]
                else:
                    adiadas = []
                legendas.append(atual)
                atual = Legenda(palavras=list(adiadas))

        atual.palavras.append(palavra)

    if atual.palavras:
        legendas.append(atual)

    return refinar_cortes(legendas)


def e_palavra_de_ligacao(texto: str) -> bool:
    return texto.strip(".,;:!?…\"'()").lower() in PALAVRAS_QUE_NAO_FECHAM_LEGENDA


def pontuar_corte(primeira: list[Palavra], segunda: list[Palavra]) -> float | None:
    """Avalia um corte entre duas legendas. Quanto menor a nota, melhor o corte.

    Devolve None quando o corte nao respeita os limites de caracteres ou de duracao.
    """
    texto_primeira = " ".join(p.texto for p in primeira)
    texto_segunda = " ".join(p.texto for p in segunda)

    if not cabe_na_legenda(texto_primeira) or not cabe_na_legenda(texto_segunda):
        return None
    if primeira[-1].fim - primeira[0].inicio > MAX_DURACAO:
        return None
    if segunda[-1].fim - segunda[0].inicio > MAX_DURACAO:
        return None

    nota = abs(len(texto_primeira) - len(texto_segunda)) * 0.3

    fecha = primeira[-1].texto
    abre = segunda[0].texto

    if fecha.endswith(FIM_DE_FRASE):
        nota -= 100
    elif fecha.endswith(PAUSA_INTERNA):
        nota -= 60

    if e_palavra_de_ligacao(abre):
        nota -= 25
    if e_palavra_de_ligacao(fecha):
        nota += 40
    if min(len(texto_primeira), len(texto_segunda)) <= TAMANHO_DE_LEGENDA_CURTA:
        nota += 20

    return nota


def refinar_cortes(legendas: list[Legenda]) -> list[Legenda]:
    """Reposiciona o corte entre legendas vizinhas da mesma frase.

    O preenchimento sequencial costuma parar onde o espaco acabou, o que separa
    palavras que se leem juntas. Aqui cada par vizinho e testado em todas as
    posicoes possiveis e fica com a de melhor nota.
    """
    for _ in range(2):
        mudou = False
        for indice in range(len(legendas) - 1):
            juntas = legendas[indice].palavras + legendas[indice + 1].palavras
            atual = len(legendas[indice].palavras)

            melhor_corte = None
            melhor_nota = None
            for corte in range(1, len(juntas)):
                nota = pontuar_corte(juntas[:corte], juntas[corte:])
                if nota is None:
                    continue
                if melhor_nota is None or nota < melhor_nota:
                    melhor_nota = nota
                    melhor_corte = corte

            if melhor_corte is not None and melhor_corte != atual:
                legendas[indice].palavras = juntas[:melhor_corte]
                legendas[indice + 1].palavras = juntas[melhor_corte:]
                mudou = True

        if not mudou:
            break

    return legendas


def juntar_legendas_curtas(legendas: list[Legenda]) -> list[Legenda]:
    """Agrupa frases curtas vizinhas para nao deixar legendas de uma palavra na tela."""
    final: list[Legenda] = []

    for legenda in legendas:
        if final:
            anterior = final[-1]
            projetado = f"{anterior.texto} {legenda.texto}"
            alguma_e_curta = min(len(anterior.texto), len(legenda.texto)) <= TAMANHO_DE_LEGENDA_CURTA
            cabe = cabe_na_legenda(projetado)
            no_tempo = legenda.fim - anterior.inicio <= MAX_DURACAO
            sem_pausa = legenda.inicio - anterior.fim < PAUSA_QUE_QUEBRA

            if alguma_e_curta and cabe and no_tempo and sem_pausa:
                anterior.palavras.extend(legenda.palavras)
                continue

        final.append(legenda)

    return final


def montar_legendas(palavras: list[Palavra]) -> list[Legenda]:
    legendas: list[Legenda] = []
    for frase in agrupar_em_frases(palavras):
        legendas.extend(dividir_frase(frase))
    return refinar_cortes(juntar_legendas_curtas(legendas))


def ajustar_tempos(legendas: list[Legenda], duracao_total: float) -> list[tuple[float, float, str]]:
    ajustadas: list[tuple[float, float, str]] = []

    for indice, legenda in enumerate(legendas):
        inicio = max(0.0, legenda.inicio)
        fim = max(legenda.fim, inicio + MIN_DURACAO)

        proximo_inicio = legendas[indice + 1].inicio if indice + 1 < len(legendas) else None
        if proximo_inicio is not None and fim > proximo_inicio - 0.04:
            fim = max(inicio + 0.3, proximo_inicio - 0.04)

        if duracao_total and fim > duracao_total:
            fim = max(inicio + 0.3, duracao_total)

        ajustadas.append((inicio, fim, legenda.texto))

    return ajustadas


# ----------------------------------------------------------------------------- saida


def formatar_tempo(segundos: float) -> str:
    total_ms = max(0, int(round(segundos * 1000)))
    horas, resto = divmod(total_ms, 3_600_000)
    minutos, resto = divmod(resto, 60_000)
    segundos_inteiros, milissegundos = divmod(resto, 1000)
    return f"{horas:02d}:{minutos:02d}:{segundos_inteiros:02d},{milissegundos:03d}"


def escrever_srt(blocos: list[tuple[float, float, str]], destino: Path) -> None:
    linhas: list[str] = []
    for numero, (inicio, fim, texto) in enumerate(blocos, start=1):
        linhas.append(str(numero))
        linhas.append(f"{formatar_tempo(inicio)} --> {formatar_tempo(fim)}")
        linhas.extend(dividir_em_linhas(texto))
        linhas.append("")

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(linhas), encoding="utf-8")


def escrever_transcricao(blocos: list[tuple[float, float, str]], destino: Path) -> None:
    texto = " ".join(bloco[2] for bloco in blocos)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------- principal


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera legenda SRT de um video ou audio.")
    parser.add_argument("entrada", type=Path, help="arquivo de video ou audio")
    parser.add_argument("--saida", type=Path, default=None, help="caminho do arquivo .srt")
    parser.add_argument("--modelo", default="large-v3", help="modelo do Whisper (large-v3, medium, small)")
    parser.add_argument("--idioma", default="auto", help="codigo do idioma falado, ou auto para reconhecer")
    parser.add_argument("--termos", default=None, help="nomes proprios e termos tecnicos, separados por virgula")
    parser.add_argument("--salvar-palavras", type=Path, default=None, help="grava as palavras com tempo em JSON")
    parser.add_argument("--palavras", type=Path, default=None, help="monta a legenda a partir de um JSON revisado")
    argumentos = parser.parse_args()

    if not argumentos.entrada.exists():
        print(f"arquivo nao encontrado: {argumentos.entrada}", file=sys.stderr)
        return 1

    for binario in ("ffmpeg", "ffprobe"):
        if shutil.which(binario) is None:
            print(f"{binario} nao esta instalado neste ambiente", file=sys.stderr)
            return 1

    saida = argumentos.saida or argumentos.entrada.with_suffix(".srt")
    duracao_total = duracao_do_arquivo(argumentos.entrada)

    if argumentos.palavras:
        print(f"usando as palavras revisadas de {argumentos.palavras}", file=sys.stderr)
        palavras = carregar_palavras(argumentos.palavras)
    else:
        with tempfile.TemporaryDirectory() as pasta:
            audio = Path(pasta) / "audio.wav"
            print(f"extraindo audio de {argumentos.entrada.name}", file=sys.stderr)
            extrair_audio(argumentos.entrada, audio)

            print(f"transcrevendo com o modelo {argumentos.modelo}", file=sys.stderr)
            palavras = remover_repeticoes_de_borda(
                transcrever(audio, argumentos.modelo, argumentos.idioma, argumentos.termos)
            )

    if not palavras:
        print("nenhuma fala foi reconhecida no audio", file=sys.stderr)
        return 1

    if argumentos.salvar_palavras:
        salvar_palavras(palavras, argumentos.salvar_palavras)
        print(f"palavras com tempo gravadas em {argumentos.salvar_palavras}", file=sys.stderr)

    blocos = ajustar_tempos(montar_legendas(palavras), duracao_total)

    escrever_srt(blocos, saida)
    escrever_transcricao(blocos, saida.with_suffix(".txt"))

    print(f"\n{len(blocos)} legendas gravadas em {saida}", file=sys.stderr)
    print(f"transcricao corrida gravada em {saida.with_suffix('.txt')}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
