# Legenda

Gera legendas em SRT a partir de um video ou audio, corrigindo pontuacao,
acentuacao e quebras de linha, sem trocar nenhuma palavra do que foi dito.

## O que o script faz

1. Extrai o audio do arquivo com `ffmpeg` em WAV mono de 16 kHz.
2. Transcreve com o Whisper `large-v3` (biblioteca `faster-whisper`), com marcacao
   de tempo palavra por palavra.
3. Monta as legendas respeitando os limites de leitura usados em legendagem
   profissional: no maximo 2 linhas, 42 caracteres por linha, 6 segundos por
   legenda e 1 segundo de duracao minima.
4. Grava dois arquivos: o `.srt` para usar no editor e um `.txt` com a
   transcricao corrida, para revisao.

## Como enviar o video

### Opcao 1: pelo navegador, para arquivos de ate 25 MB

1. Abra https://github.com/cooperation-ui/Legenda
2. No seletor de branch, no canto superior esquerdo da lista de arquivos,
   escolha `claude/beautiful-albattani-d5r647`.
3. Entre na pasta `videos`.
4. Clique em **Add file** e depois em **Upload files**.
5. Arraste o MP4 para a area de upload.
6. Escreva uma mensagem de commit e clique em **Commit changes**.
7. Avise o nome do arquivo que subiu.

O envio pelo navegador tem limite de 25 MB por arquivo.

### Opcao 2: pela linha de comando, para arquivos de ate 100 MB

```bash
git clone https://github.com/cooperation-ui/Legenda.git
cd Legenda
git checkout claude/beautiful-albattani-d5r647
cp /caminho/do/seu/video.mp4 videos/
git add videos/video.mp4
git commit -m "Adiciona video para transcricao"
git push -u origin claude/beautiful-albattani-d5r647
```

O limite por arquivo no Git comum e de 100 MB.

### Opcao 3: so o audio, para videos grandes

A legenda e feita a partir do audio, entao o video nao e necessario. Rode isto
na sua maquina e envie o `.m4a` resultante, que costuma ficar abaixo de 1 MB por
minuto de gravacao:

```bash
ffmpeg -i video.mp4 -vn -ac 1 -ar 16000 -c:a aac -b:a 48k audio.m4a
```

## Como rodar

```bash
pip install -r requirements.txt
python3 scripts/transcrever.py videos/meu-video.mp4
```

Com nomes proprios e termos tecnicos informados antes, o reconhecimento acerta
mais:

```bash
python3 scripts/transcrever.py videos/meu-video.mp4 --termos "Cratheon, HeyGen, Hyperframes"
```

Parametros disponiveis:

| Parametro            | Padrao               | Para que serve                                      |
|----------------------|----------------------|-----------------------------------------------------|
| `--saida`            | mesmo nome, com .srt | caminho do arquivo de legenda                       |
| `--modelo`           | `large-v3`           | modelo do Whisper (`large-v3`, `medium`, `small`)   |
| `--idioma`           | `auto`               | idioma falado, ou `auto` para reconhecer            |
| `--termos`           | nenhum               | nomes e termos que aparecem na fala                 |
| `--salvar-palavras`  | nenhum               | grava as palavras com tempo em JSON, para revisao   |
| `--palavras`         | nenhum               | remonta a legenda a partir de um JSON ja revisado   |

Deixe o `--idioma` em `auto`. Forcar um idioma que nao e o da fala produz um
texto distorcido, porque o modelo tenta encaixar o som em palavras do idioma
pedido.

## Revisar uma palavra sem transcrever de novo

A transcricao e a parte lenta. Para trocar uma palavra e remontar a legenda em
segundos, grave a lista de palavras com tempo na primeira passada:

```bash
python3 scripts/transcrever.py videos/meu-video.mp4 --salvar-palavras revisao/meu-video.json
```

Edite o campo `texto` da palavra errada no JSON e remonte:

```bash
python3 scripts/transcrever.py videos/meu-video.mp4 --palavras revisao/meu-video.json
```

## Conferir a legenda

```bash
python3 scripts/validar_srt.py legendas/meu-video.srt
```

O validador verifica numeracao, marcacao de tempo, sobreposicao, duracao,
numero de linhas e caracteres por linha. Velocidade de leitura acima de 22
caracteres por segundo sai como aviso, nao como erro, porque depende do ritmo
da fala.

## Como as legendas sao quebradas

As palavras sao agrupadas em frases e cada frase e dividida em blocos. Entre
dois blocos vizinhos, o script testa todas as posicoes de corte possiveis e fica
com a de melhor nota, que prefere, nesta ordem: cortar no fim de uma frase,
cortar depois de virgula, comecar o bloco seguinte por palavra de ligacao e
deixar os dois blocos com tamanho parecido. Terminar um bloco em artigo,
preposicao ou conjuncao e penalizado, para nao separar palavras que se leem
juntas.

## Requisitos

`ffmpeg`, `ffprobe`, Python 3.10 ou superior e os pacotes de `requirements.txt`.
O download dos pesos do `large-v3` ocupa cerca de 3 GB e acontece uma unica vez,
no primeiro uso.

## O que esta garantido e o que nao esta

Nenhuma palavra da transcricao e alterada pelo script. O ajuste e so de
pontuacao, maiusculas, acentuacao e quebra de linha.

O que o script nao controla e o reconhecimento errar uma palavra na hora de
ouvir, o que acontece mais com nomes proprios, girias e termos tecnicos. Por
isso existe o parametro `--termos`, por isso o `.txt` de transcricao corrida e
gravado junto e por isso a lista de palavras pode ser revisada em JSON.

Quando um trecho sai duvidoso, o caminho e redecodificar so aquela janela de
tempo, com busca mais ampla, e cruzar o resultado com outro modelo. Toda troca
de palavra feita nessa base fica registrada num arquivo de revisao ao lado da
legenda, como em `legendas/1310 - Cratheon.revisao.md`, com o segundo exato para
conferir de ouvido.

Em CPU, o processamento leva de 2 a 4 vezes a duracao do audio.
