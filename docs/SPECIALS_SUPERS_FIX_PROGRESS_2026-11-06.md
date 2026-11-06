# Correções de especiais e supers — andamento

Escopo autorizado: exemplos confirmados na auditoria funcional de 06/11.
Preservar adaptações e padrão de pad. Não gerar build nesta etapa.

## Aplicado no fonte: duração da captura em counters

Em `src/engine/fight.asm`, `AnimTick` agora mantém o último quadro das
vítimas de contra-ataque (slots 100/102), como já fazia para a vítima
de agarrão comum (76).

Antes, o fim da animação da vítima podia enviá-la ao neutro pelo caminho
genérico, sem limpar `F_GRAB`. Isso impedia `StVictimHeld` de executar
`VH_free` quando o atacante terminasse. O novo comportamento mantém a
vítima sob controle de `StVictimHeld`; a perda do vínculo segue a rotina
de soltura que limpa `F_GRAB` e `F_OWNER`.

A correção trata a causa compartilhada pelos counters de Heidern,
Takuma, Daimon, Blue Mary e Geese observados na auditoria. A confirmação
em execução depende da próxima ROM. Não há alteração de gráficos,
states adicionais, dano ou comandos neste ajuste.

## Pendente

As continuações ofensivas e os ajustes individuais de especiais/supers
do relatório ainda não foram implementados. Este registro não declara
esses golpes corrigidos, nem substitui a auditoria da ROM anterior.

Não foi feito build.
