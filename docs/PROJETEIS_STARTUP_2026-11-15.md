# Projéteis dos shotos: janela de disparo e wind-up (15/11/2026)

## Problema

O motor dispara o projétil no frame configurado em `ProjTab`. Sem uma
configuração explícita ele usava o **terceiro frame** da animação de lançamento.
Nas animações importadas de Ryu, Ken, Ryo, Robert, Takuma e Yuri os braços só
ficam estendidos vários frames depois disso, então o Hadouken/Ko'ou Ken saía
durante o wind-up.

Só atrasar o disparo para o frame de braço estendido não bastava: o `.air`
original leva 10-12 ticks até essa pose e, como os cels grandes exigem dois
ticks de upload cada, o golpe ficaria visivelmente mais lento.

## O que foi feito

1. **Release alinhado à origem.** `PROJECTILE_RELEASE` passou a apontar para o
   frame em que o CNS original cria o projétil (AnimElem 5 de Ryu/Ken, 4/5 de
   Ryo, 6 de Robert/Takuma, 7 de Yuri). O valor é gravado nos bits 3-7 do byte
   `present` do `ProjTab`; ver `tools/audit_projectile_release.py`.
2. **Wind-up compactado.** `PROJECTILE_STARTUP_SPEEDUP` em
   `tools/build_fight.py` lista os sids dos shotos. Antes do frame de release,
   `compact_projectile_startup()` mantém no máximo três poses-chave (a
   primeira, uma intermediária e a pose imediatamente anterior ao disparo).
   As poses restantes continuam com seu tempo de upload completo e o frame de
   release + cauda de recuperação não são alterados.
3. **Timeline remapeada.** `remap_startup_timeline()` move as linhas de
   `ActTab`/`PosTab` dos frames antigos para os novos índices. `PosAdd`
   descartado é somado ao próximo frame mantido, então o deslocamento para
   frente do golpe não se perde.
4. **Duração preservada.** Takuma e Yuri receberam `PROJECTILE_RECOVERY`
   menor (20/22 ticks) para compensar os dois ticks extras até o release. A
   velocidade, o dano e a lifetime dos projéteis não mudaram.

## Resultado

Todos os seis personagens soltam o projétil no frame compilado **3**, que é a
pose de braços estendidos:

| Personagem | Golpes | Release antigo | Release novo | Início do golpe (ticks) |
|---|---|---|---:|---:|
| Ryu | Hadouken / Shakunetsu | 3º frame | 3 | 6 |
| Ken | Hadouken | 3º frame | 3 | 6 |
| Ryo | Ko'ou Ken fraco/forte | 3º frame | 3 | 6 |
| Robert | Ryuu Geki Ken | 3º frame | 3 | 6 |
| Takuma | Ko'ou Ken fraco/forte | 3º frame | 3 | 6 |
| Yuri | Ko'ou Ken fraco/forte | 3º frame | 3 | 6 |

A duração total do especial fica igual ou menor que a anterior; Ken, por
exemplo, cai de 11 para 6 ticks até o disparo. Takuma e Yuri disparam dois
ticks depois do antigo default (4 -> 6), mas a recuperação encurtada mantém a
duração total do golpe.

## Como reproduzir

```sh
python3 tools/build_fight.py
PVSNESLIB_HOME=/caminho/pvsneslib make -f Makefile.pvsnes
python3 tools/audit_projectile_release.py ryu ken ryo robert takuma yuri
python3 tools/test_projectile_speed_combo_headless.py
```
