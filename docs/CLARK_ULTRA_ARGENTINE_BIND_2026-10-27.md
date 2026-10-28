# Clark × Vice — Ultra Argentine e janelas de TargetBind (27/10/2026)

## Relato

No SNES real, uma luta **Clark × Vice** travou. O sintoma é o mesmo das
ocorrências anteriores: os lutadores e o relógio param, a tela fica no
último quadro e o áudio continua.

## O que foi encontrado no Clark

Dois defeitos concretos no comando e no arremesso do Ultra Argentine:

### 1. O comando forte entrava no estado de continuação

`HCBHCB + Y` mapeava para o estado **3010**, que é o *follow-up* do
arremesso, não o iniciador. O CNS original tem duas entradas
`value = 3000` (fraco e forte) e nenhuma entrada que leve direto a 3010.
Entrar em 3010 sem vítima deixa o Clark numa pose invulnerável
(`NotHitBy SCA`) sem golpe e sem HitDef que ligue o arremesso.

- `tools/gen_snes_cmd.py`: forte `3010` → `3000`.
- `assets/characters/Clark-KOF98/Clark_SNES.cmd`: idem.
- `clarkCmdTab`: as linhas 1 e 2 (fraco/forte) agora apontam para o
  sid 85 (estado 3000).

### 2. Janela de bind de 254 frames a −80 px

O `TargetBind` final de 3010 usa `AnimElemTime(6) = 0`. O compilador só
entendia `AnimElemTime(N) >= 0` / `< 0` / `AnimElem = N`, então essa
linha caía na janela padrão `0..254`. O resultado era:

```
clarkBind86: 0,1,40,0 / 0,254,8,176 / 2,2,32,0 / ...
```

A vítima ficava presa a 80 px do chão por até 254 frames, em qualquer
frame do estado. Agora a janela é de um frame (`5,5`):

```
clarkBind86: 0,1,40,0 / 2,2,32,0 / 3,3,36,176 / 4,4,20,176 / 5,5,8,176
```

## Correção mais ampla das janelas de bind

Ao revisar o gerador apareceram três lacunas que produziam o mesmo tipo
de "vítima colada" em outros personagens:

- `AnimElemTime (N)` com espaço antes do parêntese (Mary, Heidern) não
  era reconhecido.
- `AnimElemNo(0) = N` (Vice, King) não era reconhecido.
- `AnimElemTime(N) < M` com `M > 0` delimitava o fim de um elemento, mas
  o início ficava em `0`, gerando `0..254`.

Além disso o gerador emitia as linhas na ordem do CNS, enquanto o motor
usa a **primeira** janela que casa. No MUGEN todos os `TargetBind` que
casam são executados e o **último** vence. Uma linha abrangente no começo
escondia todas as linhas específicas seguintes. Exemplos reais:
`changBind75`, `heidernBind75`, `joeBind75`, `terryBind75`,
`maryBind110` e o `clarkBind53` (Mount, estado 1210), que prendia a
vítima em um único deslocamento durante todo o arremesso.

`canon_bind()` resolve a tabela por frame (último vence) e emite apenas
as transições, de modo que o motor e o MUGEN concordam. Isso reduziu 52
linhas no total e não alterou nenhum throw normal: o audit headless
continua 50/50.

## O que não foi reproduzido

O travamento em si **não foi reproduzido** no Snes9x:

- 5 lutas Clark × Vice controladas pela IA, 3.000 frames cada;
- 4 lutas com fuzz de entradas nos dois lados (4.000 frames cada);
- 192 casos de guard-cancel/rolamento com Vice;
- matriz de especiais/supers dos dois personagens;
- arremessos normais dos dois lados e 50/50 no roster;
- 2.400 páginas de CHR MSU visíveis conferidas byte a byte, 111 poses.

Isso mantém em aberto a hipótese de timing de hardware/SD2SNES (leitura
MSU) para travamentos raros. O firmware do SD2SNES MKII deve estar em
1.11.2 ou mais novo.

## Pendências conhecidas do Ultra Argentine

Os estados 3011/3012 (e as vítimas 3020/3021) do arremesso completo não
estão mapeados no port. O super faz a fase 1 e causa ~1 de dano, em vez
do dano cheio do original. Isso é fidelidade, não travamento: o estado
86 tem saída garantida para o neutro quando a animação termina.

## Regressões

- `tools/tests/test_clark_super_bind.py`:
  - comando forte do asset entra em 3000;
  - `clarkCmdTab` fraco/forte → sid 85;
  - `clarkBind86` sem `0,254` e com as 5 janelas corretas;
  - `clarkBind53` segue cada elemento;
  - nenhuma tabela `Bind` do roster tem linha que esconde uma janela
    posterior.
- `python3 -m unittest discover -s tools/tests` (186 testes) OK.
- `make -f Makefile.pvsnes verify` OK.

ROM: checksum `$93C9`.
