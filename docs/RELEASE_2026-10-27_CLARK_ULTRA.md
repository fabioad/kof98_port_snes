# Release 27/10/2026 — Ultra Argentine completo (Clark)

## Destaques

- **Ultra Argentine do Clark completo**: o super (HCBHCB + X ou Y) agora
  executa o arremesso inteiro — agarrão, duas elevações, dois impactos e
  arremesso final — com 4 golpes e **105 de 200 de dano**, em vez de parar
  na primeira pose com ~1 de dano.
- **Comando forte corrigido**: `HCBHCB + Y` entrava no estado de
  continuação do arremesso (3010) em vez do iniciador (3000).
- **Fim do bind de 254 frames**: uma janela de `TargetBind` prendia a
  vítima a 80 px do chão por até 254 frames (4 segundos).
- **Janelas de arremesso corrigidas no roster**: Chang, Heidern, Joe,
  Terry, Mary e o Mount do Clark não ficam mais com a vítima colada em um
  deslocamento errado durante o golpe.

## Correções técnicas

- O compilador de `TargetBind` agora entende `AnimElemTime(N) = 0`,
  `AnimElemTime (N)` com espaço, `AnimElemTime(N) < M` e
  `AnimElemNo(0) = N`.
- As tabelas de bind seguem a regra do MUGEN: todos os `TargetBind` que
  casam são aplicados e **o último vence**. Antes o motor usava a primeira
  janela, então uma linha abrangente escondia todas as específicas.
- A cadeia 3010-3016 usa os slots 109-111 (grab importado) e 103-106
  (follow-ups livres de reversal). As vítimas 3020-3026 ficam no slot
  genérico `S_VHELD` e são reposicionadas pelas janelas de bind.
- `StateRet` passou a chamar `ThrowBind`: especiais importados que seguram
  a vítima (Clark e Mary) reposicionam o corpo preso a cada tick.
- O Ultra Argentine funciona com o Clark em P1 ou P2, no canto, contra
  quem está na guarda, com whiff (sem prender ninguém) e mesmo quando o
  golpe nocauteia no meio da sequência.

## Já incluído nas versões anteriores

- Reversal/counter-hit do Yamazaki com dano correto.
- Projétil do Andy (QCB+P) visível e acertando.
- Bola do Lucky saindo da mão em diagonal (Death Bound).
- Ko'ou Ken da Yuri cerca de 2× maior.
- Arremessos normais funcionando nos 50 personagens.
- Correção do travamento do guard-cancel/rolamento (Clark × Ralf).
- CHR e vozes via MSU alinhados a setor (SD2SNES), com handshake de voz.

## Instalação

Copie **kof98-snes.sfc** E **kof98-snes.msu** deste pacote para a mesma
pasta do SD, substituindo os dois arquivos.

- ROM checksum: `$293F`
- SHA-256 ROM: `e64cc1cb0259afd1870d59e36321adeef2254fb4f087a7a79268c63688b6cfb1`
- SHA-256 MSU: `bf86b4d589b06dee7959a20d6684dcee06be7c38f5785dbc988d6b3bc0d24bd1`

## Validação

- 187 testes unitários.
- 50/50 arremessos normais.
- Guard-cancel Clark × Ralf e Clark × Vice.
- Counter-grabs, reversal do Yamazaki, vozes MSU alinhadas.
- 2.400 páginas de CHR MSU conferidas byte a byte (114 poses).
- `make verify` OK.

## Se o travamento Clark × Vice voltar

Informe: qual golpe estava saindo, se o Clark era P1 ou P2, se o relógio
parou, se a música continuou e a versão do firmware do SD2SNES
(recomendado 1.11.2 ou mais novo).
