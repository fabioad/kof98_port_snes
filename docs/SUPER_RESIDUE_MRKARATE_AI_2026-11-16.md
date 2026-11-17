# Resíduos de super e level do Mr. Karate (16/11/2026)

## Quadrados dourados depois do super

Os dois slots de efeito compartilham duas páginas OBJ de 2 KiB. Um projétil
transmite o atlas do frame atual para a página do seu slot; um spark estático
(SparkHit/SparkSuper/SparkMax/Explod) usa a mesma página com o atlas fixo.

Quando um projétil era consumido, a página continuava marcada nos caches
`FX_CACHE`/`FX_CACHEBANK`. Na parada de impacto (hit-stop) o NMI continuava
transmitindo páginas enquanto a OAM ficava congelada, então um frame podia
desenhar as células do projétil com os tiles do spark — os quadrados dourados
intermitentes vistos com Terry e Saisyu.

Correções:

- todo projétil consumido (acerto, bloqueio, clash, fim de animação ou TTL)
  invalida os dois caches de página; o próximo spark estático é obrigado a
  reenviar o atlas antes de desenhar;
- durante `pausecnt` a OAM é reconstruída com o estado congelado. O spark que
  nasce no impacto aparece corretamente após o primeiro upload, e nenhuma
  célula antiga do projétil fica presa na tela.

O invalidador vive no vão de 12 bytes entre `SuperFxSfx` e `ResetSuperFx`
(bank 50, `$0F64`) para não crescer o banco 126, que está cheio.

## Mr. Karate na CPU

O id 53 estava acima do limite antigo `cmp #49` de `AI_LoadTab`, então a IA
do boss caía na tabela do Kyo. O limite passou a ser `NROSTER`; o Mr. Karate
usa `mrkarateAiTab`. Além disso, `AI_one` calcula um nível efetivo por lado:
quando o lutador é o Mr. Karate, ele vale 9 mesmo que OPTIONS esteja em 1.
O HUD de luta mostra LEVEL 8 (o topo da escala de OPTIONS) nesse confronto.

A personalidade do boss usa zona curta, agressão/anti-aéreo no máximo e o
novo flag `AI_PF_COUNTER`: parte das leituras de ameaça vira contra-ataque
em vez de bloqueio. O restante do roster mantém a tabela e o nível normais.

## Verificação

```sh
make -f Makefile.pvsnes verify
python3 tools/test_super_sparks_headless.py
python3 tools/test_terry_geyser_headless.py
python3 tools/test_ai_headless.py
python3 tools/test_mrkarate_ai_headless.py
```

`test_mrkarate_ai_headless.py` confere a tabela própria (flag `$10`), o
digito LEVEL 8 no HUD e que uma investida do P1 é contra-atacada com
OPTIONS em 1.
