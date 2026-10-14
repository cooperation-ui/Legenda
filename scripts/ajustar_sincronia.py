#!/usr/bin/env python3
"""Encosta os tempos de um SRT no inicio e no fim reais da fala.

O reconhecimento erra a marcacao de tempo por uma fracao de segundo, e as vezes
estende uma legenda para dentro de um silencio. Este script mede os silencios do
audio com o ffmpeg e, quando o inicio ou o fim de uma legenda cai dentro de um
silencio, puxa esse tempo para a borda da fala.

Uso:
    python3 scripts/ajustar_sincronia.py audio.mp3 legenda.srt
    python3 scripts/ajustar_sincronia.py audio.mp3 legenda.srt --conferir
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

RUIDO = "-35dB"
SILENCIO_MINIMO = 0.2
MARGEM = 0.04
MIN_DURACAO = 0.7
# Nao mexe no tempo quando a diferenca passa disso: ali o problema nao e marcacao,
# e o reconhecimento, e mover o tempo esconderia isso.
AJUSTE_MAXIMO = 1.5

PADRAO_TEMPO = re.compile(
    r"^(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})$"
)


def medir_silencios(audio: Path, ruido: str = RUIDO) -> list[tuple[float, float]]:
    comando = [
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(audio),
        "-af", f"silencedetect=noise={ruido}:d={SILENCIO_MINIMO}",
        "-f", "null", "-",
    ]
    saida = subprocess.run(comando, capture_output=True, text=True).stderr

    silencios: list[tuple[float, float]] = []
    inicio = None
    for linha in saida.splitlines():
        comeco = re.search(r"silence_start: (-?[\d.]+)", linha)
        if comeco:
            inicio = float(comeco.group(1))
        fim = re.search(r"silence_end: ([\d.]+)", linha)
        if fim and inicio is not None:
            silencios.append((max(0.0, inicio), float(fim.group(1))))
            inicio = None

    if inicio is not None:
        silencios.append((max(0.0, inicio), float("inf")))

    return silencios


def silencio_em(momento: float, silencios: list[tuple[float, float]]) -> tuple[float, float] | None:
    for comeco, fim in silencios:
        if comeco <= momento <= fim:
            return comeco, fim
        if comeco > momento:
            break
    return None


def para_segundos(horas: str, minutos: str, segundos: str, milissegundos: str) -> float:
    return int(horas) * 3600 + int(minutos) * 60 + int(segundos) + int(milissegundos) / 1000


def formatar_tempo(segundos: float) -> str:
    total_ms = max(0, int(round(segundos * 1000)))
    horas, resto = divmod(total_ms, 3_600_000)
    minutos, resto = divmod(resto, 60_000)
    segundos_inteiros, milissegundos = divmod(resto, 1000)
    return f"{horas:02d}:{minutos:02d}:{segundos_inteiros:02d},{milissegundos:03d}"


def ler_srt(caminho: Path) -> list[tuple[float, float, list[str]]]:
    blocos = []
    for bruto in caminho.read_text(encoding="utf-8").strip().split("\n\n"):
        linhas = [linha for linha in bruto.split("\n") if linha.strip()]
        encontro = PADRAO_TEMPO.match(linhas[1])
        if encontro is None:
            raise ValueError(f"marcacao de tempo invalida: {linhas[1]!r}")
        partes = encontro.groups()
        blocos.append((para_segundos(*partes[:4]), para_segundos(*partes[4:]), linhas[2:]))
    return blocos


def escrever_srt(blocos: list[tuple[float, float, list[str]]], caminho: Path) -> None:
    linhas: list[str] = []
    for numero, (inicio, fim, texto) in enumerate(blocos, start=1):
        linhas.append(str(numero))
        linhas.append(f"{formatar_tempo(inicio)} --> {formatar_tempo(fim)}")
        linhas.extend(texto)
        linhas.append("")
    caminho.write_text("\n".join(linhas), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Encosta os tempos do SRT na fala do audio.")
    parser.add_argument("audio", type=Path)
    parser.add_argument("srt", type=Path)
    parser.add_argument("--conferir", action="store_true", help="so mostra o que mudaria")
    parser.add_argument(
        "--ruido",
        default=RUIDO,
        help="limite de volume que conta como silencio. Grave com ruido de fundo pede valor maior, como -25dB",
    )
    argumentos = parser.parse_args()

    for caminho in (argumentos.audio, argumentos.srt):
        if not caminho.exists():
            print(f"arquivo nao encontrado: {caminho}", file=sys.stderr)
            return 1

    silencios = medir_silencios(argumentos.audio, argumentos.ruido)
    print(f"{len(silencios)} trechos de silencio medidos em {argumentos.audio.name}", file=sys.stderr)

    blocos = ler_srt(argumentos.srt)
    ajustados: list[tuple[float, float, list[str]]] = []
    mudancas = 0
    fora_de_alcance: list[str] = []

    for posicao, (inicio, fim, texto) in enumerate(blocos):
        novo_inicio, novo_fim = inicio, fim

        dentro = silencio_em(inicio, silencios)
        if dentro and dentro[1] != float("inf"):
            if 0 < dentro[1] - inicio <= AJUSTE_MAXIMO:
                novo_inicio = dentro[1]
            elif dentro[1] - inicio > AJUSTE_MAXIMO:
                fora_de_alcance.append(
                    f"legenda {posicao + 1}: comeca em {formatar_tempo(inicio)}, "
                    f"dentro de um silencio que vai ate {formatar_tempo(dentro[1])}"
                )

        dentro = silencio_em(fim, silencios)
        if dentro:
            if 0 < fim - dentro[0] <= AJUSTE_MAXIMO:
                novo_fim = dentro[0]
            elif fim - dentro[0] > AJUSTE_MAXIMO:
                fora_de_alcance.append(
                    f"legenda {posicao + 1}: termina em {formatar_tempo(fim)}, "
                    f"dentro de um silencio que comeca em {formatar_tempo(dentro[0])}"
                )

        if novo_fim - novo_inicio < MIN_DURACAO:
            novo_fim = novo_inicio + MIN_DURACAO

        if ajustados and novo_inicio < ajustados[-1][1] + MARGEM:
            novo_inicio = min(inicio, ajustados[-1][1] + MARGEM)
        if posicao + 1 < len(blocos) and novo_fim > blocos[posicao + 1][0] - MARGEM:
            novo_fim = max(novo_inicio + 0.3, blocos[posicao + 1][0] - MARGEM)

        if abs(novo_inicio - inicio) > 0.005 or abs(novo_fim - fim) > 0.005:
            mudancas += 1
            print(
                f"  legenda {posicao + 1}: "
                f"{formatar_tempo(inicio)} -> {formatar_tempo(novo_inicio)} | "
                f"{formatar_tempo(fim)} -> {formatar_tempo(novo_fim)}",
                file=sys.stderr,
            )

        ajustados.append((novo_inicio, novo_fim, texto))

    print(f"\n{mudancas} de {len(blocos)} legendas com tempo ajustado", file=sys.stderr)

    if fora_de_alcance:
        print(
            f"\n{len(fora_de_alcance)} tempo(s) dentro de silencio longo, que o script nao move "
            f"porque o ajuste passaria de {AJUSTE_MAXIMO}s:",
            file=sys.stderr,
        )
        for aviso in fora_de_alcance:
            print(f"  {aviso}", file=sys.stderr)
        print(
            "\nLegenda em cima de silencio longo quer dizer palavra inventada pelo "
            "reconhecimento. Confira o texto desses blocos antes de entregar.",
            file=sys.stderr,
        )

    if argumentos.conferir:
        print("nada foi gravado, modo de conferencia", file=sys.stderr)
        return 0

    escrever_srt(ajustados, argumentos.srt)
    print(f"gravado em {argumentos.srt}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
