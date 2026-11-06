# Correção dos 18 personagens — 06/11/2026

**Resultado:** 80 golpes/variantes passaram em P1, P1 espelhado e P2: 240 execuções. Mais 23 verificações a longa distância não encontraram dano de captura sem vítima efetivamente presa. A suíte completa passou: 301 testes e 5.069 subtestes.

## ROM instalada

- ROM: `kof98-snes.sfc`, SHA-256 `3b3a53dac09dd4df04f7264d256c4942c57770148cb49d8c1899e389e805902f`.
- MSU: `kof98-snes.msu`, SHA-256 `12b5abcbd7ccb981ee1bb909b1a28f22965aa83df206f4aa32988ad21f395316`.
- ROM/MSU foram instalados juntos; o basename padrão preserva a busca dos PCM existentes. Feche e reabra a ROM no emulador para trocar os arquivos já carregados.
- Backup do par anterior e das tabelas: `build/remaining18/before_install/`.
- Build isolado: `make -f Makefile.pvsnes GEN_DIR=build/remaining18/gen_fight BUILD_INC=build/remaining18 MSU_NAME=kof98-remaining18 ROMNAME=kof98-remaining18 CUSTOM_OBJECT=1`.

## Implementação

- `tools/remaining_specials.py` liga as fases ofensivas antes ausentes em timelines nativas limitadas, usando os cels da origem. As variantes mantêm o state/comando de origem; fases internas são compactadas para evitar esgotar os slots do motor.
- Ataques colocados nos slots defensivos 78–84 foram movidos a slots que realmente executam ataques. Não foi sobrescrito um slot de golpe ou contra-ataque já usado.
- Capturas executam o dano via TargetLifeAdd somente depois do contato e do vínculo com a vítima. As fases de captura ficam na janela de estados reconhecida pelo motor. O avanço é interrompido na sequência presa para não carregar a vítima pela tela.
- Dano foi calibrado para a barra nativa de 200 HP; expressões de vida de 1000/1500 HP não são copiadas como bytes negativos fora da faixa.
- A classificação MAX preserva os controladores de custo da origem. O export de IDs de cels permite verificar a pose de vitória do Daimon por identidade de sprite, sem depender dos antigos índices de empacotamento. As declarações Geese foram deduplicadas com a mesma prioridade existente no gerador.
- O auditor lê o mapa de states efetivamente compilado, incluindo ataques realocados e continuações sintéticas.

## Golpes verificados por personagem

Números abaixo são states da origem; o valor depois dos dois-pontos é o dano final observado contra Kyo com 200 HP. Não são números de slots SNES.

### Iori

3200: 32 HP.

[Sequência capturada](../build/remaining18/final/fixed_iori_sequence.png).

### Shingo

3050: 48 HP, 3150: 42 HP.

[Sequência capturada](../build/remaining18/final/fixed_shingo_sequence.png).

### Rugal

1400: 25 HP, 1410: 29 HP, 3000: 39 HP, 3010: 43 HP, 3150: 49 HP, 3200: 39 HP, 3210: 43 HP, 3250: 49 HP.

[Sequência capturada](../build/remaining18/final/fixed_rugal_sequence.png).

### Omega Rugal

1025: 20 HP, 1070: 39 HP, 1085: 43 HP, 1090: 49 HP, 2400: 39 HP, 2600: 25 HP, 2700: 31 HP, 2800: 42 HP, 3000: 40 HP, 6000: 48 HP.

[Sequência capturada](../build/remaining18/final/fixed_omegarugal_sequence.png).

### Saisyu

1200: 18 HP, 1210: 22 HP, 3150: 48 HP.

[Sequência capturada](../build/remaining18/final/fixed_saisyu_sequence.png).

### Heidern

1200: 22 HP, 1210: 26 HP, 1300: 25 HP, 3010: 38 HP, 3050: 48 HP.

[Sequência capturada](../build/remaining18/final/fixed_heidern_sequence.png).

### Leona

1200: 18 HP, 1201: 22 HP, 1400: 18 HP, 1401: 22 HP, 3150: 42 HP.

[Sequência capturada](../build/remaining18/final/fixed_leona_sequence.png).

### Mature

1100: 22 HP, 1320: 24 HP, 1420: 22 HP.

[Sequência capturada](../build/remaining18/final/fixed_mature_sequence.png).

### Vice

3100: 34 HP, 3200: 44 HP.

[Sequência capturada](../build/remaining18/final/fixed_vice_sequence.png).

### Daimon

1200: 27 HP, 1300: 27 HP, 1500: 27 HP, 1510: 31 HP, 1700: 29 HP, 3000: 43 HP.

[Sequência capturada](../build/remaining18/final/fixed_daimon_sequence.png).

### King

1300: 22 HP, 1350: 26 HP.

[Sequência capturada](../build/remaining18/final/fixed_king_sequence.png).

### Kim

3100: 34 HP, 3110: 38 HP, 3120: 48 HP.

[Sequência capturada](../build/remaining18/final/fixed_kim_sequence.png).

### Chang

1000: 18 HP, 1010: 22 HP, 1350: 24 HP, 3500: 48 HP.

[Sequência capturada](../build/remaining18/final/fixed_chang_sequence.png).

### Choi

3050: 40 HP, 3060: 44 HP.

[Sequência capturada](../build/remaining18/final/fixed_choi_sequence.png).

### Yashiro

2000: 20 HP, 2100: 24 HP, 3000: 38 HP, 3010: 44 HP, 3500: 48 HP.

[Sequência capturada](../build/remaining18/final/fixed_yashiro_sequence.png).

### Shermie

1400: 27 HP, 1450: 31 HP, 7000: 20 HP, 7050: 24 HP, 8050: 48 HP.

[Sequência capturada](../build/remaining18/final/fixed_shermie_sequence.png).

### Chris

1200: 22 HP, 1250: 26 HP, 1400: 24 HP, 1450: 30 HP, 2150: 34 HP, 2250: 44 HP, 7100: 24 HP, 7150: 28 HP, 8150: 48 HP, 8155: 48 HP.

[Sequência capturada](../build/remaining18/final/fixed_chris_sequence.png).

### Mr. Big

1300: 20 HP, 1310: 28 HP, 3200: 38 HP, 3210: 44 HP.

[Sequência capturada](../build/remaining18/final/fixed_mrbig_sequence.png).

## Evidências e reprodução

- [80 famílias de comandos e todas as tentativas](../build/remaining18/final/repairs.json).
- [160 execuções no lado oposto/P2](../build/remaining18/final/side_checks_final.json).
- [23 verificações de captura a longa distância](../build/remaining18/final/grab_whiffs.json).
- [18 exemplos visuais](../build/remaining18/final/fixed_checks.json).
- Log da suíte: `build/remaining18_unit_tests_release.log`.
- Verificador da ROM: `python3 tools/verify_pvsnes_rom.py kof98-snes.sfc` — OK.

```sh
python3 tools/test_remaining_specials_headless.py build/remaining18/final
python3 build/remaining18/final/check_sides.py
python3 build/remaining18/final/check_whiffs.py
pytest -q tools/tests
```

## Limites

Validação funcional por entradas de controle na ROM real executada pelo Snes9x; nenhum golpe foi iniciado escrevendo seu state na RAM. Setup de posição, HP, poder e contexto aéreo usa RAM. A fonte canônica CNS/AIR foi preservada. São adaptações nativas de duração, fases e impacto: ataques com helpers recebem contato nativo quando o motor não executa o helper. Não se certifica equivalência visual ou todas as ramificações do MUGEN, todos os confrontos, modos ou cancelamentos. Billy e demais pendências fora dos 18 não fazem parte deste fechamento.
