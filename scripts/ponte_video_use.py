#!/usr/bin/env python3
"""Liga o video-use ao Whisper local deste projeto, sem ElevenLabs.

Dois comandos:

  transcricao  converte revisao/<nome>.json (palavras com tempo do transcrever.py)
               no formato Scribe que o video-use le, em <edit>/transcripts/<id>.json.
               Os silencios viram entradas "spacing", que e de onde o video-use
               tira os cortes de respiro.

  legenda      monta o master.srt na linha do tempo ja cortada, a partir do
               edl.json, com a quebra de linha deste projeto (quatro palavras por
               linha, duas linhas por bloco), e nao com a de duas palavras do
               video-use. Nenhuma palavra e alterada: o texto vem do JSON.

Uso:
  python3 scripts/ponte_video_use.py transcricao "revisao/<nome>.json" \
      --edit-dir "videos/edit" --id "<id>"
  python3 scripts/ponte_video_use.py legenda "videos/edit/edl.json" \
      --saida "videos/edit/master.srt"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from transcrever import (  # noqa: E402
    Palavra,
    ajustar_tempos,
    carregar_palavras,
    escrever_srt,
    montar_legendas,
)



def para_scribe(palavras: list[Palavra], idioma: str | None) -> dict:
    entradas: list[dict] = []
    anterior_fim: float | None = None
    for p in palavras:
        if anterior_fim is not None and p.inicio > anterior_fim:
            entradas.append({"type": "spacing", "text": " ", "start": anterior_fim, "end": p.inicio, "speaker_id": "speaker_0"})
        entradas.append({"type": "word", "text": p.texto, "start": p.inicio, "end": p.fim, "speaker_id": "speaker_0"})
        anterior_fim = p.fim
    return {
        "language_code": idioma,
        "text": " ".join(p.texto for p in palavras),
        "words": entradas,
        "origem": "whisper local (scripts/transcrever.py)",
    }


def comando_transcricao(args: argparse.Namespace) -> int:
    palavras = carregar_palavras(args.json)
    destino = args.edit_dir / "transcripts" / f"{args.id}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(para_scribe(palavras, args.idioma), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(palavras)} palavras -> {destino}", file=sys.stderr)
    return 0


def palavras_na_saida(edl: dict, edit_dir: Path) -> tuple[list[Palavra], float]:
    """Leva cada palavra mantida pelo corte para o tempo do video final."""
    saida: list[Palavra] = []
    deslocamento = 0.0
    for trecho in edl["ranges"]:
        inicio, fim = float(trecho["start"]), float(trecho["end"])
        dados = json.loads((edit_dir / "transcripts" / f"{trecho['source']}.json").read_text(encoding="utf-8"))
        for w in dados["words"]:
            if w.get("type") != "word" or w["end"] <= inicio or w["start"] >= fim:
                continue
            saida.append(
                Palavra(
                    texto=w["text"],
                    inicio=max(w["start"], inicio) - inicio + deslocamento,
                    fim=min(w["end"], fim) - inicio + deslocamento,
                )
            )
        deslocamento += fim - inicio
    return saida, deslocamento


def comando_legenda(args: argparse.Namespace) -> int:
    edl_path = args.edl.resolve()
    edl = json.loads(edl_path.read_text(encoding="utf-8"))
    palavras, duracao = palavras_na_saida(edl, edl_path.parent)
    blocos = ajustar_tempos(montar_legendas(palavras), duracao)
    escrever_srt(blocos, args.saida)
    print(f"{len(blocos)} blocos, {duracao:.2f}s -> {args.saida}", file=sys.stderr)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="comando", required=True)

    t = sub.add_parser("transcricao", help="revisao JSON -> transcript Scribe do video-use")
    t.add_argument("json", type=Path)
    t.add_argument("--edit-dir", type=Path, required=True)
    t.add_argument("--id", required=True, help="nome da fonte no edl.json")
    t.add_argument("--idioma", default=None)
    t.set_defaults(func=comando_transcricao)

    l = sub.add_parser("legenda", help="edl.json -> master.srt no tempo do corte")
    l.add_argument("edl", type=Path)
    l.add_argument("--saida", type=Path, required=True)
    l.set_defaults(func=comando_legenda)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
