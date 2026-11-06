# Música e luta travadas após uma pausa longa

A última sessão automática do Mesen foi copiada para diagnóstico, sem alterar
o arquivo original. Ela mostrava TEAM PLAY, Daimon contra M. Bison, cenário
6 (Spain/Fairy), na troca para a música de vitória. A CPU estava no loop de
`SpcFlushSafe` e o SPC havia executado STOP fora do driver.

## Causa

O módulo aprovado `assets/audio/ffg/stg6.it` tem 71 padrões. O formato usado
pelo driver SNESMOD só reserva 64 ponteiros: `MOD_PTABLE_L=$E8` e
`MOD_PTABLE_H=$128`, com o próximo campo em `$168`. O conversor informa
`Patterns: [71/64]`, mas não rejeita a conversão. A validação do projeto
verificava apenas o tamanho em ARAM.

Ao chegar à ordem 64 (o 65º padrão), a leitura usa outro campo como ponteiro.
Um comando inválido acaba indexando a tabela de saltos fora dos limites;
o SPC sai do driver e a música para. Ao carregar outra música, a CPU fica
esperando um ACK que o SPC já não pode fornecer.

Reprodução no Mesen, ROM anterior: o sequenciador chega a `$40:01` aos
19.800 frames de pausa (~5min30s) e deixa de avançar. O teste de cinco
minutos anterior encerrava antes desse ponto. O defeito também pode ocorrer
com a música tocando por esse tempo fora da pausa.

## Correção

- `tools/it_pattern_limit.py` junta pares de padrões lineares em padrões de
  até 128 linhas, regravando os caches de máscaras corretamente. Fairy passa
  de 71 para 36 padrões. As 4.517 linhas de eventos musicais continuam iguais,
  assim como andamento, instrumentos, amostras e dados PCM.
- A instalação do pacote aprovado aplica essa transformação à cópia gerada.
  Os arquivos de origem aprovados e seus hashes permanecem intactos. As outras
  16 músicas do pacote são instaladas byte a byte como antes.
- A validação anterior ao `smconv` agora rejeita módulos com mais de 64 padrões.
  As dependências do Makefile incluem a nova transformação.
- A representação compacta mantém o módulo em 33.309 bytes de ARAM, abaixo
  dos 33.614 bytes anteriores; não se troca o limite de padrões por excesso
  de memória de áudio.

## Verificação

- `tools/tests/test_it_pattern_limit.py`: comparação de todas as linhas de
  Fairy, cabeçalhos e PCM intactos, caches de máscaras, instalação repetida,
  outras músicas inalteradas e rejeição antes de chamar o conversor.
- `tools/test_fight_pause_soak_headless.py --minutes 7 --stages 6`: pausa
  prolongada, avanço real de linha/ordem do SPC, áudio, luta congelada durante
  a pausa e movimento do personagem após continuar.
- `tools/test_mesen_pause_soak.lua`: entrada por START, contagem independente
  de frames da CPU e linha/ordem do SPC, retomada e movimento. O teste usa uma
  cópia da ROM sem `.sym` adjacente para evitar o problema de importação de
  símbolos do Mesen e lê os símbolos explicitamente.
- Logs de diagnóstico e regressão em `build/mesen_fairy_*.log`,
  `build/pause_fairy_snes9x_*.log` e `build/pause_music_unit_tests.log`.

Resultado final: Mesen e Snes9x passaram sete minutos em Fairy, com volta da
música ao início e movimento após continuar. As 17 músicas passaram pelo
sound test; 308 testes unitários passaram. ROM verificada, checksum `$703B`.
