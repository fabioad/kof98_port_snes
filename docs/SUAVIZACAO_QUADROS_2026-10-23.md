# Suavização de quadros — KOF98 SNES (23/10/2026)

## Causa

O `tools/trim_air.py` reduz cada `.air` a um orçamento de 655 elementos. Com
as mecânicas novas (arremessos, counters, supers) o número de ações
referenciadas cresceu; quando o orçamento não fechava, o tool subia o nível de
corte até 1.0 e dobrava os ticks dos quadros removidos no vizinho. O resultado
era um teleporte: o pulo do Kyo, por exemplo, tinha virado **2 poses**, com a
primeira presa por 26 ticks.

Isso não é limite de hardware: os quadros existem no `.air.orig` e o SNES
aceita até 254 poses por animação (o contador de frames é um byte; 255 é
"segurar para sempre").

## O que foi feito

1. **`tools/smooth_air.py`** (novo) devolve os quadros intermediários do
   `.air.orig`:
   - só restaura ações que o build realmente compila (`cfg["anims"]`);
   - só restaura quando a sequência atual é uma subsequência da original, o
     que preserva edições manuais (ex.: entrada da Sakura);
   - mantém os índices originais dos elementos, então `AnimElem`/`Clsn` do
     `.cns` continuam apontando para a mesma pose;
   - nunca passa de 254 elementos por ação;
   - respeita o espaço de CHR dos personagens em ROM e o orçamento dos
     personagens em MSU;
   - atualiza o hash do `.air` nos perfis de calibração (os perfis não têm
     correções indexadas por elemento, então a mudança é só visual).
2. **Prioridade**: pulo → andar/correr → agachar/levantar → ataques. Assim o
   espaço disponível vai primeiro para o que o jogador vê o tempo todo.
3. **`tools/build_fight.py`**: o tween sintético deixou de ser um por golpe.
   Agora só entra em clipes com **menos de 5 poses reais**. Clipes com 2 poses
   recebem dois dissolves (1/3 e 2/3) e clipes com 3–4 recebem um. O limite de
   upload (1280 bytes/vblank), 64 células OAM e 254 frames por animação
   continuam valendo.
4. **Personagens em ROM** (Kyo, Iori, Shingo, Terry, Benimaru, Daimon,
   Omega Rugal) usam o espaço de CHR que antes era gasto com dissolves para
   guardar os quadros reais. Por isso o tween sintético fica desligado neles
   (exceto Omega Rugal, que não tem `.air.orig`).
5. **`tools/trim_air.py`**: ações de movimento (0, 10–12, 20/21, 40–43, 47,
   100/105, 130–132, 150–152, 190, 195, 5120, 5300) nunca são afinadas, e
   nenhuma ação com 4+ poses pode cair abaixo de 4. Isso evita que um novo
   `trim_air --batch` estrague a suavização.
6. **Metas separados** de Vice, Mature, Leona e Ralf: o `SprData` desses
   quatro personagens antigos foi para um banco próprio (`CH_MBANK`), como já
   acontecia com os personagens novos. Sem isso os quadros restaurados
   estouravam as janelas fixas do `fight.asm` (Vice em `$9000`–`$FFFF`,
   Mature no fim do banco 55, etc.).

## Resultado

- **+1.456 quadros compilados** somando todos os personagens.
- **Todos os 50 personagens** têm pulo com **4 ou mais poses** no AnimTab
  gerado. Antes, 22 personagens tinham 2–3 poses.
- Andar: mínimo passou de **2 para 5** poses em todos.
- Kyo: pulo `2 → 7`; Iori `2 → 9`; Terry/Shingo/Benimaru/Daimon `2 → 7`;
  Mature `3 → 9`; Leona `9 → 15`; Ryu/Ken `2 → 4` (2 poses + 2 dissolves).
- ROM: 1.44 MiB livres de 8 MiB (`verify pvsnes: OK`).
- MSU: 28.999.680 bytes (43 personagens streamados).
- 139 testes unitários (incluindo 4 de suavização e 4 de apresentação): OK.
- `test_start_transition.py`: PASS single/versus.
- `test_roster.py`: 24/26 confrontos OK (todos os 24 confrontos visíveis,
  incluindo Mature×Vice e Benimaru×Daimon com metas separados). As duas falhas
  são os Kyo oculto × Kyo oculto, em que o harness de seleção repete o mesmo
  personagem nos dois lados.

## Como reproduzir

```sh
python3 tools/smooth_air.py --apply     # restaura os quadros dos .air.orig
python3 tools/build_fight.py            # gera CHR/metas/AnimTab/MSU
PVSNESLIB_HOME=/caminho/pvsneslib make -f Makefile.pvsnes
make -f Makefile.pvsnes verify
python3 -m unittest discover -s tools/tests -v
```

O `smooth_air.py` é incremental: rodar de novo com os `.air` já restaurados
não duplica quadros, apenas tenta adicionar os que ainda faltam dentro do
orçamento.
