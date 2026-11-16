# Auditoria de projéteis e frame de lançamento (15/11/2026)

## Escopo

Todas as linhas ativas de `ProjTab` geradas por `tools/build_fight.py`:
**153 linhas em 47 personagens**. Para cada linha o relatório mostra:

- **vx**: velocidade horizontal em pixels por tick (formato 8.8; `0.00` =
  projétil estacionário);
- **release**: frame 0-based da animação de lançamento em que o motor cria o
  projétil;
- **fonte**: frame do controlador/helper do CNS original que inicia o
  projétil;
- **status**: `ok`, `early` (sai antes da pose de disparo), `late` (sai
  depois) ou `source-out-of-anim` (a fonte dispara num frame que a animação
  compilada não tem).

A ferramenta é reproduzível:

```sh
python3 tools/audit_projectile_release.py
python3 tools/audit_projectile_release.py ryu ken robert takuma
python3 tools/audit_projectile_release.py --json build/proj_audit.json
```

## Resultado

- **138 linhas alinhadas** com a fonte (`ok`);
- **15 exceções** documentadas abaixo;
- Os seis shotos (Ryu, Ken, Ryo, Robert, Takuma e Yuri) usam o frame da pose
  de braço estendido e tiveram o wind-up compactado para não ficarem mais
  lentos que o padrão antigo. O teste headless de combo
  (`tools/test_projectile_speed_combo_headless.py`) passa em todos os 28
  casos (forte em pé/agachado, botão fraco/forte).

## Projéteis principais

| Personagem | Golpe (CNS) | sid | vx px/t | dano | release (0-based) | status |
|---|---|---:|---:|---:|---:|---|
| ryu | 弱灼熱波動拳 | 48 | 3.00 | 14 | 3 | ok |
| ryu | 強灼熱波動拳 | 49 | 4.00 | 18 | 3 | ok |
| ryu | 弱波動拳 | 52 | 4.00 | 14 | 3 | ok |
| ryu | 強波動拳 | 53 | 4.00 | 14 | 3 | ok |
| ryu | 弱真空波動拳 | 85 | 5.00 | 5 | 4 | ok |
| ryu | 強真空波動拳 | 86 | 5.00 | 5 | 4 | ok |
| ryu | MAX真空波動拳 | 88 | 8.00 | 8 | 4 | ok |
| ken | 弱波動拳 | 54 | 4.00 | 14 | 3 | ok |
| ken | 強波動拳 | 55 | 4.00 | 14 | 3 | ok |
| robert | 弱龍撃拳 | 58 | 4.00 | 18 | 3 | ok |
| robert | 強龍撃拳 | 59 | 6.00 | 22 | 3 | ok |
| robert | 弱龍撃拳(裏) | 60 | 4.00 | 14 | 5 | ok |
| robert | 弱覇王翔吼拳 | 109 | 4.00 | 44 | 7 | ok |
| robert | 強覇王翔吼拳 | 110 | 4.00 | 50 | 7 | ok |
| robert | MAX覇王翔吼拳 | 111 | 17.00 | 60 | 7 | ok |
| takuma | 弱虎煌拳 | 48 | 2.50 | 16 | 3 | ok |
| takuma | 強虎煌拳 | 49 | 3.50 | 20 | 3 | ok |
| takuma | 弱虎煌拳(裏) | 109 | 6.00 | 14 | 6 | ok |
| takuma | 強虎煌拳(裏) | 110 | 6.00 | 18 | 6 | ok |
| takuma | Haoh Shikou Ken | 111 | 5.00 | 56 | 2 | ok |
| ryo | 弱虎煌拳 | 60 | 2.50 | 14 | 3 | ok |
| ryo | 強虎煌拳 | 61 | 5.00 | 18 | 3 | ok |
| ryo | 虎煌撃 | 64 | 5.00 | 13 | 6 | ok |
| ryo | 弱覇王翔吼拳 | 85 | 4.00 | 14 | 5 | ok |
| ryo | 強覇王翔吼拳 | 86 | 4.00 | 14 | 5 | ok |
| ryo | MAX覇王翔吼拳 | 87 | 17.00 | 14 | 6 | ok |
| ryo | 弱虎煌拳(裏) | 107 | 4.00 | 14 | 5 | ok |
| ryo | 弱空中虎煌拳 | 109 | 5.00 | 14 | 3 | ok |
| ryo | 強空中虎煌拳 | 110 | 5.00 | 14 | 3 | ok |
| yuri | 弱虎煌拳 | 48 | 3.00 | 14 | 3 | ok |
| yuri | 強虎煌拳 | 49 | 4.00 | 18 | 3 | ok |
| yuri | 弱砕破 | 50 | 0.00 | 14 | 8 | ok |
| yuri | 強砕破 | 51 | 0.00 | 18 | 8 | ok |
| yuri | 弱雷煌拳 | 58 | 4.00 | 12 | 2 | ok |
| yuri | 強雷煌拳 | 59 | 6.00 | 16 | 2 | ok |
| yuri | 弱覇王翔吼拳 | 85 | 5.00 | 22 | 7 | ok |
| yuri | 強覇王翔吼拳 | 87 | 6.00 | 24 | 7 | ok |
| yuri | MAX覇王翔吼拳 | 107 | 5.00 | 60 | 7 | ok |
| sakura | 弱波動拳 | 52 | 4.00 | 14 | 4 | ok |
| sakura | 強波動拳 | 53 | 7.00 | 18 | 4 | ok |
| kyo | state 1000 | 48 | 3.00 | 14 | 4 | ok |
| kyo | 強百八式・闇払い | 49 | 4.00 | 18 | 4 | ok |
| iori | 弱百八式・闇払い | 48 | 2.75 | 12 | 3 | ok |
| iori | 強百八式・闇払い | 49 | 3.75 | 16 | 3 | ok |
| terry | 弱パワーウェイブ(表) | 58 | 3.00 | 22 | 6 | ok |
| terry | 強パワーウェイブ(表) | 59 | 4.00 | 26 | 6 | ok |
| terry | 弱パワーウェイブ(裏) | 60 | 4.00 | 14 | 6 | ok |
| terry | 弱パワーゲイザー | 85 | 0.00 | 5 | 6 | ok |
| terry | 強パワーゲイザー | 86 | 0.00 | 6 | 6 | ok |
| terry | MAXパワーゲイザー | 87 | 0.00 | 10 | 6 | ok |
| andy | 弱飛翔拳 | 52 | 0.00 | 26 | 4 | ok |
| andy | 強飛翔拳 | 53 | 0.00 | 28 | 5 | ok |
| andy | 弱飛翔拳(裏) | 58 | 4.00 | 14 | 3 | ok |
| andy | 強飛翔拳(裏) | 63 | 4.00 | 14 | 3 | ok |
| joe | 弱ハリケーンアッパー(裏) | 60 | 4.00 | 14 | 6 | ok |
| joe | 弱ハリケーンアッパー | 62 | 4.00 | 14 | 6 | ok |
| joe | 強ハリケーンアッパー | 65 | 7.00 | 14 | 6 | ok |
| joe | 強スクリューアッパー | 107 | 1.25 | 14 | 5 | ok |
| joe | 爆烈ハリケーンタイガーカカト | 108 | 7.00 | 14 | 2 | early |
| athena | Psychic Ball Corto | 48 | 4.00 | 20 | 5 | ok |
| athena | Psychic Ball Largo | 55 | 9.00 | 20 | 5 | ok |
| athena | state 3050 | 86 | 0.00 | 14 | 2 | late |
| king | ベノムストライク  (Benom Strike) | 48 | 4.00 | 18 | 3 | ok |
| king | ダブルストライク  (Outrage / Hard) | 49 | 7.00 | 11 | 3 | ok |
| benimaru | 弱雷靱拳 | 48 | 3.00 | 14 | 5 | ok |
| benimaru | 強雷靱拳 | 49 | 4.00 | 18 | 4 | ok |
| benimaru | 弱空中雷靱拳 | 50 | 4.00 | 16 | 2 | ok |
| benimaru | 強空中雷靱拳 | 51 | 5.00 | 20 | 2 | ok |
| benimaru | 弱雷光拳 | 85 | 4.00 | 6 | 6 | ok |
| benimaru | 強雷光拳 | 86 | 4.00 | 8 | 5 | ok |
| benimaru | MAX雷光拳 | 87 | 4.00 | 10 | 5 | ok |
| kensou | Light Cho kyo dan | 56 | 4.00 | 14 | 3 | ok |
| kensou | Hard Cho kyo dan | 57 | 7.00 | 16 | 3 | ok |
| geese | 疾風拳 | 58 | 7.00 | 12 | 3 | ok |
| geese | 烈風拳(表) | 60 | 3.00 | 12 | 4 | ok |
| geese | 烈風拳(裏) | 62 | 5.00 | 14 | 4 | ok |
| geese | ダブル烈風拳(表) | 65 | 4.00 | 16 | 4 | ok |
| geese | 弱レイジングストーム | 85 | 0.00 | 38 | 8 | ok |
| geese | 強レイジングストーム | 86 | 0.00 | 38 | 8 | ok |
| krauser | 弱ブリッツボール・上段 | 54 | 4.00 | 14 | 3 | ok |
| krauser | 強ブリッツボール・上段 | 55 | 4.00 | 14 | 3 | ok |
| krauser | 弱ブリッツボール・下段 | 56 | 4.00 | 14 | 3 | ok |
| krauser | 強ブリッツボール・下段 | 57 | 4.00 | 14 | 3 | ok |
| mrbig | 弱グランドブラスター | 54 | 3.00 | 14 | 6 | ok |
| mrbig | 強グランドブラスター | 55 | 4.00 | 18 | 6 | ok |
| mrbig | 弱ブラスターウェイブ | 87 | 5.00 | 12 | 5 | ok |
| mrbig | 強ブラスターウェイブ | 88 | 5.00 | 16 | 5 | ok |
| mrbig | MAXブラスターウェイブ | 110 | 6.00 | 30 | 0 | early |

## Exceções conhecidas

| Personagem | Golpe (CNS) | sid | state | vx | release | fonte | status | observação |
|---|---|---:|---:|---:|---:|---:|---|---|
| rugal | 弱烈風拳 | 48 | 1000 | 3.00 | 2 | 6 | source-out-of-anim | fonte dispara num frame que a animação compilada não tem; revisar mapeamento de anim |
| rugal | 強烈風拳 | 49 | 1010 | 4.00 | 2 | 6 | source-out-of-anim | fonte dispara num frame que a animação compilada não tem; revisar mapeamento de anim |
| omegarugal | state 1040 | 52 | 1040 | 3.90 | 2 | 16 | source-out-of-anim | fonte dispara num frame que a animação compilada não tem; revisar mapeamento de anim |
| omegarugal | state 1045 | 53 | 1045 | 6.40 | 2 | 16 | source-out-of-anim | fonte dispara num frame que a animação compilada não tem; revisar mapeamento de anim |
| omegarugal | state 1050 | 107 | 1050 | 3.90 | 2 | 18 | source-out-of-anim | fonte dispara num frame que a animação compilada não tem; revisar mapeamento de anim |
| omegarugal | state 1055 | 108 | 1055 | 5.00 | 2 | 18 | source-out-of-anim | fonte dispara num frame que a animação compilada não tem; revisar mapeamento de anim |
| joe | 爆烈ハリケーンタイガーカカト | 108 | 3100 | 7.00 | 2 | 40 | early | helper tardio; mantido no default para não atrasar o super |
| athena | state 3050 | 86 | 3050 | 0.00 | 2 | 0 | late | super sintético; sem helper direto |
| lucky | FINGERROLL <2> MOTION | 55 | 2600 | 7.00 | 2 | 4 | early | diferença de 1 frame; perfil balístico próprio |
| lucky | SHOOT <2> FADEAWAY SHOT | 87 | 2100 | 4.00 | 2 | 3 | early | diferença de 1 frame; perfil balístico próprio |
| lucky | FINGERROLL <1> MOTION | 108 | 2500 | 7.00 | 2 | 4 | early | diferença de 1 frame; perfil balístico próprio |
| lucky | SLAM <1> ON AIR | 110 | 4700 | 4.40 | 2 | 3 | early | diferença de 1 frame; perfil balístico próprio |
| mrbig | MAXブラスターウェイブ | 110 | 3050 | 6.00 | 0 | 5 | early | override explícito 0 (super/MAX) |
| eiji | 気孔砲 | 107 | 1000 | 5.00 | 0 | 5 | early | override explícito 0 (super/MAX) |
| chunli | Kikouken (new version) | 107 | 1050 | 4.00 | 0 | 8 | early | override explícito 0 (super/MAX) |

## Anexo — lista completa por personagem

## Lista completa por personagem

### andy

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 弱飛翔拳 | 1100 | 52 | 0.00 | 26 | 4 | ok |
| 強飛翔拳 | 1110 | 53 | 0.00 | 28 | 5 | ok |
| 弱飛翔拳(裏) | 1150 | 58 | 4.00 | 14 | 3 | ok |
| 強飛翔拳(裏) | 1160 | 63 | 4.00 | 14 | 3 | ok |

### athena

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| Psychic Ball Corto | 1000 | 48 | 4.00 | 20 | 5 | ok |
| Psychic Ball Largo | 1010 | 55 | 9.00 | 20 | 5 | ok |
| state 3050 | 3050 | 86 | 0.00 | 14 | 2 | late |

### benimaru

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 弱雷靱拳 | 1000 | 48 | 3.00 | 14 | 5 | ok |
| 強雷靱拳 | 1010 | 49 | 4.00 | 18 | 4 | ok |
| 弱空中雷靱拳 | 1100 | 50 | 4.00 | 16 | 2 | ok |
| 強空中雷靱拳 | 1110 | 51 | 5.00 | 20 | 2 | ok |
| 弱雷光拳 | 3000 | 85 | 4.00 | 6 | 6 | ok |
| 強雷光拳 | 3010 | 86 | 4.00 | 8 | 5 | ok |
| MAX雷光拳 | 3050 | 87 | 4.00 | 10 | 5 | ok |

### billy

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| Flaming Stick Spin light | 1800 | 64 | 4.50 | 24 | 11 | ok |
| Flaming Stick Spin long | 1850 | 66 | 7.00 | 24 | 11 | ok |
| Flaming Stick Spin MAX | 1860 | 107 | 5.50 | 11 | 11 | ok |
| ｽﾃﾀﾛ | 6000 | 110 | 7.00 | 45 | 3 | ok |

### chin

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| Zake FireBall x | 1900 | 85 | 3.00 | 9 | 1 | ok |
| Zake FireBall y | 1910 | 86 | 2.00 | 9 | 1 | ok |
| Zake FireBall Doble | 1920 | 87 | 3.00 | 12 | 1 | ok |
| Fire Zake | 1203 | 107 | 5.00 | 20 | 7 | ok |
| Fire Zake | 1300 | 108 | 5.00 | 20 | 2 | ok |
| FireBall | 2200 | 111 | 5.00 | 8 | 3 | ok |

### choi

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 灼死（MAX2） | 3500 | 88 | 11.00 | 14 | 7 | ok |

### chris

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| Light Taiyou o iru honoo | 7000 | 111 | 4.00 | 15 | 13 | ok |

### chunli

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| Kikouken | 1000 | 48 | 3.00 | 24 | 6 | ok |
| Kikou Shou | 3000 | 85 | 4.00 | 5 | 11 | ok |
| Kikouken (new version) | 1050 | 107 | 4.00 | 20 | 0 | early |

### daimon

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 玉潰し | 300 | 58 | 2.00 | 14 | 4 | ok |

### eiji

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 弱斬鉄波 | 3000 | 85 | 4.00 | 15 | 8 | ok |
| 強斬鉄波 | 3010 | 86 | 4.00 | 19 | 8 | ok |
| MAX斬鉄波 | 3020 | 87 | 17.00 | 32 | 8 | ok |
| 気孔砲 | 1000 | 107 | 5.00 | 40 | 0 | early |

### geese

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 疾風拳 | 1100 | 58 | 7.00 | 12 | 3 | ok |
| 烈風拳(表) | 1000 | 60 | 3.00 | 12 | 4 | ok |
| 烈風拳(裏) | 1050 | 62 | 5.00 | 14 | 4 | ok |
| ダブル烈風拳(表) | 1010 | 65 | 4.00 | 16 | 4 | ok |
| 弱レイジングストーム | 3000 | 85 | 0.00 | 38 | 8 | ok |
| 強レイジングストーム | 3010 | 86 | 0.00 | 38 | 8 | ok |

### heavyd

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| D・マグナム・発射 | 2105 | 87 | 4.00 | 22 | 10 | ok |
| D・マグナム・発射 | 2105 | 88 | 5.00 | 26 | 10 | ok |

### heidern

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 弱クロスカッター | 1000 | 48 | 4.00 | 14 | 5 | ok |
| 強クロスカッター | 1010 | 49 | 5.00 | 18 | 5 | ok |

### iori

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 弱百八式・闇払い | 1000 | 48 | 2.75 | 12 | 3 | ok |
| 強百八式・闇払い | 1010 | 49 | 3.75 | 16 | 3 | ok |

### joe

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 弱ハリケーンアッパー(裏) | 1050 | 60 | 4.00 | 14 | 6 | ok |
| 弱ハリケーンアッパー | 1000 | 62 | 4.00 | 14 | 6 | ok |
| 強ハリケーンアッパー | 1010 | 65 | 7.00 | 14 | 6 | ok |
| 強スクリューアッパー | 3010 | 107 | 1.25 | 14 | 5 | ok |
| 爆烈ハリケーンタイガーカカト | 3100 | 108 | 7.00 | 14 | 2 | early |

### kasumi

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 弱重ね当て | 1000 | 52 | 0.00 | 14 | 6 | ok |
| 強重ね当て | 1010 | 53 | 0.00 | 18 | 6 | ok |
| 対空重ね当て | 1500 | 56 | 0.00 | 14 | 7 | ok |
| 対空重ね当て | 1500 | 57 | 0.00 | 18 | 7 | ok |

### ken

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 弱波動拳 | 1000 | 54 | 4.00 | 14 | 3 | ok |
| 強波動拳 | 1010 | 55 | 4.00 | 14 | 3 | ok |

### kensou

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| Light Cho kyo dan | 1000 | 56 | 4.00 | 14 | 3 | ok |
| Hard Cho kyo dan | 1010 | 57 | 7.00 | 16 | 3 | ok |

### king

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| ベノムストライク  (Benom Strike) | 1000 | 48 | 4.00 | 18 | 3 | ok |
| ダブルストライク  (Outrage / Hard) | 1050 | 49 | 7.00 | 11 | 3 | ok |

### krauser

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 弱ブリッツボール・上段 | 1000 | 54 | 4.00 | 14 | 3 | ok |
| 強ブリッツボール・上段 | 1010 | 55 | 4.00 | 14 | 3 | ok |
| 弱ブリッツボール・下段 | 1050 | 56 | 4.00 | 14 | 3 | ok |
| 強ブリッツボール・下段 | 1060 | 57 | 4.00 | 14 | 3 | ok |

### kyo

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| state 1000 | 1000 | 48 | 3.00 | 14 | 4 | ok |
| 強百八式・闇払い | 1010 | 49 | 4.00 | 18 | 4 | ok |

### kyoash

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| state 1000 | 1000 | 48 | 3.00 | 14 | 4 | ok |
| 強百八式・闇払い | 1010 | 49 | 4.00 | 18 | 4 | ok |

### kyonests

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| state 1000 | 1000 | 48 | 3.00 | 14 | 4 | ok |
| 強百八式・闇払い | 1010 | 49 | 4.00 | 18 | 4 | ok |

### lucky

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| FINGERROLL <2> MOTION | 2600 | 55 | 7.00 | 22 | 2 | early |
| SHOOT <2> FADEAWAY SHOT | 2100 | 87 | 4.00 | 22 | 2 | early |
| Death Bound <1> MOTION | 2900 | 88 | 4.00 | 22 | 4 | ok |
| Death Bound <2> MOTION | 3000 | 89 | 4.00 | 22 | 4 | ok |
| FINGERROLL <1> MOTION | 2500 | 108 | 7.00 | 22 | 2 | early |
| SLAM <1> ON AIR | 4700 | 110 | 4.40 | 1 | 2 | early |
| FINGERROLL SDM <1&2> MOTION | 3100 | 111 | 5.00 | 30 | 4 | ok |

### mrbig

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 弱グランドブラスター | 1000 | 54 | 3.00 | 14 | 6 | ok |
| 強グランドブラスター | 1010 | 55 | 4.00 | 18 | 6 | ok |
| 弱ブラスターウェイブ | 3000 | 87 | 5.00 | 12 | 5 | ok |
| 強ブラスターウェイブ | 3010 | 88 | 5.00 | 16 | 5 | ok |
| MAXブラスターウェイブ | 3050 | 110 | 6.00 | 30 | 0 | early |

### omegarugal

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| ダークジェノサイド弱 | 1000 | 48 | 0.20 | 6 | 3 | ok |
| ダークジェノサイド強 | 1005 | 49 | 0.30 | 6 | 3 | ok |
| state 1040 | 1040 | 52 | 3.90 | 10 | 2 | source-out-of-anim |
| state 1045 | 1045 | 53 | 6.40 | 12 | 2 | source-out-of-anim |
| ストライカー | 2899 | 57 | 7.00 | 10 | 0 | ok |
| state 7100 | 7100 | 82 | 1.00 | 14 | 3 | ok |
| state 1050 | 1050 | 107 | 3.90 | 4 | 2 | source-out-of-anim |
| state 1055 | 1055 | 108 | 5.00 | 5 | 2 | source-out-of-anim |

### robert

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 弱龍撃拳 | 1000 | 58 | 4.00 | 18 | 3 | ok |
| 強龍撃拳 | 1010 | 59 | 6.00 | 22 | 3 | ok |
| 弱龍撃拳(裏) | 1050 | 60 | 4.00 | 14 | 5 | ok |
| 弱覇王翔吼拳 | 3000 | 109 | 4.00 | 44 | 7 | ok |
| 強覇王翔吼拳 | 3010 | 110 | 4.00 | 50 | 7 | ok |
| MAX覇王翔吼拳 | 3020 | 111 | 17.00 | 60 | 7 | ok |

### rugal

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 弱烈風拳 | 1000 | 48 | 3.00 | 16 | 2 | source-out-of-anim |
| 強烈風拳 | 1010 | 49 | 4.00 | 20 | 2 | source-out-of-anim |
| 弱グラビティスマッシュ | 1500 | 60 | 4.00 | 14 | 2 | ok |
| 空中弱グラビティスマッシュ | 1550 | 61 | 4.00 | 14 | 0 | ok |
| state 1702 | 1702 | 82 | 5.00 | 14 | 3 | ok |

### ryo

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 弱虎煌拳 | 1000 | 60 | 2.50 | 14 | 3 | ok |
| 強虎煌拳 | 1010 | 61 | 5.00 | 18 | 3 | ok |
| 虎煌撃 | 2100 | 64 | 5.00 | 13 | 6 | ok |
| 弱覇王翔吼拳 | 3000 | 85 | 4.00 | 14 | 5 | ok |
| 強覇王翔吼拳 | 3010 | 86 | 4.00 | 14 | 5 | ok |
| MAX覇王翔吼拳 | 3050 | 87 | 17.00 | 14 | 6 | ok |
| 弱虎煌拳(裏) | 1050 | 107 | 4.00 | 14 | 5 | ok |
| 弱空中虎煌拳 | 2000 | 109 | 5.00 | 14 | 3 | ok |
| 強空中虎煌拳 | 2010 | 110 | 5.00 | 14 | 3 | ok |

### ryu

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 弱灼熱波動拳 | 1300 | 48 | 3.00 | 14 | 3 | ok |
| 強灼熱波動拳 | 1310 | 49 | 4.00 | 18 | 3 | ok |
| 弱波動拳 | 1000 | 52 | 4.00 | 14 | 3 | ok |
| 強波動拳 | 1010 | 53 | 4.00 | 14 | 3 | ok |
| 弱真空波動拳 | 3000 | 85 | 5.00 | 5 | 4 | ok |
| 強真空波動拳 | 3010 | 86 | 5.00 | 5 | 4 | ok |
| MAX真空波動拳 | 3050 | 88 | 8.00 | 8 | 4 | ok |

### saisyu

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 弱百八式・闇払い | 1000 | 48 | 2.50 | 14 | 4 | ok |
| 強百八式・闇払い | 1010 | 49 | 3.50 | 18 | 4 | ok |
| 裏百八式・大蛇薙　攻撃 | 3005 | 104 | 10.00 | 40 | 6 | ok |
| 裏百八式・大蛇薙　攻撃 | 3005 | 107 | 10.00 | 48 | 6 | ok |
| MAX裏百八式・大蛇薙　攻撃 | 3055 | 108 | 10.00 | 70 | 6 | ok |

### sakura

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 弱波動拳 | 1000 | 52 | 4.00 | 14 | 4 | ok |
| 強波動拳 | 1010 | 53 | 7.00 | 18 | 4 | ok |

### shermie

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| Close Mugetsu no raiun | 7200 | 58 | 1.00 | 20 | 9 | ok |
| Light Yatanagi no muchi | 7300 | 59 | 4.00 | 12 | 14 | ok |
| DM Ankoku raikohken | 8100 | 114 | 5.00 | 25 | 5 | ok |

### takuma

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 弱虎煌拳 | 1000 | 48 | 2.50 | 16 | 3 | ok |
| 強虎煌拳 | 1010 | 49 | 3.50 | 20 | 3 | ok |
| 弱虎煌拳(裏) | 1050 | 109 | 6.00 | 14 | 6 | ok |
| 強虎煌拳(裏) | 1060 | 110 | 6.00 | 18 | 6 | ok |
| 覇王翔吼拳 | 1502 | 111 | 5.00 | 56 | 2 | ok |

### terry

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 弱パワーウェイブ(表) | 1000 | 58 | 3.00 | 22 | 6 | ok |
| 強パワーウェイブ(表) | 1010 | 59 | 4.00 | 26 | 6 | ok |
| 弱パワーウェイブ(裏) | 1050 | 60 | 4.00 | 14 | 6 | ok |
| 弱パワーゲイザー | 3000 | 85 | 0.00 | 5 | 6 | ok |
| 強パワーゲイザー | 3010 | 86 | 0.00 | 6 | 6 | ok |
| MAXパワーゲイザー | 3050 | 87 | 0.00 | 10 | 6 | ok |

### yamazaki

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| state 1215 | 1215 | 58 | 8.00 | 8 | 2 | ok |
| Lv5 | 3140 | 85 | 12.00 | 20 | 11 | ok |

### yuki

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| Yuki-Chan no Kaban no Nakami | 1000 | 48 | 4.00 | 14 | 7 | ok |
| Otome no Sakebi | 1100 | 49 | 3.50 | 12 | 2 | ok |
| EX Ai no Kusanagi Dai Koushin!! | 3350 | 89 | 11.00 | 22 | 5 | ok |

### yuri

| Golpe (CNS) | state | sid | vx px/t | dano | release | status |
|---|---:|---:|---:|---:|---:|---|
| 弱虎煌拳 | 400 | 48 | 3.00 | 14 | 3 | ok |
| 強虎煌拳 | 401 | 49 | 4.00 | 18 | 3 | ok |
| 弱砕破 | 410 | 50 | 0.00 | 14 | 8 | ok |
| 強砕破 | 411 | 51 | 0.00 | 18 | 8 | ok |
| 弱雷煌拳 | 450 | 58 | 4.00 | 12 | 2 | ok |
| 強雷煌拳 | 451 | 59 | 6.00 | 16 | 2 | ok |
| 弱覇王翔吼拳 | 500 | 85 | 5.00 | 22 | 7 | ok |
| 強覇王翔吼拳 | 501 | 87 | 6.00 | 24 | 7 | ok |
| MAX覇王翔吼拳 | 550 | 107 | 5.00 | 60 | 7 | ok |


## Notas de implementação

- `tools/calibration/projectiles.py` (`PROJECTILE_RELEASE`) guarda o frame
  de release por personagem/sid.
- `tools/build_fight.py` grava esse frame nos bits 3–7 do byte `present` do
  `ProjTab`; o motor o lê em `ProjTrySpawn` (`src/engine/fight.asm`).
- Para os seis shotos, `PROJECTILE_STARTUP_SPEEDUP` +
  `compact_projectile_startup()` reduzem o wind-up a três poses-chave e
  `remap_startup_timeline()` move as linhas de `ActTab`/`PosTab` para os
  novos índices. O frame de release e a cauda de recuperação não são
  alterados.
- Projéteis com `vx = 0.00` são intencionais (explosão de palma do Andy,
  coluna do Raging Storm, supers estacionários).
- O release configurado é limitado ao último quadro do clipe compilado
  (`ProjTab`), então um `AnimElem` que a animação não tem não deixa mais a
  super sem disparar.
- Os quatro supers Haoh Shikou Ken usam o clipe compacto do Ko'ou Ken (a
  arte grande 2070/2100 não cabe na página de 16 células/OAM). O release e o
  dano de cada variante estão em `docs/HAOH_PROJETEIS_2026-11-15.md`.
