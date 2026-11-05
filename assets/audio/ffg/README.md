# Áudio aprovado: Final Fight Guy

Fonte permanente dos 17 módulos aprovados nos previews de `music/ffg_energy/`.
Os dez `stgN.it` e os sete `menu_*.it` são cópias exatas desses candidatos,
com padrões, andamento e keymaps preservados e timbres derivados da ROM local.

`manifest.json` liga cada módulo ao destino, à composição MIDI quando ela é
recompilada e aos hashes aprovados. `tools/approved_music.py` instala os
módulos e recusa dados alterados ou MIDI conhecido com hash diferente.
Isso impede que uma recompilação recoloque os timbres 909 antigos ou use
um arranjo desatualizado para um MIDI modificado.

O build não depende da ROM de referência, dos MP3, do libgme nem da extração:

```sh
make -f Makefile.pvsnes all verify
```

O SDK SNESMOD converte estes IT para o soundbank e aplica o teto de ARAM
com os efeitos e a reserva de vozes do projeto. A correção de endereçamento
usada nos SPC standalone de preview não participa do soundbank da ROM.

Para alterar notas ou timbres futuramente, gerar e ouvir novos candidatos,
atualizar os IT deste diretório e seus hashes no manifest. Os arquivos
`assets/audio/menu/*.it` e `build/gen_audio/it/stg*.it` são os destinos de
instalação, não a fonte a ser editada para persistir a alteração.
