# Stages: arte de alta definição e animações adaptadas ao SNES

Data: 17/11/2026. Status: proposta técnica; não implementada ou validada em execução.

Atualização: o [piloto da China](STAGE_CHINA_PILOTO_2026-11-17.md) foi
implementado e testado no emulador. As demais opções abaixo continuam propostas.
O [bazar](STAGE_BAZAR_PILOTO_2026-11-17.md) recebeu a mesma abordagem em seguida.

## Objetivo

Usar as artes em alta definição como fonte para cenários mais fiéis e com
animações melhores, dentro dos recursos disponíveis no SNES. O resultado
continua sendo arte adaptada à resolução, às paletas e à memória do console;
não se propõe exibir a resolução HD original durante a luta.

## Estado atual observado

- `tools/build_stages.py` converte imagens de 512×224 para BG1, com limite
  de 512 tiles estáticos 4bpp (16.384 bytes de gráficos).
- Os cenários já usam três paletas, até 45 cores visíveis e reutilização de
  padrões com espelhamento horizontal/vertical. Esses recursos não são
  melhorias futuras: já estão implementados.
- `tools/stage_requant.py` reduz a variedade de tiles para caber nesse
  orçamento. A documentação da conversão registra perda de detalhes quando
  regiões diferentes precisam compartilhar os mesmos padrões.
- `build_anims()` em `tools/build_stages.py` gera poses por reamostragem
  vertical de trechos da imagem estática. O efeito é uma oscilação simples,
  não a reprodução dos gestos originais dos personagens de fundo.
- As poses ficam residentes num pool compartilhado a partir do tile 704,
  com limite configurado de 160 tiles. O conversor reúne clips de vários
  cenários; a troca de pose usa alterações no tilemap.
- O relatório de 13/11 registra ocupação de 120 dos 160 tiles desse pool.
  Essa contagem deve ser reconfirmada no build ao iniciar a implementação.

Ver [conversão com três paletas e espelhamento](STAGES_3PAL_FLIP_2026-11-13.md).
O README antigo em `assets/stages/stages_png_snes/animations/` contém propostas
anteriores; para o comportamento implementado, conferir o conversor e
`src/engine/fight.asm`.

## Melhorias propostas

### Conversão com prioridades por região

Partir das fontes HD e preservar com maior prioridade rostos, placas,
contornos e construções características. Aceitar maior simplificação em
céu, chão e texturas repetidas. A intenção é concentrar os tiles nos detalhes
que mais contribuem para reconhecer o cenário, preservando os retoques já
aprovados nas versões SNES.

### Poses reais nas animações principais

Extrair poses dos assets originais, quando disponíveis, ou redesenhar poses
adaptadas para torcida, bandeiras e outros elementos relevantes. Como ponto
inicial de experimentação, testar 3–6 poses com 6–12 atualizações por segundo,
ajustando a cadência por elemento. Esses números são hipóteses de trabalho,
não limites do hardware nem desempenho já demonstrado. A cadência do cenário
deve ser independente da atualização da luta.

### Pool de animação por cenário

Estudar o carregamento apenas das poses do cenário ativo no espaço reservado
às animações. Isso pode permitir mais poses ou elementos por cenário sem
aumentar a reserva total de VRAM. Exige adaptar os índices, descritores e o
carregamento; o ganho depende da quantidade de tiles exclusivos de cada clip.

### Atualizações pequenas e escalonadas

Manter a arte estática e atualizar somente as regiões animadas. Preferir a
troca de entradas do tilemap quando as poses couberem residentes em VRAM.
Se for necessário transferir novos gráficos, enviar somente os tiles
alterados, com orçamento medido por VBlank e atualizações distribuídas entre
frames. Essa alternativa precisa ser avaliada junto com as transferências
dos lutadores e efeitos; não há orçamento livre confirmado nesta proposta.

### Mais de 512 tiles estáticos, se necessário

O limite de 512 tiles pertence à organização atual do projeto. O tilemap
convencional do SNES possui índice de 10 bits, permitindo referenciar até
1.024 tiles relativos à base de gráficos. Isso não significa que exista
memória livre para todos eles nesta engine.

Antes de aumentar `MAX_TILES`, mapear as faixas ocupadas por gráficos,
tilemaps, fontes, HUD, animações e sprites durante a luta. Reorganizar essas
faixas exige verificar colisões e custos de carregamento. Aumentar somente
a constante do conversor não constitui uma solução segura.

Referência: [SNESdev — Tilemaps](https://snes.nesdev.org/wiki/Tilemaps).

## Piloto recomendado e critérios de avaliação

1. Escolher um cenário representativo e guardar imagens e medições da versão
   atual para comparação.
2. Manter inicialmente os 512 tiles estáticos e as três paletas, aplicando
   prioridades visuais à conversão da fonte HD.
3. Substituir a oscilação de um elemento importante por poses reais e avaliar
   o pool por cenário.
4. Validar a conversão com `tools/verify_stage_export.py` e conferir os
   limites de tiles e as faixas efetivamente utilizadas em VRAM.
5. Comparar capturas com a mesma câmera e avaliar detalhes, coerência das
   cores, repetição de padrões e naturalidade das poses.
6. Executar uma luta completa, incluindo deslocamento da câmera, golpes e
   efeitos, verificando corrupção gráfica, HUD, estabilidade da cadência e
   orçamento de transferências. Validar em hardware quando disponível.
7. Só depois decidir se o ganho justifica ampliar o orçamento estático e
   aplicar o processo aos demais cenários.

Há oportunidades concretas de melhoria no processo atual, especialmente nas
poses e na distribuição dos tiles. A qualidade alcançável e o custo de
execução ainda dependem do piloto; esta proposta não garante um ganho
quantitativo nem estabelece um novo layout de VRAM.
