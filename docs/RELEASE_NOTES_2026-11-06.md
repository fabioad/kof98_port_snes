# Atualizações recentes — release 06/11/2026

## Golpes e personagens

- Correção de **80 golpes/variantes de 18 personagens**, validados em P1,
  P1 espelhado e P2.
- Fechamento dos **29 golpes incompletos** da auditoria funcional: golpes que
  entravam mas terminavam sem ataque efetivo ou só com o dano inicial da
  captura.
- Correção dos **100 casos de agarrão comum** (50 personagens, frente/trás),
  incluindo dano, soltura e retorno ao neutro.
- Fases ofensivas ausentes religadas em especiais e supers de 18 personagens
  (Iori, Shingo, Rugal, Omega Rugal, Saisyu, Heidern, Leona, Mature, Vice,
  Daimon, King, Kim, Chang, Choi, Yashiro, Shermie, Yamazaki e Blue Mary).
- **M. Bison:** Head Press/Devil Reverse com altura limitada e sem repetição.
- **Geese:** DP agora pula, acerta na descida e recupera rápido.
- **Ralf/Clark:** lançamentos de vítima limitados para não estourar o OAM.
- **Chun-Li, Ken, Ryu, Geese e Krauser:** supers, projéteis, agarrões e
  hitboxes aéreas revisados.
- **Yuri:** quadro de queda, backdash e sprites de corpo limpos; tweens
  sintéticos removidos.
- **Terry:** Power Geyser voltou a desenhar o pilar 48x80 na frente do
  oponente; hitbox alto, dano e guarda mantidos.
- **Normais de perto:** perfis de proximidade para os quatro botões do elenco,
  com seleção por distância e empurrão apenas no último acerto dos golpes
  multi-hit.

## Entrada e comandos

- Atalhos KOF adicionais para supers de **Yuri, Geese e Terry**, mantendo os
  comandos originais.
- Carga dos especiais BF consumida corretamente; um botão sozinho não repete
  mais o golpe.
- **Daimon:** FF/BB do dash voltaram a funcionar.
- Padrão de botões: **Y=WP, X=SP, B=WK, A=SK**; **L=esquiva**, **R=blowback**.
- Arremesso normal padronizado para todos os personagens, frente e trás.

## Modos e interface

- **TEAM PLAY:** nova tela de ORDER SELECT antes de cada confronto.
- **Omega Rugal sem MSU:** o atalho L+R não seleciona o Omega; Single Play
  pula Rugal/Omega e vai ao ending normal. Com MSU o fluxo continua igual.
- Menu de pausa com CONTINUE e EXIT.
- Corrigida tela preta dos endings.
- Corrigida cintilação no topo do HUD.
- Lista de comandos e navegação de menus ajustadas.

## Áudio e MSU-1

- Pacote aprovado Final Fight Guy com **17 músicas** integrado.
- Validação de módulos IT limitada a **64 padrões** antes do conversor.
- Corrigido congelamento de música/luta em pausas longas.
- Guitarra de **Rumbling on the City** reduzida ao mesmo volume da SA Yard.

## Estabilidade e validação

- Corrigidos congelamentos de animação no streaming MSU-1 e recuperação de
  seeks pendentes.
- **311 testes unitários** passaram.
- **400 seleções** de normais de perto/longe passaram no Snes9x headless.
- Testes de pausa longa no Snes9x e no Mesen.
- Capturas de regressão para golpes, Yuri e ORDER SELECT.

## Build

- ROM: `kof98-snes.sfc`
- SHA-256: `cf09b7c2c937ea52092641b046d13cb6e61fbd8c2d0a3d2e6a6a2c85f53d39de`
- MSU: `kof98-snes.msu`
- SHA-256: `9be860bfe972279a44ff4299fbdd952eefc6babe790e273be70914c71c334f0e`

Atualize **ROM e MSU juntos** e reabra o par no emulador.
