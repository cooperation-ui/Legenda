# Revisao da legenda de "Aula 2 - Igor (compressed by happyscribe.com) (1).mp3"

Audio de 33 minutos e 6 segundos, fala em ingles com sotaque, reconhecida
automaticamente. Legenda em `legendas/Aula 2 - Igor.srt`, 728 blocos, quatro
palavras por linha. So em ingles, como pedido.

Documentos de referencia em `roteiros/`: o roteiro de gravacao, o mapeamento dos
13 clipes da Parte 2 e o texto em ingles de P2-11 e P2-12.

## Sincronia

As 13 pausas de pergunta foram medidas com o ffmpeg: 3:55, 10:08, 11:48, 14:33,
15:37, 19:40, 22:55, 25:00, 27:47, 29:21, 29:50, 31:16 e 32:41, todas entre 5,1
e 5,4 segundos. Nenhuma das 728 legendas toca nenhuma delas, conferido bloco por
bloco. A primeira legenda comeca em 5,12 s, exatamente onde a fala comeca.

Depois de montada, a legenda passou por `scripts/ajustar_sincronia.py`, que
encosta inicio e fim na borda da fala medida no audio. Vinte e nove blocos
tiveram o tempo corrigido.

## Duas passadas e um juiz

A primeira passada usou o filtro de voz, que e o padrao. Ela perdia a primeira
palavra quando essa palavra e dita baixo na volta da fala, o que aconteceu em
varios pontos, entre eles um "I" em 29:56 e um "The" em 10:13.

A segunda passada rodou sem o filtro e trouxe 42 palavras a mais, mas perdeu
outras que a primeira havia pegado. Isso nao e defeito do filtro: o modelo
decodifica em janelas de 30 segundos, e cada configuracao corta em um lugar
diferente.

As duas passadas divergiram em 95 pontos relevantes. Cada um foi decodificado
uma terceira vez, em janela curta, com busca mais ampla e com o vocabulario do
roteiro, e essa terceira leitura decidiu. Resultado: 38 correcoes aplicadas.

## Trechos que estavam faltando e voltaram

| Tempo | Texto |
|---|---|
| 02:09 | "repair that defect in the posterior layer." |
| 05:44 | "posterior rectus sheath," |
| 09:00 | "tension on, especially when" |
| 12:31 | "those stitches come with two. One stitch comes with two needles." |
| 22:16 | "the peritoneum is very fragile." |
| 28:40 | "with abdominal wall" |

## Termos corrigidos

| Saia | Ficou | Quantas vezes |
|---|---|---|
| retroactive space | retrorectus space | 8 |
| linea semilaris, lignis similare, the inseminaries, lenient semilitis, linear semilunaris | linea semilunaris | 6 |
| transverse abdominis, change versus some downless | transversus abdominis | 4 |
| a two -opprolene | a 2-0 Prolene | 1 |
| tension or Zolomatcha stitch | tension horizontal mattress stitch | 1 |
| falcipar ligament | falciform ligament | 1 |
| arcate line | arcuate line | 1 |
| neurofibers | nerve fibers | 1 |
| placate | plicate | 1 |
| abdominal mass release | abdominis muscle release | 1 |
| where the bell was slipping | where the bowel was slipping | 1 |
| repair side | repair site | 1 |
| posterior forces are together | posterior rectus sheath is not reloaded | 1 |

"retrorectus space" merece explicacao, porque e a unica correcao que contraria o
reconhecimento nas tres passadas: todas devolveram "retroactive space". Mantive
a correcao porque "retroactive space" nao existe em cirurgia, o roteiro escreve
"retrorectus space" e o proprio audio produziu "retrorectus" correto em 21
outros pontos. E o efeito do sotaque sobre um termo tecnico.

## Tres trechos para conferir de ouvido

Nestes a transcricao esta como o audio foi ouvido, mas o sentido nao fecha e as
tres decodificacoes divergem. Nao inventei palavra em nenhum:

| Tempo | Como esta | Observacao |
|---|---|---|
| 01:47 | "maybe they'll have the sternum belly" | "sternum" saiu nas tres, mas a frase nao fecha |
| 09:19 | "as one complex which together is anaginate" | as tres passadas devolveram coisa diferente e nenhuma e palavra do ingles |
| 31:10 | "which is close to the posterior sheath" | a referencia do seu documento diz "as close to posterior sheath" |

## Duas grafias que dependem de voce

| Tempo | Como esta | Alternativa | Por que |
|---|---|---|---|
| varios | TAP, P-TEP | TAPP, PeTEP | Ele pronuncia "tap" e "P-TEP". O seu roteiro escreve TAPP e PeTEP. As duas grafias tem o mesmo som, e "TAP" sozinho pode ser lido como transversus abdominis plane |
| 31:01 | intraparietal hernia | interparietal hernia | Duas decodificacoes sem dica devolveram "intraparietal", o seu roteiro usa "interparietal" e o mapeamento usa "intraparietal". Os dois sons sao praticamente iguais |

## Divergencia entre o mapeamento e o audio

O mapeamento diz que o Dr. Igor fala o numero do clipe em voz alta, como "P2-03"
e "P2 five". Neste audio nao existe nenhuma dessas marcacoes, nem com o filtro
de voz desligado. Ou este arquivo e outro material, ou ja passou por edicao.

## Formato

Nenhum problema de formato. Das 1423 linhas, 1313 tem quatro palavras ou menos,
109 tem cinco e uma tem seis, sempre nos casos em que cortar na quarta separaria
o que se le junto.

Noventa e dois blocos passam de 22 caracteres por segundo. E uma aula falada em
ritmo rapido, e baixar esse numero exigiria cortar palavras.

## Como refazer

```bash
python3 scripts/transcrever.py "videos/Aula 2 - Igor (compressed by happyscribe.com) (1).mp3" \
  --palavras "revisao/Aula 2 - Igor.json" \
  --saida "legendas/Aula 2 - Igor.srt"

python3 scripts/ajustar_sincronia.py \
  "videos/Aula 2 - Igor (compressed by happyscribe.com) (1).mp3" \
  "legendas/Aula 2 - Igor.srt"
```
