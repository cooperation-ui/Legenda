#!/usr/bin/env python3
"""
Gera legenda SRT a partir de um video ou audio, sem alterar nenhuma palavra do que foi dito.

O script extrai o audio com ffmpeg, transcreve com faster-whisper (large-v3 por padrao)
e monta as legendas respeitando limites de leitura: no maximo 2 linhas, 42 caracteres
por linha e 6 segundos por legenda.

Uso:
    python3 scripts/transcrever.py videos/meu-video.mp4
    python3 scripts/transcrever.py videos/meu-video.mp4 --termos "Legenda, Claude, HeyGen"
    python3 scripts/transcrever.py audio.m4a --modelo medium --saida legendas/audio.srt
"""

from __future__ import annotations

import argparse
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
MIN_CARACTERES_PARA_QUEBRAR_EM_PONTO = 18

FIM_DE_FRASE = (".", "!", "?", "…")
PAUSA_INTERNA = (",", ";", ":", "—")


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


def transcrever(audio: Path, modelo: str, idioma: str, termos: str | None) -> list[Palavra]:
    from faster_whisper import WhisperModel

    whisper = WhisperModel(modelo, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)

    prompt = None
    if termos:
        prompt = f"Termos e nomes proprios que aparecem neste audio: {termos}."

    segmentos, info = whisper.transcribe(
        ler_wav(audio),
        language=idioma,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
        condition_on_previous_text=False,
        initial_prompt=prompt,
    )

    print(f"idioma detectado: {info.language} (confianca {info.language_probability:.2f})", file=sys.stderr)

    palavras: list[Palavra] = []
    for segmento in segmentos:
        if not segmento.words:
            continue
        for palavra in segmento.words:
            texto = palavra.word.strip()
            if not texto:
                continue
            palavras.append(Palavra(texto=texto, inicio=palavra.start, fim=palavra.end))
        print(f"  [{segmento.start:7.2f} - {segmento.end:7.2f}] {segmento.text.strip()}", file=sys.stderr)

    return palavras


def montar_legendas(palavras: list[Palavra]) -> list[Legenda]:
    legendas: list[Legenda] = []
    atual = Legenda()

    for indice, palavra in enumerate(palavras):
        if atual.palavras:
            texto_projetado = f"{atual.texto} {palavra.texto}"
            pausa = palavra.inicio - atual.fim
            duracao_projetada = palavra.fim - atual.inicio

            excedeu_tamanho = not cabe_na_legenda(texto_projetado)
            excedeu_duracao = duracao_projetada > MAX_DURACAO
            pausa_longa = pausa >= PAUSA_QUE_QUEBRA

            if excedeu_tamanho or excedeu_duracao or pausa_longa:
                legendas.append(atual)
                atual = Legenda()

        atual.palavras.append(palavra)

        terminou_frase = palavra.texto.endswith(FIM_DE_FRASE)
        ultima = indice == len(palavras) - 1
        if terminou_frase and len(atual.texto) >= MIN_CARACTERES_PARA_QUEBRAR_EM_PONTO and not ultima:
            legendas.append(atual)
            atual = Legenda()

    if atual.palavras:
        legendas.append(atual)

    return legendas


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


def ajustar_tempos(legendas: list[Legenda], duracao_total: float) -> list[tuple[float, float, str]]:
    ajustadas: list[tuple[float, float, str]] = []

    for indice, legenda in enumerate(legendas):
        inicio = max(0.0, legenda.inicio)
        fim = legenda.fim

        if fim - inicio < MIN_DURACAO:
            fim = inicio + MIN_DURACAO

        proximo_inicio = legendas[indice + 1].inicio if indice + 1 < len(legendas) else None
        if proximo_inicio is not None and fim > proximo_inicio - 0.04:
            fim = max(inicio + 0.3, proximo_inicio - 0.04)

        if duracao_total and fim > duracao_total:
            fim = max(inicio + 0.3, duracao_total)

        ajustadas.append((inicio, fim, legenda.texto))

    return ajustadas


def formatar_tempo(segundos: float) -> str:
    if segundos < 0:
        segundos = 0.0
    total_ms = int(round(segundos * 1000))
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera legenda SRT de um video ou audio.")
    parser.add_argument("entrada", type=Path, help="arquivo de video ou audio")
    parser.add_argument("--saida", type=Path, default=None, help="caminho do arquivo .srt")
    parser.add_argument("--modelo", default="large-v3", help="modelo do Whisper (large-v3, medium, small)")
    parser.add_argument("--idioma", default="pt", help="codigo do idioma falado no audio")
    parser.add_argument("--termos", default=None, help="nomes proprios e termos tecnicos, separados por virgula")
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

    with tempfile.TemporaryDirectory() as pasta:
        audio = Path(pasta) / "audio.wav"
        print(f"extraindo audio de {argumentos.entrada.name}", file=sys.stderr)
        extrair_audio(argumentos.entrada, audio)

        print(f"transcrevendo com o modelo {argumentos.modelo}", file=sys.stderr)
        palavras = transcrever(audio, argumentos.modelo, argumentos.idioma, argumentos.termos)

    if not palavras:
        print("nenhuma fala foi reconhecida no audio", file=sys.stderr)
        return 1

    legendas = montar_legendas(palavras)
    blocos = ajustar_tempos(legendas, duracao_total)

    escrever_srt(blocos, saida)
    escrever_transcricao(blocos, saida.with_suffix(".txt"))

    print(f"\n{len(blocos)} legendas gravadas em {saida}", file=sys.stderr)
    print(f"transcricao corrida gravada em {saida.with_suffix('.txt')}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
