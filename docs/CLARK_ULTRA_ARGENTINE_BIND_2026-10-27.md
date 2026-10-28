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
clarkBind86: 0,1,40,0 / 0,254,8,176 / 2,2,32,0 / ...   (antes)
```

A vítima ficava presa a 80 px do chão por até 254 frames, em qualquer
frame do estado. Agora a janela é de um frame (`5,5`) — a tabela mudou
de nome depois que 3010 passou para o slot 109, mas o conteúdo é:

```
clarkBind109: 0,1,40,0 / 2,2,32,0 / 3,3,36,176 / 4,4,20,176 / 5,5,8,176
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

## Cadeia completa do Ultra Argentine

Depois do fix do comando e do bind, o arremesso ainda parava na fase 1
(só ~1 de dano): os estados 3011-3016 e as vítimas 3020-3026 não tinham
slot de runtime. Agora a cadeia inteira está mapeada:

| estado MUGEN | sid | conteúdo |
|---|---|---|
| 3010 | 109 | agarrão, TargetState 3020, binds, anim 3010 |
| 3011 | 110 | elevação + 1º TargetLifeAdd, anim 3011 |
| 3012 | 111 | queda, anim 3012 |
| 3013 | 103 | repetição da elevação + 2º dano |
| 3014 | 104 | repetição da queda |
| 3015 | 105 | elevação final + 3º dano, anim 3015 |
| 3016 | 106 | arremesso final + 4º dano, anim 3016 |

- 103-106 são os slots livres de follow-up de ReversalDef; o Clark não
  tem reversal, então eles ficam livres para ele. 109-111 são os slots
  de grab importado.
- As vítimas 3020/3021/3022/3025/3026 mapeiam para o slot genérico
  `S_VHELD` (76), então a vítima fica presa e o atacante a reposiciona
  pelas janelas de bind a cada tick.
- `S_EXT_GRAB` passou de 109 para 103: `StVictimHeld` mantém a vítima
  presa enquanto o dono está em 103-111.
- `StateRet` agora chama `ThrowBind`: especiais importados que seguram
  a vítima (Clark 103-111, Mary 109-111) reposicionam o corpo preso.
  `ThrowBind` sai na hora quando ninguém está preso, então os especiais
  comuns não pagam nada além do teste.

Resultado headless (P1 fraco, P1 forte, Clark como P2, vítima na guarda,
vítima no canto e KO no meio da cadeia): a sequência é
109→110→111→103→104→105→106→0, a vítima fica em 76 por 434 ticks e o
dano total é 105 de 200 (o HitDef inicial ~1 + 4 × 26). O dano por hit
sai da fórmula do CNS (`-floor((((13-var(21))...`, com `damage_scale`
2.0); o port não aplica o escalonamento de combo do original, então a
soma fica um pouco acima da fonte (46 unidades escalonadas).

As animações 3020-3026 de vítima do original usam `ChangeAnim2` (sprites
do Clark). O port mantém a pose genérica de segurado (`S_VHELD`), como
nos outros arremessos; é uma diferença visual, não funcional.

## Regressões

- `tools/tests/test_clark_super_bind.py`:
  - comando forte do asset entra em 3000;
  - `clarkCmdTab` fraco/forte → sid 85;
  - `clarkBind109` sem `0,254` e com as 5 janelas corretas;
  - a cadeia 109→110→111→103→104→105→106→0 está ligada;
  - `clarkBind53` segue cada elemento;
  - nenhuma tabela `Bind` do roster tem linha que esconde uma janela
    posterior.
- Cadeia completa: P1 fraco/forte, Clark como P2, vítima na guarda, no
  canto e KO no meio do arremesso, sem travamento e com o dano cheio.
- `python3 -m unittest discover -s tools/tests` (187 testes) OK.
- 50/50 arremessos normais; guard-cancel Clark × Ralf e Clark × Vice;
  counter-grabs; reversal do Yamazaki; 21 vozes MSU alinhadas.
- 2.400 páginas de CHR MSU visíveis conferidas (114 poses).
- `make -f Makefile.pvsnes verify` OK.

ROM: checksum `$293F`.
