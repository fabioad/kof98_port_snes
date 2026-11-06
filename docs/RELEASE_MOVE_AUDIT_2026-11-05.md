# Auditoria funcional e inventário de adaptações — 05/11/2026

> **Atualização de 06/11:** os 100 casos de agarrão comum receberam uma
> [correção no fonte](NORMAL_THROWS_FIX_2026-11-06.md), com cobertura dos
> 50 personagens nas duas direções. Não foi feito build; os resultados de
> ROM abaixo são o registro anterior à correção.

## Resultado

**Critério de release confirmado pelo autor em 06/11: estabilidade do port
dentro dos limites do SNES.** Reutilização de clipes, cadeias reduzidas,
trajetórias adaptadas e substituições de mecânica são decisões intencionais.
Devem ser preservadas. Diferença em relação ao MUGEN, por si só, não é bug
nem bloqueador de release.

O inventário abaixo conserva a comparação com os pacotes de origem. As
recomendações anteriores de restaurar a execução original foram substituídas
pela prioridade de corrigir glitches e falhas funcionais. A Categoria D não
precisa reproduzir integralmente as versões MUGEN para ser aceita.

Na ROM examinada, os **50 personagens capturam e soltam a vítima** com pelo
menos um comando de agarrão comum, tanto para frente quanto para trás.
Entretanto, **19 personagens causam somente 1–2 HP** nesse agarrão. Portanto,
“sem agarrão” deve distinguir ausência de captura de agarrão incompleto.

Esta é uma auditoria de código/tabelas com teste funcional dos agarrões comuns.
Os especiais/supers abaixo têm evidência estática; não foi feita uma comparação
visual de cada golpe em execução no MUGEN e no SNES. Personagem sem falha nova
confirmada aqui não está automaticamente certificado para release.

## P0 — agarrão comum com dano praticamente ausente

Teste em VS, P1 contra Kyo parado, vítima com 200 HP, distância inicial de
25 pixels entre centros, comandos extraídos da CmdTab gerada. O resultado foi
igual nas duas direções:

- **1 HP:** Kyo, Kyo Nests, Kyo Ash, Rugal, Leona, Mature, Vice, Andy, Ryo,
  Athena, Kensou, Mai, Chizuru, Chang, Shermie, Billy, Lucky e Brian.
- **2 HP:** Omega Rugal.

Todos capturaram, soltaram e recuperaram o controle dentro de 600 ticks.
Isso confirma a captura, mas **não** um agarrão finalizado corretamente.

Causas comprovadas no código e nas tabelas:

- **Vice, Kensou, Chang e Brian:** `TargetLifeAdd` negativo fora da faixa
  de um byte com sinal. Exemplos: `-140 → 116`, `-152 → 104`,
  `-146 → 110`. O gerador grava `arg & 0xFF`; o runtime interpreta esse
  byte com sinal e termina **curando** a vítima. Repetindo com 100 HP,
  os quatro terminaram com **200 HP**, nas duas direções.
- **Kyo/Nests/Ash:** o evento de dano está no elemento 6 (índice 5),
  mas o clipe compilado do agarrão tem quatro elementos. O evento não
  é alcançado.
- **Shermie:** o dano está no elemento 11, mas o clipe compilado tem
  oito elementos. Além disso, o valor `-130` também excede o byte com
  sinal; corrigir só a duração da animação não resolve os dois problemas.
- **Andy e Ryo:** o bind remete a `811`; não basta tocar o primeiro
  estado de captura para preservar toda a finalização.
- **Leona:** o bind escolhido é `3305`, e a vítima já é solta no tick 3.
  O clipe compilado de 75 é o mesmo de 74.
- **Mai:** bind `821` com clipe compilado de um elemento; soltura no tick 5.
- **Athena, Chizuru e Lucky:** o bind usado não contém evento direto de
  dano; é necessário portar a lógica de origem/continuação, em vez de
  considerar o dano inicial da captura como resultado final.
- **Rugal, Omega Rugal, Mature e Billy:** dano de 1–2 HP confirmado;
  revisar a cadeia completa, os estados da vítima e os eventos de impacto.
  Esta auditoria não atribui uma causa única a esses quatro.

Arquivos centrais: [`wire_throw_chain`](../tools/build_fight.py), emissão do
`ActTab` no mesmo gerador e `AO_tlife` em
[`src/engine/fight.asm`](../src/engine/fight.asm).

### Dano de agarrão que merece calibração separada

- **Daimon, Joe, Geese e Sakura:** 7 HP; capturam e recuperam. É um resultado
  baixo, mas não foi classificado como ausência de agarrão sem definir o dano
  pretendido para o port.
- **Chris:** 121 HP; **Chun-Li:** 81 HP; **Blue Mary:** 76 HP;
  **King:** 71 HP. São candidatos a revisão de balanceamento em uma barra de
  200 HP, não prova de golpe ausente.

## Adaptações aceitas — agarrões especiais convertidos em ataques

Nestes casos, o HitDef de origem é de agarrão e o build aplica `throw: 0`
e `p2state: 0xFF`. Essa conversão faz parte das adaptações do port e não
exige restaurar a captura de origem. Validar o ataque adaptado conforme
seu comportamento no port:

- **Takuma:** Shin Kishin Geki `3100`.
- **Mai:** Toki Tsubute `1050`.
- **Yashiro:** Kujiku Daichi `2300`, Araburu Daichi `3600` e
  Ankoku Jigoku `3700`.
- **Shermie:** Whip `1200`, Spiral `1300` e Carnival `2100`.
- **Yamazaki:** Bakudan Pachiki `1400`.
- **Blue Mary:** Super Dunk `3000/30000`.
- **Geese:** Raimei Gouha Nage `1500` e Shinkuu Nage `1600`.
- **Mr. Big:** `1500/3100`.
- **Eiji:** Yamikari `3200`.

Esses nove personagens não foram classificados como sem agarrão comum.
As famílias acima são inventário de adaptação, não nove defeitos confirmados.

## Inventário — entradas de origem sem state próprio ligado

A comparação inclui o **CMD MUGEN original**, para documentar o que foi
eliminado ou substituído durante a adaptação. Isso não obriga incluir todos
os golpes do pacote no release. Só tratar como falha um comando previsto
para o port que não executa o comportamento esperado.

- **Athena:** Phoenix Fang Arrow aéreo `2000/2020/2050`. Os states
  `3000/3050/3100/4000` já tratados não substituem essas entradas aéreas
  de origem.
- **Mature:** Ebony Tears `1500/1501/1502` e SDM Heaven's Gates `3100`.
  Também faltam states próprios de variantes C/Z de Death Row, Metal
  Massacre, Despair e Sacrilege; as versões-base dessas famílias existem.
- **Leona:** Baltic Launcher `1300/1305` de origem. `1410/1411` são
  variantes Riot e devem ser avaliadas somente se essa forma fizer parte
  do escopo do release. Não confundir outros golpes renomeados no port
  com o Baltic Launcher original.
- **Benimaru:** MAX Raiko Katategoma `3350`; o normal `3300` está ligado.
- **Rugal:** Gravity Smash aéreo forte `1560`; a família tem outras
  entradas implementadas. Eye Beam já é adaptado por `1702`, portanto
  a ausência do root `1700` não foi contada como outro golpe faltante.
- **Kyo, Kyo Nests e Kyo Ash:** MAX 182 Shiki '99 `3350` e ramificações
  `1615/1620/1625`. O comando adicional `SHIKI_99` aponta para `3305`,
  não para o MAX `3350`. `1710` está ligado e não deve continuar sendo
  listado como ausente.

**Shingo `3150` está ligado no sid 78.** Não deve ser contado como ausente
por uma varredura que só examine os slots convencionais de especiais/supers.

Há outras variantes sem state próprio, mas várias são aliases, entradas
alternativas ou fases substituídas. A evidência bruta em
`build/release_audit_20261105/original_command_candidates.json` é uma lista de
**candidatos para revisão**, não uma contagem automática de golpes faltantes.
Guard cancels, AI, states de sistema e formas opcionais também precisam ser
filtrados antes de virar pendência de release.

## Inventário — variantes de origem aéreas com entrada terrestre no port

- **Ken:** Tatsumaki aéreo `1250`, sid 107.
- **Chun-Li:** Spinning Bird aéreo `1250`, sid 108.
- **Lucky:** Air Slam `4700`, sid 110.

Os states de origem têm `type = A`; as regras emitidas desses slots têm
`posture = 3` (S|C), sem o bit aéreo 4. Entrar e causar dano a partir do
chão não comprova o funcionamento da variante aérea de origem. A escolha
terrestre pode fazer parte da adaptação; não a alterar apenas pelo `type = A`
do pacote MUGEN.

**Sakura:** Ouka Kyaku `1400` é uma adaptação adicional: usa clipe emprestado
e o comando foi redirecionado para `1200`. Preservar essa escolha e testar
a execução adaptada, sem exigir equivalência ao mergulho original.

## Adaptações aceitas de animação, cadeia ou comportamento

As substituições abaixo são reais no código e foram confirmadas como
adaptações intencionais pelo autor. As diferenças descritas não constituem
uma lista de reconstrução para este release.

- **Omega Rugal:** RE usa a entrada Gravity Smash e clipes de golpe próximo;
  `1050/1055/8000/8005/2310` não preservam integralmente a execução original.
  O victim state `8001` não veio no pacote.
- **Choi:** `1200/1600/3100` reutilizam `1000`, `3200` reutiliza `1010`,
  `1100` usa `1160` e Ultimate Storm `2400` usa `2901`. Manter as
  trajetórias e famílias adaptadas.
- **Shermie:** Axle/Shoot `1000` e Shajitsu `7100` usam `7350`;
  Mugetsu `7225` também usa `7350`; variantes fracas/fortes e famílias
  distintas foram agrupadas.
- **Yashiro:** Odoru/Kujiku compartilham `2201`; Final Impact `3100` usa
  `3020`; Araburu usa clipe de outra família de agarrão.
- **Chris:** Direction Change/Shooting Dancer/Twister pulam para clipes de
  continuação; `1600/2100` são projéteis no port. As variantes de
  Orochinagi foram agrupadas no clipe `8110`.
- **Lucky:** seis entradas reativadas compartilham o clipe `3203` no build
  atual, incluindo Shoot, Finger Roll, Slam/Air Slam e Shoot Out.
  As diferenças de trajetória e execução da origem foram simplificadas.
- **King:** `3200/3600/3700/3800` usam o clipe `3400` (Silent Flash).
- **Brian:** `3300/3400/3500/3600` compartilham o clipe `3600`.
- **Chun-Li:** Houyoku Sen `3100` usa o clipe `3200` (Hazan Tenshou).
- **Heavy D!:** D. Shadow `2200` usa o clipe `2000`.
- **Joe:** Screw Upper `3010` usa `3100` e Slash Kick `1310` usa `1400`.
- **Chang:** Tekkyuu Dai Assatsu L2 `3400` usa o Haki Kyaku `1400`;
  a bola de metal também tem efeito aproximado.
- **Terry:** Double Kong `1700` usa Power Dunk `1400`; Power Charge MOW
  reutiliza clipes de outras variantes. Buster Wolf já tem adaptação de três
  contatos; isso não deve voltar à lista de “golpe inexistente”.
- **Andy:** Dan Da Dan `3200/3210/3250` foi reduzido a dois contatos;
  o loop original de rush não foi preservado.
- **Chin:** Hyper Long Walk Hell `2200` entra pelo clipe `2201`;
  revisar a sequência completa, sem confundir o rush adaptado com o original.
- **Mai:** MAX2 `2030` usa o launcher `1080`; o relatório anterior mede
  apenas 5 HP. Revalidar finalização e propriedades além do comando.
- **Rugal:** Beads Destruction `1800` usa clipe de soco `300`;
  o pacote não trouxe a AIR 1800. Eye Beam tem arte sintetizada.
- **Eiji:** Mukuro Nui `1600` usa o clipe `3100`.
- **Krauser:** Kaiser Claw `1700` usa o clipe `1300`.
- **Robert:** MAX Muei Senpuu `3270` usa `3220`; distinguir as variantes
  e conferir a sequência, além do dano total.
- **Sakura:** Ouka Kyaku e supers usam adaptações; revalidar a movimentação
  própria do mergulho e as finalizações.
- **Iori:** Tsumakushi e Koto Tsuki In forte continuam adaptações;
  Ya Sakazuki tem projétil nativo, sem preservar toda a lógica MUGEN.
- **Kyo/Nests/Ash:** Orochinagi e variantes usam fases/clipes sintetizados;
  a presença de `3550` não comprova o MAX Mushiki: o CNS identifica esse
  state como MAX Kamukura. Separar as famílias pelo CNS.
- **Clark:** as cadeias foram religadas; `1205/1305` e `1420` ainda usam
  poses emprestadas. Não foi confirmada nova falha funcional de especial
  nesta auditoria.
- **Chizuru:** os golpes de clone são executados pelo próprio corpo;
  movimentação corrigida nos casos documentados não adiciona a entidade do
  clone. AfterImage foi removido intencionalmente e não é, por si, bloqueador.

## Candidatos a testes de estabilidade

Os seguintes casos têm dependências de Helper, transições/expressões ou
continuações que o extrator representa parcialmente. **São candidatos a
testes de execução/recuperação, não falhas confirmadas nem exigências de
reimplementar Helpers e continuações MUGEN:**

- **Shingo:** MAX Burning Shingo `3150` e supers de rush.
- **Saisyu:** Tsumugari `3100/3110/3150`, Helper `3105` e continuações.
- **Heidern:** Final Bringer/Heidern End e drenagem dos contra-agarrões.
- **Daimon:** Arashi no Yama normal/MAX e seus encadeamentos/agarres.
- **Leona:** Earring/Slasher/Launcher e fases de supers.
- **Kim:** Houou Kyaku `3000/3020`, entradas de rush e finalizações.
- **Ken:** Shippuu `3100/3150`, Shinryuuken e suas fases.
- **Ryu:** super `3200 → 3201` e variantes aéreas de origem.
- **Vega:** continuações dos supers `3100/3150`.
- **Athena:** Crystal Bit e Helpers de corpo/ataque, além dos aéreos ausentes.
- **Ralf:** victim states e efeitos de queimadura ainda aproximados;
  a montaria já tem cadeia própria e não foi reclassificada como ausente.
- **Yuri:** MAX Ryuuko `560/561` consta como implementado com 10 HP no
  levantamento anterior; conferir execução e recuperação da adaptação.
- **Kensou:** Niku Man `2000` foi tratado como power-up sem dano;
  validar o efeito de suporte pretendido, e não apenas entrada/recuperação.

## Prioridade vigente para o release

1. Validar os 100 casos de agarrão comum após a próxima compilação. A
   correção dos 19 personagens está no fonte; ainda não foi validada na ROM.
2. Eliminar travamentos, vítima presa, falta de recuperação, cura indevida
   e eventos de impacto que nunca são alcançados.
3. Corrigir glitches gráficos reais: sprites invisíveis ou corrompidos,
   tiles/VRAM incorretos, posições fora da tela e resíduos após o golpe.
4. Confirmar que os comandos e pads previstos para o port funcionam nos
   dois lados, preservando as adaptações e o orçamento atual de recursos.

Restaurar fidelidade ao MUGEN, ampliar arte, criar Helpers/clones ou
reconstruir famílias intencionalmente simplificadas fica fora deste escopo.

Critério de aceite por golpe: executar o comportamento definido para o port,
respeitar os pads, aplicar o efeito/dano pretendido e devolver o controle
com sprites e estados válidos. Captura é exigida nos agarrões que o port
mantém como agarrões. Um `PASS` que só verifica sid e dano mínimo não
certifica ausência de glitches.

## Evidência e reprodução

- ROM: `kof98-snes.sfc`, SHA-256
  `93ceeb5160a7ef7f48cc3fbd7f88e414f5713de9277426aea94880b1877ae173`.
- MSU SHA-256:
  `3afe26e220bb7e1666e8b0609ea6b1eebc89ffab301a62914933692b77ba4726`.
- A ROM foi recompilada externamente durante a auditoria. Os testes foram
  repetidos no par fixado em `build/release_audit_20261105/93ceeb5160a7/`;
  os 100 resultados de dano permaneceram iguais aos da primeira ROM
  (`74f085e83863…`).
- **100 casos** de agarrão comum: 50 personagens × frente/trás.
- **10 casos adicionais** com 100 HP: Vice, Kensou, Chang, Shermie e Brian.
- Resultados finais: `throws.json` e `throw_healing.json` na pasta do par
  fixado; os JSONs registram hashes da ROM, MSU e core. As tabelas de input
  também foram copiadas para `tables/` nessa pasta.
- Tabelas/CNS analisados: `source_scan.json`; comandos MUGEN candidatos:
  `original_command_candidates.json`, na mesma pasta.
- Ferramenta: [`tools/audit_release_throws_headless.py`](../tools/audit_release_throws_headless.py).

```sh
python3 tools/audit_release_throws_headless.py
python3 tools/audit_release_throws_headless.py --chars vice kensou chang shermie brian --hp 100 --out build/release_audit_20261105/throw_healing.json
```

Para reproduzir exatamente o par auditado, use também
`--rom build/release_audit_20261105/93ceeb5160a7/kof98-snes.sfc`
e `--tables build/release_audit_20261105/93ceeb5160a7/tables`.

A ferramenta retorna código 1 se detectar ciclo incompleto, dano de até
2 HP ou cura acima da vida inicial. **Código 1 é esperado na ROM auditada.**
`CAPTURE` no log significa apenas que captura/soltura/recuperação aconteceram.

Limites: agarrão comum testado como P1, começando à esquerda de Kyo, nas duas
direções de input; não certifica inputs de P2, início espelhado, todas as
distâncias, todos os botões alternativos ou equivalência visual. A ROM e os
assets de gameplay não foram alterados por esta auditoria.
