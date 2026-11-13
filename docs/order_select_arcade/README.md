# ORDER SELECT do arcade (KOF'98) — referência

Capturado da ROM arcade (`kof98.zip` + `neogeo.zip`) rodando no **MAME 0.285**,
via script Lua (`-autoboot_script`) que insere ficha, dá start e espera o jogo
chegar sozinho ao ORDER SELECT (os timers confirmam modo ADVANCED e o time é
sorteado). Tela nativa: **320×224, 60 Hz**.

## Arquivos

| arquivo | o que é |
|---|---|
| `01_order_select_sem_lutadores.png` | o pedido: fundo azul/vermelho, `ORDER SELECT`, `VS`, números, `TIME` e `1ST PLAYER SELECT`, **sem os lutadores** |
| `02_fundo_mais_vs.png` | só o fundo listrado + `VS` (sem textos e sem lutadores) |
| `05_order_select_time18.png` | mesma composição com `TIME 18` (variação) |
| `04_camada_texto.png` | camada só de textos (RGBA, fundo transparente) |
| `06_camada_vs.png` | logo `VS` recortado (RGBA, fundo transparente) |

## Como foi feito

O MAME não tem como desligar a camada de sprites, e nesse jogo os lutadores
são sprites desenhados por cima do fundo. A tela é montada em etapas:
fundo + `VS` → lutadores entram → textos aparecem. Não existe quadro com o
texto já completo e sem os lutadores, então:

- `02` é o quadro em que o fundo e o `VS` já estão prontos e os lutadores
  ainda não entraram (6540/6550 do capture);
- `01` e `05` são esse fundo com os retângulos de texto (`ORDER SELECT`,
  `1ST PLAYER SELECT`, `TIME`, `1`, `2`, `3`) copiados do quadro completo,
  colados por máscara de diferença — os lutadores ficam de fora;
- `04` e `06` são as camadas separadas, úteis para redesenhar no port.

## Cores dominantes (para reduzir a 15 cores no SNES)

- faixa azul: `#000EA0`, `#002CD3`, `#001EB6`, `#0026BE`, `#0000 92`
  (textura ruidosa; base ~`#001EB6`, sombra ~`#000092`)
- faixa vermelha: `#A00800`, `#D31E08`, `#B60E00`, `#A90800`, `#980000`
  (base ~`#A90800`, realce ~`#D31E08`)
- faixa preta central: `#080808`, ruído `#0E0E00`
- `VS`: `#FFB026`, `#FF9800`, `#FFCB56`, contorno branco `#FFFFFF`
- letras de `ORDER SELECT` / `1ST PLAYER SELECT`: amarelo `#FFCB16` com
  contorno/sombra escura

## Ajustes de limpeza

- `CREDIT 00` removido das imagens (`01` e `02`): a faixa vermelha foi
  espelhada sobre o texto e o encontro suavizado com um degradê de 6 linhas,
  sem corte seco.
