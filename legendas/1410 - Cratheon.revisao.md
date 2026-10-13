# Revisao da legenda de "1410 - Cratheon.MP3"

Audio de 58,2 segundos, narracao em ingles, reconhecida automaticamente.
Duas legendas, conforme a regra da Cratheon:

- `legendas/1410 - Cratheon.srt`, em ingles, 21 blocos
- `legendas/1410 - Cratheon.pt-BR.srt`, em portugues, mesmos tempos

O roteiro usado na gravacao esta em `roteiros/1410 - Cratheon.en.txt`.

## Alinhamento com o roteiro

A transcricao foi alinhada palavra por palavra contra o roteiro: 165 palavras
ouvidas contra 161 escritas, semelhanca de 0,920. Nove diferencas apareceram, e
cada uma foi tratada de um jeito diferente.

### Corrigido pelo roteiro

| Reconhecido | Gravado | Em que me baseei |
|---|---|---|
| "Medicine has a character." | "Medicine? Ask Cratheon." | O roteiro traz "Ask Cratheon". A redecodificacao com dica de vocabulario devolveu "Ask Cratheon", e o arquivo anterior da Cratheon falhou do mesmo jeito no nome da marca, que saiu como "Escration". Confira em 56,2 s. |

### Eco de segmento descartado

Em 25,8 s o reconhecimento escreveu "the textbook, book, the split-second". A
redecodificacao da janela isolada traz "the textbook" uma vez so. O "book," era
repeticao na emenda entre dois segmentos e foi descartado.

### Mantido como esta no audio, embora o roteiro diga outra coisa

Nestes dois casos o roteiro nao vale, porque a legenda precisa bater com o que
se ouve no video, e nao com o que estava escrito para ser lido:

| No audio | No roteiro | Em que me baseei |
|---|---|---|
| "autonomous. Good, that number is real." | sem o "Good" | Duas decodificacoes da janela de 4,0 a 5,6 s devolveram "Good", a segunda com confianca 0,91. A palavra esta no audio. Confira em 4,6 s. |
| "are predictable ones" | "are the predictable ones" | A janela isolada de 19,2 a 21,4 s devolveu "are predictable ones" com confianca 0,99, sem o artigo, nas duas tentativas. Confira em 20,0 s. |

### Diferenca so de escrita

O roteiro escreve os numeros em palavras, "eighty-something", "ninety percent" e
"ten percent". A legenda usa "80-something percent", "90%" e "10%", que e a
forma curta usada em legendagem e ocupa menos espaco na tela. Sao as mesmas
palavras faladas, escritas de outro jeito.

## Ajuste na traducao

O bloco 1 saiu com 24,3 caracteres por segundo e foi encurtado, de "Voce vai ver
manchetes dizendo que os robos cirurgicos" para "Voce vera manchetes dizendo que
robos cirurgicos". Depois disso, nenhum bloco da versao em portugues passa de 22
caracteres por segundo. A versao em ingles tem um bloco em 22,5, onde nao da para
encurtar.

## Como refazer

```bash
python3 scripts/transcrever.py --palavras "revisao/1410 - Cratheon.json" \
  --saida "legendas/1410 - Cratheon.srt"

python3 scripts/aplicar_traducao.py \
  "legendas/1410 - Cratheon.srt" \
  "traducao/1410 - Cratheon.pt-BR.txt" \
  "legendas/1410 - Cratheon.pt-BR.srt"
```
