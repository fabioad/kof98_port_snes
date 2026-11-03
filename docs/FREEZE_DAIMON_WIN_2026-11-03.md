# Travamento no início da pose de vitória do Daimon (03/11/2026)

## Sintoma

No SNES real com SD2SNES, a luta trava no começo da pose de vitória do
Daimon (estado 90 / anim 181). O print mostra o Daimon já na pose, com a
faixa superior do HUD corrompida. A música continua, como nos outros
travamentos de leitura MSU já documentados.

O que acontece exatamente nesse instante:

- `EnterState(90)` carrega o anim 181, cujos sprites são 49, 50, 51, 52,
  53 e 54 (6 elementos).
- O ActTab do estado 90 começa as três vozes de vitória (vozes 1, 2 e 3
  da tabela do Daimon) logo no início da pose.
- Os sprites 51 e 54 têm chunks que atravessam o fim de uma página de
  8 KiB do cache MSU. O clamp de CHR da correção do Ralf já cobre esses
  dois; o teste novo confirma que a pose inteira fica dentro de uma
  página.

O caminho de **voz** (`MsuReadAlignedFar`) não tinha nem o clamp de
página nem um contador correto. Era ele que travava.

## Causa 1: o contador do chunk de voz era sobrescrito pelo ponteiro

O leitor de voz usava dois scratchs que se sobrepõem:

```text
scr2 = $14  -> ponteiro de destino de 24 bits ($14, $15, $16)
scr3 = $16  -> contagem de bytes do chunk
```

`sta scr2+2` grava o banco do destino em `$16`, ou seja, **em cima de
`scr3`**. O valor gravado é `$7F` (127). A partir daí:

- o loop de saída copiava 127 bytes em vez dos 512 pedidos (ou do valor
  encurtado pelo clamp);
- `MRD_POS` avançava 127 bytes, não 512;
- a próxima iteração buscava de novo o mesmo setor, só que 127 bytes
  adiante, repetindo a operação até completar os 512 bytes.

Cada chunk de voz virava ~4 leituras MSU completas (seek + leitura de
512 bytes), em vez de uma. Numa voz de 2.600 bytes isso são ~21 buscas
por quadro, com prefixos variados; várias caem no último setor de uma
página de 8 KiB (por exemplo, a voz 0 do Clark, as vozes 34/36 do Ralf e
a voz 0 do Daimon). No SD2SNES isso termina no mesmo bloqueio de CPU dos
outros relatos. O áudio da voz também saía repetido/errado.

## Causa 2: a voz não passava pelo clamp de página

Mesmo com a contagem certa, uma leitura de voz de 512 bytes pode começar
no último setor de uma página de 8 KiB e atravessar o fim dela. O clamp
`MsuChrPageClamp` existia só no caminho de CHR (`MsuStageUploadFar`).
Aquelas vozes continuariam capazes de travar o console.

## Correção

`src/snes/fight_bridge.asm`:

1. `MsuReadAlignedFar` guarda a contagem em `scr6` **antes** de escrever
   o banco do ponteiro de destino. O loop de cópia e o avanço de
   `MRD_POS` usam `scr6`, então `scr2+2` pode usar `$16` sem destruir o
   contador.
2. O mesmo `MsuChrPageClamp` agora é chamado logo depois de alinhar o
   seek da voz. Se `prefixo + payload` passasse do fim da página, o
   payload é encurtado; o loop copia o resto na sequência e avança por
   `MRD_POS`, sem perder byte.

O clamp de CHR foi mantido como estava. O comentário dele agora cita
também as vozes.

## Testes

Unitários (`tools/tests/test_msu_chr_page_clamp.py`, 12 PASS):

- `DaimonWinPoseTests`: confirma que o estado 90 usa o anim 181
  (sprites 49–54), que 51/54 cruzariam a página sem o clamp, e que com o
  clamp todos os chunks da pose e todos os 223 sprites do Daimon ficam
  dentro de uma página e cobrem exatamente o `dmalen`.
- `MsuVoicePageClampTests`: confere todas as tabelas de voz MSU, simula o
  clamp e prova que ele cobre exatamente o total de cada amostra. Também
  verifica que o leitor de voz chama `MsuChrPageClamp`.
- Os testes antigos do Ralf continuam passando.

Headless:

- `python3 tools/test_msu_voice_alignment_headless.py`: **PASS 21
  vozes** do Clark, comparadas byte a byte com o `.msu`. Antes da
  correção do contador esse teste falhava já na voz 0 (byte 421 vinha
  zero). Agora as leituras avançam de 512 em 512 bytes.
- `python3 tools/test_msu_chr_visibility_headless.py`: **PASS**, 960
  páginas visíveis, 56 poses distintas.

Build:

- `make -f Makefile.pvsnes verify PVSNESLIB_HOME=...`: checksum
  **`$5904`**, verificação OK.
- O `.msu` não mudou de conteúdo (SHA-256
  `086369eb…50b7241`); só a ROM foi recompilada.
- Build de teste em `build/daimon_win_fix_20261103/` (copie o `.sfc` **e**
  o `.msu` juntos):
  - `kof98-snes.sfc`: SHA-256 `00f2d75e…6592a3`
  - `kof98-snes.msu`: SHA-256 `086369eb…50b7241`

## Teste no console

Copie **`kof98-snes.sfc` e `kof98-snes.msu` juntos** para o SD. Repita a
luta até o Daimon vencer e espere a pose/entrada das vozes de vitória.
Vale testar também:

- Jiraishin fraco do Daimon (voz 0, que também cruzava página);
- especiais do Ralf que usam as vozes 34/36;
- uma voz longa qualquer (Galactica, Ranbu) para conferir que o áudio
  deixou de repetir.

Se ainda travar, os próximos suspeitos são o firmware do SD2SNES
(1.11.2 corrige o incremento do ponteiro no fim do DMA) e uma diferença
entre o `.sfc` e o `.msu` copiados. Nesse caso, instrumentar
`RT_MSUFAIL`/`TEL_DROP` e confirmar que o layout do `.msu` no cartão é o
mesmo do build.
