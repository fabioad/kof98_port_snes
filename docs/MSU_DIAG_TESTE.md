# Teste do MSU no SD2SNES MKII — diagnóstico D1

Extraia `kof98-msu-diag.sfc` e `kof98-msu-diag.msu` na mesma pasta do SD.
Inicie essa ROM, entre em uma luta com Rugal normal contra Kyo e aguarde
alguns segundos. Faça ataques e tire uma foto da tela com os números.
Depois repita com dois personagens MSU, por exemplo Rugal contra Leona.
Use o arquivo `.msu` deste pacote, sem renomear apenas um dos arquivos.

Esta versão instrumenta o carregamento atual; ainda não aplica a correção
de busca persistente. A ROM normal não é substituída.

## Números na tela

Todos os números estão em hexadecimal. Os contadores acumulam desde o boot
e voltam a zero ao ultrapassar FFFF. O painel atualiza a cada 16 quadros
apresentados durante a luta. Fica nas linhas 5 a 8 do HUD, sobre o cenário.

- `CPU`: bytes diferentes dos esperados em três amostras de 1280 bytes
  lidas pela CPU no boot. O esperado é `0000`.
- `VRAM`: palavras de 16 bits diferentes dos esperados após DMA MSU→VRAM
  no boot. Usa o mesmo canal 5, modo 09 e tamanho dos uploads dos lutadores.
  O esperado é `0000`. Esse teste lê a VRAM de volta pela CPU.
- `B`: resultado do teste inicial: `0000` terminou; `0001` timeout na busca
  do teste CPU; `0002` timeout na busca do teste DMA; `0004` MSU não detectado
  (CPU e VRAM mostram FFFF, sem teste). Com B diferente de zero, CPU/VRAM
  não representam uma verificação completa.
- `REQ`: buscas dos gráficos solicitadas durante o jogo.
- `OK`: buscas dos gráficos que ficaram prontas dentro do limite original.
- `TO`: buscas dos gráficos que excederam o limite de 1024 consultas.
  Conta apenas gráficos, separado de eventuais timeouts das vozes.
- `P1` / `P2`: blocos de gráficos MSU transferidos por DMA de cada jogador.
  Não contam os personagens residentes na ROM nem os testes iniciais.
- `ST`: último status lido durante a espera dos gráficos. O bit 80 indica
  MSU ocupado; outros bits do status podem estar ligados normalmente.
- `POS`: última posição solicitada no arquivo `.msu`.
- `LEN`: tamanho em bytes do último bloco solicitado; até `0500` (1280).

## Como interpretar

- CPU=0000, VRAM=0000, B=0000 e TO crescendo com P1/P2 parados: forte sinal
  de falha no tempo de espera/buscas repetidas durante a luta.
- CPU diferente de zero com B=0000: dados lidos não correspondem ao `.msu`
  empacotado; investigar arquivo, leitura, mapeamento e integridade do SD.
- CPU=0000 e VRAM diferente de zero com B=0000: investigar caminho DMA/VRAM.
- Ambos os testes passam e P1/P2 crescem apesar de personagens corrompidos:
  investigar transferências durante a luta, concorrência com vozes, endereços,
  geometria/OAM e momento em que a página de tiles fica visível.

O teste inicial usa uma espera maior (FFFF consultas) e amostras do começo,
meio e final do conjunto de personagens (Rugal, Chizuru e Ken). Ele ajuda a
separar integridade dos dados de prazo durante a luta, mas não valida todo
o arquivo. O painel adiciona uma transferência de 256 bytes a cada 16 quadros;
isso altera um pouco o tempo de apresentação. Validação em emulador não
substitui o teste no console.

Recompilar: `python3 tools/build_msu_diag.py`, com os objetos e recursos do
build normal já presentes. A saída fica em `build/msu_diag` e no pacote
`kof98-msu-diag.zip` na raiz do projeto.
