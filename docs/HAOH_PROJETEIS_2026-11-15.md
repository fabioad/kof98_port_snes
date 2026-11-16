# Haoh Shikou Ken: projétil visível e dano de super (15/11/2026)

## Sintoma

Os supers Haoh Shikou Ken da Yuri, do Ryo, do Robert e do Takuma entravam no
estado e acertavam, mas o projétil não aparecia para o jogador. Em alguns
casos o golpe parecia não disparar nada.

## Causa

1. **Disparo durante o flash.** A linha do ProjTab de duas variantes estava
   presa no frame 0 (`release = 0`). O motor criava o projétil no primeiro
   tick do estado, antes do `SuperPause` (4 ticks de flash + 28 de escurecida)
   e antes da pose de palma. O tiro atravessava e acertava o oponente durante
   o flash; quando o personagem fazia a pose, o projétil já tinha sumido.
   Afetava:

   - Yuri MAX Haoh (sid 107 / estado 550): a fonte cria o helper 555 no
     `AnimElem = 8`; agora sai no frame 7, como as versões fraca/forte;
   - Takuma Haoh (sid 111): o estado 1500 é só a carga; o helper real nasce
     no 1502 (`AnimElem = 3`). O port tocava apenas o 1500 e disparava no
     frame 0. O sid 111 agora toca o 1502 e dispara no frame 2.

2. **Comando do Takuma sombreado.** `QCFx2+P` casava primeiro com o atalho do
   Ryuuko Ranbu (sid 88), então a Haoh nem entrava. A prioridade foi
   invertida: `QCFx2+P` agora é Haoh; o Ryuuko continua no comando original
   `632146+P`.

3. **Sem trava de segurança.** O frame de release configurado pode não
   existir na animação compilada depois de um remapeamento de estado. O
   `ProjTab` agora limita o release ao último quadro do clipe, em vez de
   esperar para sempre por um frame que nunca chega.

## Arte: projétil normal, não o grande

O projétil grande da Haoh (frames 2070-2073 e 2100-2105 do pacote) chega a
**96x155** px. A página de efeito do motor é de 16 células 16x16 (2 KiB por
frame), e o orçamento de OAM do combate não comporta os ~40-60 cells desses
frames. Ele continua sendo desenhado com o clipe compacto do Ko'ou Ken da
Yuri, o mesmo usado por Ryo, Robert e Takuma.

Como a arte grande não entra no orçamento, o dano compensa:

| Personagem | Golpe | sid | Dano por contato | Total medido |
|---|---|---:|---:|---:|
| Yuri | Haoh fraco/forte | 85/87 | 22/24 (5 contatos) | 110/120 |
| Yuri | MAX Haoh | 107 | **60** (1 contato) | 60 |
| Ryo | Haoh fraco/forte/MAX | 85/86/87 | 14 (5 contatos) | 70 |
| Robert | Haoh fraco/forte/MAX | 109/110/111 | **44/50/60** (1 contato) | 44/50/60 |
| Takuma | Haoh | 111 | **56** (1 contato) | 56 |

Os Haoh em sids 109-111 são de um contato (o motor só aplica os cinco
contatos genéricos nos sids 85-89), então o dano por contato carrega a super
inteira. O Takuma passou a gastar 1000 de energia, como os outros supers; o
estado 1502 isolado não tinha custo próprio.

## Validação

```sh
python3 tools/test_haoh_projectile_headless.py
python3 tools/audit_projectile_release.py yuri ryo robert takuma
python3 tools/test_kyokugen_projectile_anim_headless.py
```

O teste headless verifica, para as dez variantes, que o estado entra, que o
spark nasce **com a animação já iniciada** (frame > 0), que desenha células
OAM de palette 2, que percorre a tela e que acerta o adversário. Saída do
build de 15/11 23:28:

```
PASS yuri Haoh weak (sid 85): frame 7, 27 cells, 173 px, 110 dmg
PASS yuri Haoh strong (sid 87): frame 7, 27 cells, 172 px, 120 dmg
PASS yuri MAX Haoh (sid 107): frame 7, 27 cells, 120 px, 60 dmg
PASS ryo Haoh weak (sid 85): frame 5, 27 cells, 174 px, 70 dmg
PASS ryo Haoh strong (sid 86): frame 5, 27 cells, 174 px, 70 dmg
PASS ryo MAX Haoh (sid 87): frame 6, 27 cells, 161 px, 70 dmg
PASS robert Haoh weak (sid 109): frame 7, 27 cells, 120 px, 44 dmg
PASS robert Haoh strong (sid 110): frame 7, 27 cells, 120 px, 50 dmg
PASS robert MAX Haoh (sid 111): frame 7, 26 cells, 119 px, 60 dmg
PASS takuma Haoh (sid 111): frame 2, 27 cells, 105 px, 56 dmg
```

O teste do Ko'ou Ken normal (`test_kyokugen_projectile_anim_headless.py`)
continua passando nos seis frames de Yuri, Ryo, Robert, Takuma e Andy. O
`test_category_d_batch2_headless.py` cobre os comandos do Takuma e da Yuri
MAX no mesmo build (40/40 casos, Haoh do Takuma com 56 de dano e MAX Haoh da
Yuri com 60).

## Build

- ROM `kof98-snes.sfc`: checksum **`$E04D`**, SHA-256
  `103849decff751aa…`, gerada em 15/11 23:46 (perfil PRO completo, com
  `KOF_OAM_TRUNCATE=1 KOF_SPRITE_BBOX_TRUNCATE=1`).
- `tools/verify_pvsnes_rom.py`: **OK** (Fast HiROM NTSC/U, 8 MiB).

## Arquivos

- `tools/calibration/projectiles.py` — release 7 para o MAX Haoh da Yuri.
- `tools/build_fight.py` — release do Takuma, remapeamento 1500→1502,
  prioridade de comando, dano das Haohs de um contato e trava de release.
- `tools/test_haoh_projectile_headless.py` — regressão.
