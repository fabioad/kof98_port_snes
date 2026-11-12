# Áudio aprovado: Final Fight Guy HQ

Fonte permanente dos 17 módulos aprovados em 2026-11-12 na ROM de teste
`kof98-ffg-soundtest.sfc` (comparação ATUAL × NOVA). Os dez `stgN.it` e os
sete `menu_*.it` são cópias exatas de `music/ffg_hq/it/`, convertidos de novo
a partir do MIDI por `music/ffg_hq/tools/mid2it_ffg.py`. As características:

- arranjo completo em 8 canais, com alocação por prioridade;
- instrumentos Capcom extraídos da ROM local do Final Fight Guy;
- estéreo por canal MIDI e envelopes com release curto;
- volume global igualado ao pacote anterior.

Ryu-ko (stg8) foi cortada em 280 s para caber no teto de ARAM real, medido
no jogo (veja `tools/validate_snesmod.py`).

`manifest.json` liga cada módulo ao destino, ao MIDI de origem e aos hashes
aprovados. `tools/approved_music.py` instala os módulos e recusa dados
alterados ou MIDI com hash diferente. Isso impede que uma recompilação use um
arranjo desatualizado para um MIDI modificado.

O build não depende da ROM de referência, dos MP3, do libgme nem da extração:

```sh
make -f Makefile.pvsnes all verify
```

O SDK SNESMOD converte estes IT para o soundbank e aplica o teto de ARAM
(`tools/validate_snesmod.py`) com os efeitos e a reserva de vozes do projeto.

Para alterar notas ou timbres no futuro:

1. Gere tudo de novo com `python3 music/ffg_hq/tools/build_hq.py`.
2. Ouça na ROM gerada por `music/ffg_hq/tools/make_soundtest.py`.
3. Copie os IT para este diretório e atualize os hashes no manifest.

Os arquivos `assets/audio/menu/*.it` e `build/gen_audio/it/stg*.it` são os
destinos de instalação, não a fonte a ser editada.

O pacote anterior (2026-11-05, `music/ffg_energy/`) continua no histórico do git.
