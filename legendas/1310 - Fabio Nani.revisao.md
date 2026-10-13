# Revisao da legenda de "1310 - Fabio Nani.MP3"

Audio de 127,7 segundos, consulta medica em portugues, reconhecida com confianca
1,00. Legenda com 47 blocos, sem problema de formato.

## Decisoes de palavra

Tres trechos vinham sem sentido. Cada um foi redecodificado em janela isolada,
com busca mais ampla, uma vez sem dica de vocabulario e uma vez com uma dica de
termos da area.

| Reconhecido | Gravado | Em que me baseei |
|---|---|---|
| "quase eu nao to meio diuretico" | "quase eu nao tomei diuretico" | A redecodificacao com dica devolveu "tomei", com confianca 0,70. "to meio" e "tomei" soam quase igual, e "nao to meio diuretico" nao se encaixa na frase. Confira em 3,1 s. |
| "uma caracteristica... De tensao de liquido" | "uma caracteristica... de retencao de liquido" | A redecodificacao com dica devolveu "retencao". O proprio audio usa "retencao hidrica" em 77,8 s. Confira em 7,1 s. |
| "e so a bipeda" | "e so a bioimpedancia" | A redecodificacao com dica devolveu "bioimpedancia". Toda a conversa trata de leitura de massa muscular e gordura, que e o que esse exame mede. "bipeda" nao tem sentido ali. Confira em 127,2 s. |

O "De" maiusculo depois das reticencias virou minusculo, porque continua a
mesma frase. Ajuste de caixa, nao de palavra.

## Um numero que nao fecha

Em 83,2 s: "30 para 48 sao 10 litros de agua". A conta daria 18, nao 10. Testei a
janela quatro vezes, com e sem dica, e todas devolveram "30", nunca "38". Entao
ficou "30", como foi falado. Vale conferir contra o numero que aparece na tela,
porque pode ter sido ele que errou, nao o reconhecimento.

## Velocidade de leitura

Dez blocos passam de 22 caracteres por segundo, ate 28,8. E uma conversa rapida,
com duas pessoas se alternando. Baixar esse numero exigiria cortar palavras.

## Como refazer

```bash
python3 scripts/transcrever.py --palavras "revisao/1310 - Fabio Nani.json" \
  --saida "legendas/1310 - Fabio Nani.srt"
```
