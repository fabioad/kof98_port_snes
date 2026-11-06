# Normais de perto e descida do pulo da Yuri

## Yuri

O cel defeituoso 40,5 foi substituído pelo cel limpo 40,4 em **todas as 19
ações** que o usavam, não apenas nos três saltos. Tempos, loop, offsets AIR,
colisões e física do salto permanecem iguais.

Os tweens sintéticos da Yuri apareciam como ruído azul em alguns quadros
(landing, get-up, dash para trás e fatias de especiais). Todos os sids que
recebiam dissolve foram desligados em `tween_skip_sids` (17, 18, 46, 61, 62,
além dos 6/20 já existentes). O build não gera mais nenhum tween cel para ela;
os clips usam diretamente as poses de origem. O dash para trás voltou às
quatro poses e termina limpo.

Uma varredura nos cels de corpo (grupos < 1000) encontrou 123 pixels
isolados em 101 sprites — inclusive o último quadro do dash (105,2). Esses
pixels são removidos antes da geração de CHR/meta. Grupos de efeito (>= 1000)
ficam intactos para não apagar partículas intencionais.

## Normais por proximidade

Os quatro botões normais em pé selecionam um perfil de perto quando os
lutadores estão no chão, a até 40 pixels entre as origens. A seleção é
fixada na entrada do golpe, para não mudar quando há empurrão. P1, P2 e
CPU passam pelo mesmo caminho. Agarrões e comandos mantêm sua prioridade.

`tools/close_normals.py` mapeia os Statedefs de perto dos pacotes de origem;
por exemplo, Terry usa 205/215/235/245, King 200/220/210/230 e Billy
201/221/211/231. Botões sem versão separada na origem continuam com seu
normal existente. Alternativas de outros modos/anim e HitDefs sem dano não
acrescentam contatos. Controladores duplicados são deduplicados pelo elemento.

São reutilizados os estados 5–8, as animações, as caixas e as páginas CHR
existentes. Os perfis alteram dano, hitstun, empurrão, defesa e hitstop.
Os valores de dano conservam a normalização do personagem e o empurrão é
limitado ao campo de jogo do SNES.

Quando há múltiplos contatos, a pose ativa é mantida brevemente e o latch
é rearmado depois de quatro ticks sem pausa. Há um limite de três contatos.
O empurrão intermediário é suprimido e o último contato usa a velocidade
normal do perfil. Nessa aproximação, esses normais mantêm a vítima em hitstun,
sem o knockdown da origem. O HP de Terry tem dois contatos de 18 de dano
antes das correções de defesa/combo do jogo.

A implementação acrescenta perfis compactos de 32 bytes por botão, uma
consulta direta por campo e 12 bytes de estado WRAM para os dois lados.
Não acrescenta CHR, sprites, canais de DMA nem leituras ao arquivo MSU.
O helper `HitCheck` e o acesso aos dados ficam no espaço reservado abaixo
 de $0D00 do mesmo banco de CPU; não há expansão da janela de luta de 32 KiB.

## Saída do golpe e empurrão

`CloseNormalTickFar` limpa o perfil já no primeiro tick fora dos states 5–8,
e `CloseNormalEnterFar` também o zera em toda troca de state. O teste espera
um tick extra ao sair do normal antes de exigir `CN_PROFILE = 0`, cobrindo a
ordem de `AnimTick`/`TickFighter` sem deixar perfil residual.

Nos dois contatos do HP de perto do Terry, o primeiro acerto mantém a vítima
no lugar e o segundo aplica o empurrão do perfil (0,0 → 1,5 px/tick no P1 e
0,0 → −1,5 px/tick no P2, conforme o lado). O ajuste de `CloseNormalPtrFar`
compara o offset baixo do campo (`$080C`/`$0614`) e usa uma área de zeros
com padding suficiente para o stride dos campos de velocidade.

## Verificação

- `tools/tests/test_close_normals.py`: contagem dos contatos, exclusão de
  animação alternativa e consistência dos perfis do elenco.
- `tools/test_close_normals_headless.py`: **400** seleções perto/longe
  passaram; recuperação, limpeza do perfil e contatos reais do HP de Terry
  nos dois lados. P1/P2 perto: 18+18 HP, sem empurrão no primeiro contato e
  empurrão no último; longe: 32 HP.
- `tools/test_yuri_jump_descent_headless.py`: clips gerados usam o cel limpo;
  saltos neutro, para frente e para trás chegam ao chão no jogo. Capturas
  em `build/yuri_jump_descent/`.
- Suíte completa: 311 testes unitários passaram.

Logs desta atividade: `build/close_normals_*.log` e `build/yuri_jump_descent.log`.
A ROM e o MSU devem ser atualizados juntos após a regeneração dos assets.
