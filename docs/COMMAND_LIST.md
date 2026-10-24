# Command list

Submenu de consulta de golpes por personagem. Fica disponível em qualquer
modo pelo menu de pausa.

## Uso

- **SELECT** durante a luta abre o menu de pausa.
- Selecione **COMMAND LIST** e confirme com **A/X/Y/START**.
- **B** ou **START** fecha a lista e volta ao menu de pausa.
- No menu de pausa, **B** ou **SELECT** fecha o menu e retoma a luta.
- **UP/DOWN** rola a lista (12 linhas visíveis).
- **LEFT/RIGHT** alterna entre a lista do **P1** e a do **P2**.
- O campo `P1`/`P2` no topo indica o lado ativo.
- `>` marca a linha selecionada.
- `+` marca um golpe que aquele lado já executou.
- A linha 8 mostra a legenda das categorias:
  `NRM CMD SPC SUP MAX THR SYS`.

## Controles (pad SNES)

| Botão | Ação |
| --- | --- |
| Y | soco fraco (WP) |
| X | soco forte (SP) |
| B | chute fraco (WK) |
| A | chute forte (SK) |
| L | esquiva parada |
| L + trás | esquiva para trás |
| L + frente | esquiva para frente |
| R | blowback |
| L + R | taunt |

Os botões de ombro são roteados em tempo de execução pelo `PushHist`
(`src/engine/fight.asm`): `L` vira o token MUGEN `c`, `R` vira `y+b` e
`L+R` vira `s`. Por isso o `_SNES.cmd` de cada personagem continua usando
os comandos MUGEN originais; a lista exibe o botão físico equivalente.

O layout fica no calibrador `assets/calibration/input_profiles.json`:

```json
"buttons": {
  "default": {"x": "Y", "y": "X", "a": "B", "b": "A",
              "c": "L", "z": "R"},
  "characters": {}
}
```

`buttons.default` vale para todo o elenco. Se um personagem precisar de
outro botão, adicione apenas a diferença em `buttons.characters`, por
exemplo `"leona": {"x": "B", "a": "Y"}` (troca WP/WK só na Leona). O build
aplica o override antes de montar `ButtonTab` e a command list.

### Yuri (pacote ohgaki)

O pacote da Yuri usa a ordem de botões do Neo Geo nos comandos MUGEN
(`a`=soco fraco, `x`=soco forte, `b`=chute fraco, `y`=chute forte), em vez
da convenção padrão do pacote (`x`=WP, `y`=SP, `a`=WK, `b`=SK). O gerador
`tools/gen_char_cfg.py` traduz apenas os tokens dos comandos dela para a
convenção padrão; o pad físico continua igual ao resto do elenco:

| Botão | Yuri |
| --- | --- |
| Y | soco fraco |
| X | soco forte |
| B | chute fraco |
| A | chute forte |

Assim os especiais também caem nos botões certos: QCF+Y (Ko-Ou-Ken fraco),
QCF+X (forte), QCB+Y/X (Saiha), HCB+B/A (Senkai Kyaku) e DP+B/A (Kuuga).

Cada linha mostra:

```
> NOME DO GOLPE     COMANDO     CAT
```

O comando é traduzido para o pad SNES do personagem (A/B/X/Y/L/R/START),
usando o mesmo mapa `buttons` que o motor usa para ler o controle. Os
movimentos de sistema com `L`/`R` (esquiva, rolls, blowback e taunt) são
mostrados pelo botão físico, e não pelos tokens MUGEN internos.

## Categorias

| Tag | Categoria | Slots |
| --- | --- | --- |
| `NRM` | Normal | 5-8, 19-26 |
| `CMD` | Command move / blowback | 67 |
| `SPC` | Special | 48-66 |
| `SUP` | Super normal | 85-89 sem a flag MAX |
| `MAX` | MAX super / ativação MAX | 85-89 com a flag MAX do personagem; 96 |
| `THR` | Agarre | 74 |
| `SYS` | Sistema (dash, dodge, roll, taunt, charge) | 45-47, 69, 78-84, 94-97 |

A flag MAX é **por personagem** (`CH_MAXMASK` no descritor), não um slot
fixo. Na maioria do elenco o 87 é o MAX do primeiro super e 88/89 são o
segundo super (fraco/forte), mas há exceções: Iori 89, Heavy D! 86, Lucky
86, Ryu 88, Vice 89 e Omega Rugal 88/89. O gerador decide isso pelo nome
do estado, pelo formato de custo SDM do CNS e por `MAX_SIDS_OVERRIDE`.

## Origem dos nomes e comandos

O gerador (`tools/build_fight.py`) monta a lista por personagem a partir de:

1. Labels `[State -1, NOME]` do CMD sanitizado (`<Char>_SNES.cmd`);
2. CMD original do personagem, quando o label sanitizado é genérico
   (`special_48`, `sys_45`, etc.);
3. `txt/ReadMe(ENG).txt`, casando sequência de direções + classe de botão
   (soco/chute);
4. fallback legível por categoria (`SPECIAL`, `THROW`, `MAX MODE`, ...).

Os botões MUGEN são convertidos para os rótulos SNES do próprio personagem.
Os comandos longos são compactados (`QCF`, `QCB`, `DP`, `HCF`, `HCB`,
`QCBHCF`, `QCFx2`, ...). Nomes são limitados a 16 caracteres e comandos a 11
para caber no HUD de 32 colunas.

## Formato gerado

Personagens com descritor fixo (Iori, Kyo, Rugal, etc.) guardam a tabela no
próprio `<char>_spr.inc`. Personagens importados usam:

- `build/gen_fight/<char>_cmdlist.inc` — bloco individual (build standalone);
- `build/gen_fight/cmdlist_pool.inc` — pool deduplicado usado no build PVS.

Cada tabela começa em `<char>CmdList`:

```
<char>CmdList:
    .db count
    .db sid, categoria
    .dw ponteiro_nome, ponteiro_comando
```

Os ponteiros são de 16 bits no banco da tabela. O descritor do personagem
aponta para ela em `CH_CMDLIST` (offset 88) e `CH_CMDLISTBANK` (offset 90;
zero significa “usar `F_TBANK`”).

## Runtime

- `CL_VARS` fica em `$4F40` (PVS) / `$0800` (standalone) e guarda:
  `CL_OPEN`, `CL_SIDE`, `CL_SEL`, `CL_TOP`, `CL_COUNT`, `CL_LAST1/2`,
  `CL_SEEN1/2` (48 bytes por lado).
- `CmdTrack` é chamado por `EnterState`. Se o modo for PRACTICE e o state
  estiver na lista, marca `CL_SEEN1/2` e grava o último sid.
- `CmdListTick` trata a navegação e congela a luta enquanto o menu está
  aberto. Quando aberto pelo menu de pausa, `CL_FROM_PAUSE` faz o fechamento
  voltar para CONTINUE/COMMAND LIST/EXIT em vez de retomar a luta.
- `CmdListDraw` desenha o cabeçalho, a legenda, as 12 linhas e a ajuda nas
  linhas 7-21 do BG3.
- `CmdListClearPanel` limpa a área ao fechar (também usado pelo menu de
  pausa).

## Testes

```sh
python3 -m unittest tools.tests.test_command_list
python3 tools/test_command_list_headless.py
```

O primeiro valida cobertura, tamanho, caracteres e categorias de todos os
personagens. O segundo executa o fluxo real de menu/luta no Snes9x libretro.
