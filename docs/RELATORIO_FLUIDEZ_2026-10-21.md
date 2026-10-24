# Fluidez e glitches — KOF98 SNES

Auditoria de 21/10/2026 do código de trabalho, incluindo alterações locais existentes. Nenhuma mudança no motor ou nos assets foi feita por esta auditoria.

## Diagnóstico

A prioridade é reduzir e organizar o trabalho de apresentação e retirar leituras síncronas do caminho dos golpes. Calibrar dano, duração e paleta ajuda na fidelidade, mas não resolve sozinho atraso de upload, espera de áudio, descarte de projéteis ou falta de espaço para sprites.

Há três fenômenos diferentes a medir: parada da simulação, repetição da pose enquanto a simulação avança e congelamento intencional de impacto/super. Não é adequado remover `pausecnt` para eliminar as “pausinhas”: ele também implementa hitstop e SuperPause legítimos.

## 1. P0 — Orçamento único para apresentação

Evidência: `FightPresent` em `src/engine/fight.asm:13005` ativa forced blank e executa efeitos, OAM, os dois uploads de lutadores, HUD e animação de cenário antes de reativar a imagem. `DMACHUNK=1280` limita cada lutador, não o conjunto. `FxPrepareBoth` pode fazer dois uploads de 2.048 bytes; `FlushHud` envia 2.048 bytes. `FightTick` marca `huddirty` ao final de cada tick normal.

Somando apenas esses caminhos, a apresentação pode transferir **9.248 bytes**: 2×1.280 de lutadores + 2×2.048 de efeitos + 2.048 de HUD + 544 de OAM. Sem os dois uploads de efeitos, são 5.152 bytes. São somas estáticas de caminhos possíveis; não são medições de duração nem prova de que todos coincidem em cada frame. Preparação, seeks e cenário acrescentam trabalho.

Otimizar: orçamento global em tempo/ciclos, incluindo setup e seeks; enviar apenas regiões alteradas do HUD; enviar somente os tiles usados pelos efeitos; preparar descritores fora da janela de apresentação; adiar trabalho visual de baixa prioridade. Revisar se o ISR da biblioteca já envia OAM para evitar duplicação. Preservar o commit consistente entre tiles e OAM.

Validar: registrar início/fim da apresentação por scanline, bytes por classe e prazo excedido. Comparar dois especiais simultâneos, dois projéteis, impacto e cenário animado. Não aumentar `DMACHUNK` antes dessa medição nem depender de prolongar forced blank para acomodar trabalho.

## 2. P0 — Vozes e acesso MSU sem bloquear golpes

Evidência: `VoicePlay` (`fight.asm:13615`) faz seek com até `$FFFF` tentativas e copia cada byte MSU→`VOICE_BUF` em um loop antes de retornar. O gerador limita cada voz a 6.000 amostras PCM de 4 kHz, antes de codificar BRR. Terry tem exceção de voz residente na ROM; os demais usam MSU quando há tabela de voz. Portanto, até um personagem com gráficos na ROM pode passar por leitura MSU ao falar.

Otimizar: pré-carregar as vozes frequentes dos dois personagens durante a entrada da luta; manter impactos essenciais residentes; carregar o restante em etapas limitadas por frame, com uma fila de áudio e política de prioridade. A fala deve ser agendada sem impedir o tick. Centralizar a propriedade do único cursor MSU entre gráficos e vozes. Garantir que um buffer não seja sobrescrito enquanto ainda é consumido pelo envio à APU; o código usa um `VOICE_BUF` compartilhado, cuja vida útil precisa ser verificada.

Validar: comparar exatamente o mesmo replay com e sem vozes, sobretudo duas falas no mesmo frame. Medir também `spcProcess`/envio à APU: mover BRR para ROM elimina a leitura MSU, mas não demonstra que todo custo de áudio desapareceu.

## 3. P0 — Streaming previsível sem alterar timing dos golpes

Evidência: uma pose de 3.072 bytes exige pelo menos três apresentações frias a 1.280 bytes por passagem. `ASF_q_new` protege o upload em andamento contra substituição, correção que deve ser preservada. Entretanto, a animação segue avançando: `AnimSetFrame` atualiza `F_ATKBOX`/`F_HURTBOX` enquanto offsets/tiles aguardam commit. Pode haver um golpe ativo antes da pose correspondente aparecer.

Otimizar: prefetch dos próximos sprites de animações previsíveis; cache por identidade do conteúdo; reaproveitar tiles entre poses; empacotar apenas alterações onde houver ganho medido. Priorizar primeiro frame ativo, defesa e reação a hit. Pré-carregar estados frequentes dos dois lutadores na entrada da luta, respeitando o mapa de WRAM/VRAM. Comandos e branches exigem fallback explícito: duas páginas de ping-pong não constituem cache arbitrário para todos os estados.

Não aumentar indiscriminadamente os ticks AIR para “caber” no upload: isso muda startup, recuperação e cancelamentos. Definir e medir o atraso entre frame lógico e pose apresentada; não congelar toda a simulação à espera do streaming.

## 4. P0 — Timeout MSU não pode publicar dados incompletos

Evidência: em `SD_msu` (`fight.asm:14138`), esgotar a espera faz `jmp SD_advance` mesmo sem DMA. O cursor avança e pode chegar a `SD_commit`, tornando visível uma página que não foi completamente preenchida.

Corrigir: timeout deve manter cursor e página visível, registrar falha e permitir nova tentativa com limite de tempo por frame. Só publicar a página depois de todos os blocos realmente transferidos. Como a rotina roda sob forced blank, a espera de `$FFFF` tentativas também merece substituição por protocolo que não retenha a apresentação.

Validar com MSU ausente, arquivo incorreto/truncado e atraso de leitura controlado. Essa falha existe no fluxo do código; sua frequência em uso normal não foi medida aqui.

## 5. P1 — OAM, rastros e prioridade visual

Evidência: o conversor aceita até 64 células por pose. Dois personagens podem consumir o total de 128 entradas antes dos rastros e efeitos. `BuildOam` desenha efeitos, depois rastros/P1, depois rastros/P2; `DF_cell` tem guarda de capacidade, mas isso pode descartar o fim do P2. Não encontrei controle de pressão por scanline no motor inspecionado. A guarda global evita escrita fora do shadow, mas não garante desenho completo.

Otimizar: reservar espaço para ambos os corpos antes dos rastros; cortar células fora da tela; reduzir ghosts e efeitos quando a linha estiver carregada; relatar no build a ocupação por linha para pares de poses. Inspecionar os flags de overflow da PPU no teste em emulador compatível.

`GhostPush` guarda ponteiro de meta e página, sem copiar os tiles. Como as páginas são reutilizadas pelo ping-pong, verificar se um rastro ainda vivo referencia tiles já substituídos. Usar geração da página/invalidação ou representação que preserve os gráficos enquanto o rastro estiver vivo. É risco inferido do modelo de armazenamento, ainda sem reprodução visual nesta auditoria.

## 6. P1 — Projétil não pode perder espaço para faísca

Evidência: `ProjSpawn` (`fight.asm:11814`) procura dois slots de `SPARKS`; se ambos estiverem ocupados, retorna e descarta o spawn. `ProjTrySpawn` marca `F_PROJDONE` antes da chamada. Assim, uma tentativa descartada fica consumida. `ProjTrySpawn` também retorna quando `vx=0`, impedindo representar um projétil parado por esse caminho.

Corrigir: separar objetos de gameplay dos efeitos cosméticos, ou permitir que um projétil substitua efeito descartável; retornar sucesso do spawn antes de consumir o evento. Usar flag de existência independente da velocidade. Limitar quantidade de projéteis por regra explícita do golpe. Para o renderer, incluir banco/identidade completa na chave do cache de efeitos: hoje `FX_CACHE` compara só a palavra do ponteiro, e é preciso verificar se o linker garante unicidade entre bancos.

Validar dois projéteis simultâneos, impacto no frame de lançamento, reflexo, ataque estacionário e expiração. Distinguir limitação deliberada do kit de descarte acidental.

## 7. P1 — Arte e paleta: reduzir custo sem cortar o personagem

O conversor já usa paleta global de 15 cores, deduplicação de células e divisão 8×8/16×16 para caber na página de 96 tiles. Porém, quando não cabe, pode suprimir quadrantes; `max_dma=2560` em Rugal/Omega também remove células cujo intervalo excede o limite. Isso pode explicar partes ausentes mesmo sem corrupção de VRAM.

Otimizar: gerar relatório de pixels/células removidos por pose e rejeitar perdas em partes essenciais; aperfeiçoar recorte, alinhamento e deduplicação antes de reduzir detalhe. Não impor o mesmo corte de bytes a todos os chars. Comparar poses do SFF com render SNES, incluindo extremos de especiais e supers.

Athena já tem correção e teste de banco de paleta; não atribuir todo glitch dela à paleta. Estender verificação a P1/P2, espelhamento, PalFX, rastros, projéteis e troca de membro. Manter índices/transparência coerentes no build e enviar CGRAM apenas quando houver alteração necessária. As caixas AIR são agregadas em um retângulo por tipo: é uma aproximação de colisão, não um ganho de fluidez a ser confundido com fidelidade.

## 8. P0 de validação — Confiar nos medidores e no build

O catálogo `tools/calibration/catalog.py:192` ainda usa **192 bytes para MSU e 1.536 para ROM**; ambos os caminhos do motor atual usam 1.280. Também há comentário antigo de 1.536 bytes junto ao DMA MSU. `tools/probe_freeze.py:19` chama o offset 26 de `p1psprid`, mas o ABI atual define `F_PSPRID=47` e `F_HITDONE=26`. Esse probe pode interpretar dano/flags como ID de sprite.

Correção recomendada: gerar constantes de ABI e orçamento para ASM/Python a partir da mesma definição; associar cada resultado a hashes de ROM, MSU, código/configuração e core; publicar o bundle completo de forma atômica. Evitar usar relatório anterior como certificado da ROM nova.

O snapshot `release-source-restored`, de 20/10, contém 48 personagens, 7 erros estáticos e 34 avisos de HitDef sem caixas AIR. Seus 21.697 registros de animação, contando aliases/slots repetidos, dão 3.633 registros cuja duração é menor que o limite frio recalculado a 1.280 bytes. **Isso não significa 3.633 engasgos nem mede FPS**: repetição, cache, transições e concorrência mudam o resultado. É triagem histórica para selecionar replays.

Os sete erros desse snapshot são: referências de sprite em Kyo SIDs 85/86, Shingo 91 e Chizuru 49; projéteis parados de Yuri 50/51; projétil não ligado de Athena 86. A rejeição de `vx=0` ainda está presente no código atual. Os demais casos precisam de recatálogo atualizado e revisão de alcançabilidade/intencionalidade antes de concluir que são bugs atuais. Não confundir ausência de candidato antiaéreo com defeito obrigatório do kit.

## Validação realizada nesta auditoria

- `python3 -m unittest discover -s tools/tests -v`: 86 testes executados em 65,279 s, 8 erros reportados e 1 ignorado. Os oito erros são `FileNotFoundError` para `build/gen_fight/kyo_spr.inc` e/ou `iori_spr.inc`. Log completo: `/tmp/kof98-audit-unit.log`.
- O teste `test_super_stage_vram_headless.py` foi iniciado, mas não concluiu e foi interrompido. Não há resultado aprovado ou diagnóstico de causa para ele nesta auditoria.
- O JSON salvo `headless-final.json` aprova 16 normais de quatro personagens; não cobre todos os golpes de todo o roster. O `roster-runtime.json` de `release-source-restored` lista 48 IDs esperados, mas contém apenas um confronto Kyo/Iori.
- ROM examinada: SHA-256 `59823cb7f6e84ff2b4ea90fc86a6ba641a37960ed311a0aa028d3f333e5486d3`. MSU: `c154029d8f9f2fff7fb552de7a5832b53b3ab6c776ed1d988a7f4235f014153c`. São diferentes dos hashes do snapshot anterior.

## Ordem de execução e critério de conclusão

1. Completar/reconciliar os gerados, repetir a suíte e corrigir ABI/orçamentos dos probes. Criar telemetria de tick, apresentação, espera de áudio, idade de upload, falha de MSU e descarte de objeto.
2. Retirar a cópia síncrona de voz do caminho do golpe e corrigir timeout/commit do MSU.
3. Implantar HUD parcial, orçamento global e uploads menores de efeitos; então medir a margem disponível para prefetch/cache de sprites.
4. Garantir prioridade dos corpos e projéteis; validar ghosts e perda de arte no conversor.
5. Executar matriz por personagem e pelos dois lados: movimento, defesa, hit, todos os normais, especiais, supers, follow-ups, variações de botão, cancelamentos e troca de membro. Combinar ataques pesados com dois projéteis, vozes e cenário animado. Começar por ROM×ROM, ROM×MSU, MSU×MSU e mirror matches; ampliar combinações onde a telemetria indicar pressão.

Critérios propostos: nenhum deadline perdido na matriz determinística; nenhum commit de upload incompleto; nenhum projétil de gameplay descartado por efeito; nenhum overflow visual não tratado nos cenários suportados; timing lógico preservado; atraso visual documentado e sem pose antiga no instante ativo; sessões longas sem stalls inesperados. Comparar replay em Snes9x e Mesen/bsnes, e validar no hardware/cartucho MSU de destino. FPS nominal do emulador e `framecnt` isolado não certificam fluidez.

O maior retorno esperado está em **HUD parcial + apresentação com orçamento global + voz assíncrona/prefetch**, seguido de cache de sprites. O efeito quantitativo de cada mudança ainda precisa de baseline de tempo; esta auditoria não atribui percentuais de ganho sem medi-los.
