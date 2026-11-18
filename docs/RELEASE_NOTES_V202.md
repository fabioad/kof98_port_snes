# KOF'98 SNES v2.0.2

Correções baseadas em `kof98-feedback-videos.md`.

## Golpes corrigidos (validados em testes headless)

| Item | Correção | Teste |
|---|---|---|
| G01 | Kim, Hou'oh Tenbu Kyaku (QCB×2+A / MAX A+B) agora completa a sequência de chutes e a finalização (dano 115, antes 15) | `tools/test_kim_super_headless.py` |
| G04 | Chun-Li, Hyakuretsu Kyaku (B repetido, estado 57): 5 chutes em pé, vítima em hitstun entre eles e derrubada só no quinto | `tools/test_chunli_hyakuretsu_headless.py` |
| — | Chun-Li, Spinning Bird Kick (QCB+K, estado 52): 5 impactos e derrubada (mantido) | `tools/test_chunli_spinning_bird_headless.py` |
| G08 | Heidern, Neck Rolling (DP+A/B) tem a continuação do ataque à cabeça (estados 117/118) | `tools/test_heidern_grabs_headless.py` + vídeo |
| G10 | Iori, Aoi Hana: 3 etapas encadeadas, termina derrubando | `tools/test_iori_aoi_hana_headless.py` |

## Outras correções (parcialmente validadas)

- Command List: página de notação (A), rodapé de legenda, 10 linhas de golpes por página.
  Teste: `tools/test_command_list_headless.py`.
- Direção de projéteis multi-hit (B04) e MAX sem re-armar efeito (R02): código escrito, sem teste dedicado.
- Demo de abertura e menus (B14), encerramento mais lento (fade/hold): `test_endings.py` e
  `test_attract_demo_headless.py` passam.

## Limitações conhecidas

- O Hyakuretsu Kyaku da Chun-Li usa 6 sprites (preparação, 4 chutes, quinto chute repetido) porque o
  bloco de metadados da personagem estava a 54 bytes do limite de 64 KiB.
- O Hyakuretsu não avança mais ao iniciar: o passo à frente (`POST_CAL_VEL`, estado 57) ligava o
  latch de "sopro aéreo" (`F_TFLAGS` bit 4), que o caminho de acerto transformava em derrubada já
  no primeiro chute -- por isso os outros quatro erravam.
- Command List: os botões L/R de categoria foram removidos por falta de espaço no banco 50.
- G11 ("Lightning Kick") foi tratado como o Hyakuretsu Kyaku da Chun-Li; é uma inferência.
- Itens não verificados: B01, B02, B06–B13 e o restante da lista.

## Vídeo

`python3 tools/capture_v202_video.py` regrava o vídeo de demonstração (Kim, Chun-Li vs Sakura,
Heidern, Iori e Command List). O vídeo sai em 768x672, com áudio e sem textos de apresentação;
os dois golpes da Chun-Li entram em velocidade normal e em câmera lenta:

```
python3 tools/capture_v202_video.py --out work/videos/kof98_v202.mp4
```
