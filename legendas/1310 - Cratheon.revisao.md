# Revisao da legenda de "1310 - Cratheon.MP3"

Audio de 43,2 segundos, narracao em ingles, reconhecida automaticamente com
confianca 1,00. Legenda final em `legendas/1310 - Cratheon.srt`, com 17 blocos.

## Ajustes de pontuacao e formato

Pontuacao, maiusculas e quebras de linha foram ajustadas sem mexer nas palavras.
Todos os blocos terminam em fim de frase ou em fronteira limpa de oracao, e
nenhuma linha passa de 42 caracteres.

## Decisoes de palavra

O reconhecimento produziu seis trechos que nao correspondiam ao que foi falado.
Cada um foi redecodificado em janela isolada, com busca mais ampla, e tres deles
tambem foram conferidos nos modelos `medium.en` e `small.en`.

| Reconhecido | Gravado na legenda | Em que me baseei |
|---|---|---|
| "the steadiest woman hand" | "the steadiest human hand" | `small.en` ouviu "human" no trecho equivalente. "woman hand" nao e construcao do ingles, "human hand" e a frase padrao nesse contexto. Confira em 0,9 s. |
| "a woman tremor" | "a human tremor" | Mesmo caso, mesma fala. Confira em 17,9 s. |
| "about a hundred micros" | "about a hundred microns" | Micron e a unidade de medida usada; "micros" nao e unidade. A redecodificacao com dica de vocabulario devolveu "microns". Confira em 4,1 s. |
| "that differences everything" | "that difference is everything" | As duas palavras saiam com confianca baixa, 0,58 e 0,57, as menores do audio inteiro. Confira em 7,9 s. |
| "in the perfect one" | "into a perfect one" | A janela isolada devolveu "into a perfect one" sem nenhuma dica de vocabulario. Confira em 26,0 s. |
| "Escration" | "Cratheon" | Nome da marca, que esta no nome do arquivo. A redecodificacao com dica devolveu "Kratheon". Confira em 42,5 s. |

Duas palavras repetidas na emenda entre segmentos, um "This is" duplicado em
28,2 s, foram descartadas: a copia vinha com duracao zero.

As quatro primeiras decisoes da tabela sao leitura minha de trechos em que o
reconhecimento ficou abaixo do confiavel. Sao os pontos para ouvir antes de
publicar. As duas ultimas estao confirmadas por redecodificacao.

## Velocidade de leitura

Cinco blocos passam de 22 caracteres por segundo, chegando a 25. Isso vem do
ritmo da narracao. Reduzir esse numero exigiria cortar palavras.

## Como refazer

A lista de palavras com tempo esta em `revisao/1310 - Cratheon.json`. Para
mudar qualquer palavra e remontar a legenda sem transcrever de novo:

```bash
python3 scripts/transcrever.py "videos/1310 - Cratheon.MP3" \
  --saida "legendas/1310 - Cratheon.srt" \
  --palavras "revisao/1310 - Cratheon.json"
```

## Versao traduzida

`legendas/1310 - Cratheon.pt-BR.srt` traz a mesma legenda em portugues, com a
marcacao de tempo identica a da original, bloco por bloco. O texto da traducao
fica em `traducao/1310 - Cratheon.pt-BR.txt` e pode ser editado e remontado com
`scripts/aplicar_traducao.py`.

Tres blocos foram encurtados na traducao para segurar a velocidade de leitura,
que sobe quando o portugues fica mais longo que o ingles:

| Bloco | Primeira versao | Versao final |
|---|---|---|
| 12 | "E por isso que a cirurgia robotica avanca" | "Por isso a cirurgia robotica avanca" |
| 13 | "para procedimentos cada vez mais delicados." | "a procedimentos cada vez mais delicados." |
| 15 | "Trata-se de fazer pelos pacientes o que antes simplesmente nao era possivel." | "Trata-se de fazer pelos pacientes o que antes nao era possivel." |

Depois do ajuste, a versao em portugues nao tem nenhum bloco acima de 22
caracteres por segundo. A versao em ingles mantem cinco, porque ali nao da para
encurtar: a regra e nao mexer nas palavras faladas.
