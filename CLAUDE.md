# Legenda

Projeto de legendagem: entra video ou audio, sai SRT com pontuacao corrigida e
sem nenhuma palavra alterada em relacao ao que foi falado.

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
