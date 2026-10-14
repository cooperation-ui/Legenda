#!/usr/bin/env python3
"""Confere se um arquivo SRT respeita os limites de leitura e de formato.

Uso:
    python3 scripts/validar_srt.py legendas/meu-video.srt
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

MAX_CARACTERES_LINHA = 42
MAX_LINHAS = 2
PALAVRAS_POR_LINHA = 4  # alvo: acima disso sai aviso
TOLERANCIA_DE_PALAVRAS = 6  # acima disso e erro de formato
MAX_DURACAO = 6.0
MIN_DURACAO = 0.7
MAX_CARACTERES_POR_SEGUNDO = 22.0  # acima disso, so um aviso: depende do ritmo da fala

PADRAO_TEMPO = re.compile(
    r"^(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})$"
)


def para_segundos(horas: str, minutos: str, segundos: str, milissegundos: str) -> float:
    return int(horas) * 3600 + int(minutos) * 60 + int(segundos) + int(milissegundos) / 1000


def ler_blocos(caminho: Path) -> list[tuple[int, float, float, list[str]]]:
    blocos = []
    for bruto in caminho.read_text(encoding="utf-8").strip().split("\n\n"):
        linhas = [linha for linha in bruto.split("\n") if linha.strip()]
        if len(linhas) < 3:
            raise ValueError(f"bloco incompleto: {bruto!r}")

        encontro = PADRAO_TEMPO.match(linhas[1])
        if encontro is None:
            raise ValueError(f"marcacao de tempo invalida: {linhas[1]!r}")

        partes = encontro.groups()
        blocos.append(
            (
                int(linhas[0]),
                para_segundos(*partes[:4]),
                para_segundos(*partes[4:]),
                linhas[2:],
            )
        )
    return blocos


def main() -> int:
    if len(sys.argv) != 2:
        print("informe o caminho do arquivo .srt", file=sys.stderr)
        return 2

    caminho = Path(sys.argv[1])
    blocos = ler_blocos(caminho)
    problemas: list[str] = []
    avisos: list[str] = []
    avisos_de_palavras: list[str] = []

    for posicao, (numero, inicio, fim, linhas) in enumerate(blocos):
        if numero != posicao + 1:
            problemas.append(f"legenda {numero}: numeracao fora de ordem")
        if fim <= inicio:
            problemas.append(f"legenda {numero}: fim nao e posterior ao inicio")

        duracao = fim - inicio
        if duracao > MAX_DURACAO:
            problemas.append(f"legenda {numero}: {duracao:.2f}s na tela, acima de {MAX_DURACAO}s")
        if duracao < MIN_DURACAO:
            problemas.append(f"legenda {numero}: {duracao:.2f}s na tela, abaixo de {MIN_DURACAO}s")

        if len(linhas) > MAX_LINHAS:
            problemas.append(f"legenda {numero}: {len(linhas)} linhas, acima de {MAX_LINHAS}")

        for linha in linhas:
            if len(linha) > MAX_CARACTERES_LINHA:
                problemas.append(f"legenda {numero}: linha de {len(linha)} caracteres, acima de {MAX_CARACTERES_LINHA}")

            quantidade = len(linha.split())
            if quantidade > TOLERANCIA_DE_PALAVRAS:
                problemas.append(f"legenda {numero}: linha de {quantidade} palavras, acima de {TOLERANCIA_DE_PALAVRAS}")
            elif quantidade > PALAVRAS_POR_LINHA:
                avisos_de_palavras.append(f"legenda {numero}: linha de {quantidade} palavras: {linha!r}")

        caracteres = sum(len(linha) for linha in linhas)
        velocidade = caracteres / duracao if duracao else 0
        if velocidade > MAX_CARACTERES_POR_SEGUNDO:
            avisos.append(f"legenda {numero}: {velocidade:.1f} caracteres por segundo, acima de {MAX_CARACTERES_POR_SEGUNDO}")

        if posicao + 1 < len(blocos) and fim > blocos[posicao + 1][1]:
            problemas.append(f"legenda {numero}: sobrepoe a legenda {numero + 1}")

    print(f"{len(blocos)} legendas conferidas em {caminho}")

    if avisos_de_palavras:
        print(f"\n{len(avisos_de_palavras)} linha(s) acima de {PALAVRAS_POR_LINHA} palavras:")
        for aviso in avisos_de_palavras:
            print(f"  {aviso}")
        print("\nSao os casos em que cortar na quarta palavra separaria o que se le junto.")

    if avisos:
        print(f"\n{len(avisos)} aviso(s) de velocidade de leitura:")
        for aviso in avisos:
            print(f"  {aviso}")
        print("\nVelocidade alta vem da fala rapida no audio. Baixar esse numero")
        print("exigiria cortar palavras, o que este projeto nao faz.")

    if problemas:
        print(f"\n{len(problemas)} problema(s) de formato:")
        for problema in problemas:
            print(f"  {problema}")
        return 1

    print("\nnenhum problema de formato encontrado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
