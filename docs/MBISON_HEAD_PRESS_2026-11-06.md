# M. Bison — Head Press e Devil Reverse (06/11/2026)

ROM verificada:
`727f8a2bee3a2e866e195ef4d9ce79f958a52628671b43bef2e9fdf6a56fde84`.

## Sintomas

- O pulo subia até ~126–127 px. O topo do sprite passava da linha 224 e o
  Y do OAM voltava ao início, desenhando o personagem na parte de baixo da
  tela.
- O golpe era acionado duas vezes: as regras de complemento aéreo do CMD
  (`air_du_x/y/a/b`) miravam 1205/1301 e casavam de novo com a carga ainda
  no buffer enquanto o personagem já estava no ar.

## Correções

- `state_vel` reduzido: 1201/1301 de `-12` para `-7`; 1205 de `-6` para
  `-4`.
- 1301 (Head Press) limitado a 2 frames de subida e encadeado ao state 1305
  (`StAirSpec`, com gravidade e clamp de chão), em vez de cair direto no
  pouso 1202.
- Regras de comando que entram em 1205/1301 no ar foram removidas com o novo
  filtro `cmd_drop_states`; os encadeamentos 1201→1205 e 1301→1305 continuam.
- A caixa do 1305 foi alargada e o HitDef armado no primeiro frame para o
  Head Press acertar durante a descida.

## Verificação headless

| Golpe | y_peak | Caminho de states | Dano |
|---|---:|---|---:|
| Devil Reverse | 64,0 px | 52 → 60 → 68 → 64 → 0 | 18 |
| Head Press | 52,0 px | 54 → 62 → 65 → 64 → 0 | 15 |

O caminho mostra uma única execução, sem reentrada em 1205/1301. A altura
máxima agora fica bem abaixo do topo da tela.

## Limites

O teste usa Kyo parado e a distância padrão de 24 px. A altura e a repetição
foram medidas em ticks do jogo; não é uma partida livre.
