# Proposta de timbres Final Fight Guy para KOF98 SNES

Abra [ouvir.html](ouvir.html) para ouvir os pares atual/proposta.
Os MP3 estão em `previews/`: 60 segundos por música, 12 para vitória.
Há 17 propostas, 17 comparações anteriores e quatro referências da ROM.

A proposta foi **aprovada e integrada ao projeto e à ROM** em 2026-11-05.
Os 17 IT em `candidates/` são idênticos aos arquivos ativos, com fontes
permanentes em `assets/audio/ffg/`. Os MIDIs permanecem preservados.
`before/` guarda os 17 módulos anteriores; o backup integral anterior à
integração está em `integration-backup-20261105-093142.tar.gz`, incluindo
ROM, MSU, símbolos e soundbank. Hashes em `integration-backup.json`.

## O que foi extraído e examinado

Fonte: `music/examples/Final Fight Guy (Japan).sfc`, ROM de 1 MiB fornecida
localmente. Hash SHA-256 em `reference/extraction.json`.
A extração executa a ROM pelo Snes9x libretro instalado, captura RAM e DSP
do APU e encontra o driver Capcom residente:

- Lista de sequências: ARAM `$0e02`.
- Instrumentos: ARAM `$4a00`, entradas de seis bytes (SRCN, ADSR1,
  ADSR2, GAIN e escala de afinação).
- Diretório de amostras: ARAM `$4800`, valor efetivo do registrador DIR.
- 28 amostras BRR, exportadas também em PCM WAV mono a 32 kHz.
  Todas têm correspondência exata de seus bytes BRR na ROM; offsets no JSON.
- 21 sequências residentes com cabeçalhos válidos, exportadas como SPC.
  Os IDs incluem músicas, jingles e possíveis efeitos multicanal; não se
  atribuiu título comercial nem classificação definitiva a cada ID.

Os SPC das sequências usam um pequeno seletor em RAM livre `$ff00` e um RET
no polling do host. Isso permite iniciar cada ID sem a CPU 65816, que não
existe num arquivo SPC. Os dados de sequência, instrumentos e amostras
continuam sendo os da ROM. `runtime.spc`, `apu_ram.bin` e `apu_dsp.bin`
guardam a captura anterior a essa seleção.

A base técnica foi conferida nas implementações oficiais de
[CapcomSnesScanner do VGMTrans](https://github.com/vgmtrans/vgmtrans/blob/master/src/main/formats/CapcomSnes/CapcomSnesScanner.cpp),
[CapcomSnesInstr](https://github.com/vgmtrans/vgmtrans/blob/master/src/main/formats/CapcomSnes/CapcomSnesInstr.cpp)
e no decodificador BRR do
[Snes9x](https://github.com/snes9xgit/snes9x/blob/master/apu/bapu/dsp/SPC_DSP.cpp).
As equações de filtros BRR em `extract_reference.py` seguem esse decodificador.

## Direção sonora aplicada

O banco de referência usa núcleos de onda curtos, loops compactos e ataque
rápido. Os primeiros instrumentos têm ADSR1 `$ff`; ADSR2 e GAIN variam por
programa. O bumbo e a caixa são amostras curtas que concentram o impacto no
início do som, enquanto os instrumentos sustentados reutilizam pequenos
loops. Os valores exatos, duração, loop e escala de afinação de cada fonte
estão em `reference/extraction.json`.

No projeto, parte dos instrumentos antigos foi reduzida a 3–5,5 kHz.
Nesta proposta são usados os PCM decodificados das amostras BRR originais,
sem esse rebaixamento global de taxa:

- Bumbo, caixa e tom: fontes 07, 06 e 08 da ROM.
- Chimbal, prato e rim: articulações curtas derivadas da porção ruidosa da
  caixa, com filtro de diferença e envelope de queda. São adaptações;
  não são apresentados como pratos originais extraídos de Final Fight Guy.
- Baixos: fonte 04; pads: 03; teclas: 02/12; ataques e leads: 00/01/09.
  A escolha varia com a função do instrumento existente.

As notas **não foram regravadas nem reordenadas**. Ordens e padrões IT,
keymaps, envelopes dos instrumentos, comandos de efeito, pan e andamento
foram preservados byte a byte. Foram trocados os PCM e os cabeçalhos de
amostra que definem afinação/loops. A afinação usa a escala do driver Capcom
com estimativa do registro de oitava do timbre anterior. Essa estimativa
não constitui uma aferição perceptiva de afinação em todas as notas.

Foi reservada margem no volume global do módulo (75% do valor anterior)
para evitar saturação ao somar as novas fontes. Isso não altera a sequência
de notas, mas faz algumas propostas soarem mais baixas que o original.
Não se normalizou a intensidade entre os pares. Os envelopes IT existentes
foram mantidos; não se promete reprodução idêntica do ADSR do driver Capcom
pelo driver SNESMOD.

## Como os MP3 foram produzidos

Caminho: **IT proposto → smconv do SDK PVSnesLib 4.6 → SPC executável →
emulação SPC700/S-DSP pelo libgme → PCM estéreo 32 kHz → MP3 192 kb/s**.
Não é um render de MIDI por SoundFont. Nenhuma equalização, compressão ou
reverberação foi aplicada depois da emulação. Ambos os lados recebem o
mesmo ganho fixo de exportação de 0,70.

Isso demonstra a execução da música no APU emulado. **Não é gravação de um
SNES físico**, nem captura da luta com efeitos e vozes concorrentes. Essas
condições precisarão ser verificadas na integração, depois da revisão sonora.

Foi encontrado um defeito no exportador standalone do smconv instalado:
`MakeSPC` usa `module_base=$18ca`, enquanto as tabelas e o driver usam `$1a00`.
O driver compilado maior termina em `$19aa`, e o preenchimento negativo é
ignorado. O resultado inicial era silêncio. `spc_export.py` localiza o
cabeçalho do módulo e reloca somente seus dados para `$1a00`, mantendo
intactos driver, notas e amostras. Essa correção foi aplicada apenas aos
SPC de revisão; não modificou o SDK ou a ROM. Ver
[código oficial de MakeSPC](https://github.com/alekmaul/pvsneslib/blob/master/tools/smconv/it2spc.cpp).

## Validação dos previews, antes da integração

- Os 17 módulos ativos continuam com os hashes anteriores.
- Padrões e ordens comparados por bytes e SHA-256; instrumentos e keymaps
  conferidos byte a byte na produção dos candidatos.
- Os 17 módulos passaram em `tools/validate_snesmod.py`: máximo de 33.614
  bytes por módulo, abaixo do teto de 44.500 bytes do projeto.
- Os 17 novos trechos têm áudio não nulo e nenhum sample saturado na saída
  PCM do DSP emulado durante o intervalo gravado. Alguns originais saturam;
  não se alterou o lado “antes” para esconder isso.
- Os 38 MP3 foram abertos com ffprobe; codec, estéreo, taxa e duração conferidos.
- Não houve compilação nem substituição da ROM do jogo.

Esses itens descrevem a etapa de revisão anterior. Na integração aprovada,
os módulos ativos foram substituídos e `kof98-snes.sfc` foi recompilada.
O projeto agora copia os arquivos aprovados por `tools/approved_music.py`,
com hashes do MIDI e do módulo para impedir regressão aos timbres antigos.
O soundbank é gerado por `smconv -s`; a correção do exportador standalone
não é aplicada ao banco da ROM.

`candidates/manifest.json` registra fontes, alterações, hashes e ARAM.
`previews/validation.json` registra duração, pico, RMS e saturação antes do
ganho de exportação. Esses números se referem aos trechos gravados, não
constituem certificação de todas as passagens de cada música.

## Reprodução

Na raiz do projeto, com o mesmo SDK e libgme instalados:

```sh
python3 music/ffg_energy/extract_reference.py
python3 music/ffg_energy/build_candidates.py
python3 music/ffg_energy/render_previews.py
python3 music/ffg_energy/make_listening_page.py
python3 tools/validate_snesmod.py /run/media/fabio/Dados/Fabio/pvsneslib-sdk-4.6/devkitsnes/tools/smconv music/ffg_energy/candidates/*.it
```

A geração recusa sobrescrever uma baseline que difira do arquivo ativo.
A reprodução trabalha em `music/ffg_energy/` e não instala as músicas no jogo.

## Integração no projeto e na ROM

As 17 faixas aprovadas foram instaladas, sem refazer os arranjos, a partir
de `assets/audio/ffg/`. Uma recompilação completa gerou o novo soundbank e
`kof98-snes.sfc`, com o MSU correspondente ao lado da ROM.

Verificações da integração:

- Os 17 IT ativos são idênticos byte a byte aos candidatos ouvidos.
- Todas as partes do soundbank foram comparadas com os bytes embutidos na ROM.
- `tools/test_ffg_music_headless.py` carrega as 17 faixas no sound test da
  própria ROM, compara os cabeçalhos na ARAM com os SPC aprovados, verifica
  áudio e avanço dos ticks e completa a volta do seletor.
- Passaram também as regressões de trocas de música na fase 8 em Single,
  Survivor e Team, da passagem título/demo e da limpeza das vozes entre telas.
- As proteções de hash e preservação de notas têm testes em
  `tools/tests/test_approved_music.py`.

Os resultados e hashes finais ficam em `integration.json`.
O validador `tools/validate_snesmod.py` agora exporta seu SPC auxiliar em
pasta temporária: validar um IT não sobrescreve mais o SPC de preview.

> **Substituído em 2026-11-12** por `music/ffg_hq/` (reconversão HQ a partir
> dos MIDI). Este diretório fica como histórico do pacote de 2026-11-05.
