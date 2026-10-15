# Legenda

Projeto de legendagem: entra video ou audio, sai SRT com pontuacao corrigida e
sem nenhuma palavra alterada em relacao ao que foi falado.

## Como a linha e quebrada

Quatro palavras por linha e o alvo, em qualquer idioma. A linha so passa de
quatro quando cortar na quarta separaria palavras que se leem juntas, e nunca
passa de seis. Um bloco tem no maximo duas linhas, oito palavras e 42 caracteres
por linha.

A unica excecao as oito palavras e um bloco que ficaria menos de 0,8 segundos na
tela: ali a juncao com o vizinho vale mais do que a linha enxuta, porque um bloco
que ninguem consegue ler e pior.

`scripts/validar_srt.py` avisa sobre linha de cinco ou seis palavras e acusa erro
acima de seis.

Essa regra vale das legendas feitas a partir de 14 de outubro de 2026 em diante.
As legendas anteriores ficaram com a quebra antiga, de linhas mais cheias. Se
alguma delas for remontada a partir do JSON de revisao, ela sai no formato novo,
o que e esperado.

## Regra para arquivos da Cratheon

Arquivo cujo nome contem "Cratheon", em qualquer caixa: entregar sempre duas
legendas, nao uma.

1. `legendas/<nome>.srt`, em ingles, que e o idioma falado nesses arquivos.
   Transcricao fiel, sem trocar palavra.
2. `legendas/<nome>.pt-BR.srt`, em portugues, traduzida a partir da primeira,
   com a marcacao de tempo identica, bloco por bloco.

O texto editavel da traducao vai em `traducao/<nome>.pt-BR.txt`, montado com
`scripts/aplicar_traducao.py`.

Ainda assim, rode o reconhecimento de idioma em vez de fixar o ingles. Se a
deteccao apontar outro idioma num arquivo da Cratheon, avise antes de seguir,
porque isso significa que o material mudou.

Essa regra vale so para os arquivos da Cratheon. Para qualquer outro arquivo,
entregue uma legenda no idioma falado e so traduza se for pedido.

## Quando vem o roteiro junto

Se o usuario mandar o roteiro que a pessoa usou para gravar, guarde em
`roteiros/<nome>.<idioma>.txt` e alinhe a transcricao contra ele palavra por
palavra, com `difflib`, antes de fechar a legenda. O alinhamento acha os erros
de reconhecimento em segundos.

O roteiro orienta, mas nao manda: a legenda precisa bater com o que se ouve no
video. Quando o audio e o roteiro divergem, redecodifique a janela. Se a palavra
estiver no audio, ela fica na legenda mesmo fora do roteiro, e a divergencia vai
registrada na nota de revisao.

## Audio longo, com pausas e sotaque

Tres coisas que so aparecem em arquivo longo, aprendidas na aula de 33 minutos
do Dr. Igor:

1. O vocabulario de `--termos` vai em `hotwords`, reaplicado em todas as janelas
   de 30 segundos. O `initial_prompt` sozinho vale so para a primeira.
2. O filtro de voz come a primeira palavra quando ela e dita baixo na volta da
   fala. Em audio com pausas longas, rode tambem com `--sem-vad` e compare as
   duas passadas com `difflib`. Onde elas divergirem, decodifique a janela uma
   terceira vez, curta e com busca mais ampla, e deixe essa leitura decidir.
3. Depois de montar, rode `scripts/ajustar_sincronia.py` para encostar os tempos
   na borda da fala. Ele tambem avisa quando uma legenda cai dentro de um
   silencio longo, que e sinal de palavra inventada.

Nenhuma legenda pode conter uma pausa de fala no meio, e nenhuma palavra pode se
estender por cima de um silencio. As duas regras ja estao no gerador.

## Como e o fluxo

```bash
# 1. transcrever, guardando as palavras com tempo para revisao
python3 scripts/transcrever.py "videos/<nome>" \
  --saida "legendas/<nome>.srt" \
  --salvar-palavras "revisao/<nome>.json" \
  --termos "Cratheon"

# 2. conferir o formato
python3 scripts/validar_srt.py "legendas/<nome>.srt"

# 3. montar a versao em portugues
python3 scripts/aplicar_traducao.py \
  "legendas/<nome>.srt" \
  "traducao/<nome>.pt-BR.txt" \
  "legendas/<nome>.pt-BR.srt"
```

## O que nao fazer

- Nao fixar `--idioma`. Forcar um idioma que nao e o da fala devolve texto
  distorcido, com palavras inventadas.
- Nao trocar palavra da transcricao por conta propria. Quando um trecho sair
  duvidoso, redecodifique so aquela janela de tempo, cruze com outro modelo e
  registre a decisao num arquivo `legendas/<nome>.revisao.md`, com o segundo
  exato para o usuario conferir de ouvido.
- Nao cortar palavra para melhorar a velocidade de leitura da transcricao.
  Encurtar frase e permitido so na traducao.

## Edicao de video: video-use + Hyperframes

Quando o usuario mandar video para editar, a ordem e: decupar (cortar respiros e
erros) com o video-use, legendar, e so depois animar com o Hyperframes.

Preparacao, uma vez por sessao: `bash scripts/preparar_edicao.sh` e exporte o
`HYPERFRAMES_BROWSER_PATH` que ele imprime. Os repositorios ficam em
`ferramentas/` (fora do git). Leia `ferramentas/video-use/SKILL.md` antes de
editar; as Hard Rules dele valem, menos as duas trocadas abaixo.

1. Transcreva com o nosso `scripts/transcrever.py` (fluxo acima), nao com o
   ElevenLabs. Depois converta para o video-use:
   `python3 scripts/ponte_video_use.py transcricao "revisao/<nome>.json" --edit-dir "videos/edit" --id <id>`
   e rode `ferramentas/video-use/helpers/pack_transcripts.py --edit-dir videos/edit`.
2. Proponha o corte em portugues e espere o ok antes de renderizar. Monte
   `videos/edit/edl.json`, com `"subtitles": "master.srt"`.
3. A legenda sai da nossa regra (quatro palavras por linha), nunca do
   `--build-subtitles` do video-use:
   `python3 scripts/ponte_video_use.py legenda videos/edit/edl.json --saida videos/edit/master.srt`
   e depois `scripts/validar_srt.py`.
4. Animacoes: um projeto Hyperframes por slot em `videos/edit/animations/slot_<n>/`
   (`npx --yes hyperframes init . --example blank --non-interactive --skip-skills`).
   O CDN jsdelivr e bloqueado aqui: instale `gsap` com npm no slot e aponte o
   `<script>` para `node_modules/gsap/dist/gsap.min.js`. Para animar por cima do
   video, renderize com `--format webm` (fundo transparente) e ponha em `overlays`.
5. `python3 ferramentas/video-use/helpers/render.py videos/edit/edl.json -o videos/edit/final.mp4`
   (`--draft` para conferir os cortes antes). Confira quadros nos cortes antes de entregar.
