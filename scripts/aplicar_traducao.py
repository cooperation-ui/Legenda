#!/usr/bin/env python3
"""Monta uma legenda traduzida reaproveitando os tempos da legenda original.

A traducao entra num arquivo de texto com um bloco por paragrafo, na mesma ordem
dos blocos do SRT de origem. As quebras de linha sao recalculadas pelas mesmas
regras do gerador, entao o texto traduzido nao precisa vir pre-quebrado.

Uso:
    python3 scripts/aplicar_traducao.py original.srt traducao.txt saida.srt
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from transcrever import MAX_CARACTERES_LEGENDA, dividir_em_linhas  # noqa: E402

PADRAO_TEMPO = re.compile(r"^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$")


def ler_tempos(caminho: Path) -> list[str]:
    tempos = []
    for bruto in caminho.read_text(encoding="utf-8").strip().split("\n\n"):
        linhas = [linha for linha in bruto.split("\n") if linha.strip()]
        if len(linhas) < 3 or not PADRAO_TEMPO.match(linhas[1]):
            raise ValueError(f"bloco invalido no SRT de origem: {bruto!r}")
        tempos.append(linhas[1])
    return tempos


def ler_traducao(caminho: Path) -> list[str]:
    blocos = []
    for bruto in caminho.read_text(encoding="utf-8").strip().split("\n\n"):
        texto = " ".join(linha.strip() for linha in bruto.split("\n") if linha.strip())
        if texto:
            blocos.append(texto)
    return blocos


def main() -> int:
    if len(sys.argv) != 4:
        print("uso: aplicar_traducao.py original.srt traducao.txt saida.srt", file=sys.stderr)
        return 2

    origem, traducao, destino = (Path(argumento) for argumento in sys.argv[1:])

    tempos = ler_tempos(origem)
    textos = ler_traducao(traducao)

    if len(tempos) != len(textos):
        print(
            f"a origem tem {len(tempos)} blocos e a traducao tem {len(textos)}. "
            "Os dois precisam bater, um bloco de traducao por bloco de legenda.",
            file=sys.stderr,
        )
        return 1

    longos = [posicao + 1 for posicao, texto in enumerate(textos) if len(texto) > MAX_CARACTERES_LEGENDA]
    if longos:
        print(f"blocos acima de {MAX_CARACTERES_LEGENDA} caracteres: {longos}", file=sys.stderr)
        print("encurte a traducao desses blocos, senao a legenda passa de duas linhas.", file=sys.stderr)
        return 1

    linhas: list[str] = []
    for numero, (tempo, texto) in enumerate(zip(tempos, textos), start=1):
        linhas.append(str(numero))
        linhas.append(tempo)
        linhas.extend(dividir_em_linhas(texto))
        linhas.append("")

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(linhas), encoding="utf-8")
    print(f"{len(textos)} blocos gravados em {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
