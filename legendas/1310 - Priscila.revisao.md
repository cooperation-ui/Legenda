# Revisao da legenda de "1310 - Priscila.MP3"

Audio de 109,2 segundos, fala em portugues, reconhecida com confianca 1,00.
Legenda com 34 blocos, sem problema de formato.

## Decisao de palavra

| Reconhecido | Gravado | Em que me baseei |
|---|---|---|
| "Voce aberta a mama" | "Voce aperta a mama" | A redecodificacao da janela de 0 a 3,2 s com dica de vocabulario devolveu "aperta". "aberta" nao se encaixa na frase. Confira em 0,5 s. |

## Dois trechos que eu deixei como sairam

Em 56,9 s, "e agora vem a parte quase ninguem te conta sobre exame". A gramatica
pede "a parte que quase ninguem te conta", mas nenhum dos tres modelos testados,
`large-v3`, `medium` e `small`, produziu esse "que". O mais provavel e que ela
tenha comido a palavra na fala rapida, entao a transcricao ficou fiel ao audio.

No mesmo trecho, `medium` ouviu "sobre o exame", com confianca 0,26 nesse "o",
contra "sobre exame" no `large-v3`. Confianca baixa demais para inserir palavra.

Os dois pontos estao em 56,9 s, se quiser conferir de ouvido.

## Velocidade de leitura

Dois blocos passam de 22 caracteres por segundo, 22,6 e 25,0, pelo ritmo da fala.

## Como refazer

```bash
python3 scripts/transcrever.py --palavras "revisao/1310 - Priscila.json" \
  --saida "legendas/1310 - Priscila.srt"
```
