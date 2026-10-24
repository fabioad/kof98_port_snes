# Lutadores como blocos sólidos ("bug dos hitboxes") — 23/10/2026

## Sintoma

No meio da luta, um ou os dois lutadores somem e no lugar aparecem
retângulos sólidos do tamanho do metasprite, na cor de destaque da paleta
do personagem (Brian = bege `$533F`, Geese = amarelo `$0ADD`). O formato
acompanha as células 16x16 do metasprite, então parece uma "hitbox"
desenhada; o HUD, o cenário e os efeitos continuam corretos.

## Causa

Não é lógica de luta nem colisão. As páginas de OBJ ($6000-$7FFF) são
escritas só pelo upload de CHR dos lutadores (DMA do MSU-1). Se o arquivo
`kof98-snes.msu` for **truncado/reescrito enquanto o emulador está aberto**,
as leituras de CHR caem no novo fim de arquivo.

No Mesen, `Msu1::Read` faz:

```cpp
if(!_dataBusy && _dataPointer < _dataSize) {
    _dataPointer++;
    return (uint8_t)_dataFile.get();   // EOF -> -1 -> $FF
}
return 0;
```

`_dataSize` é capturado no boot. Depois de um `cp` que trunca o arquivo (mesmo
inode), `_dataPointer < _dataSize` continua verdadeiro, mas `get()` devolve
EOF, convertido em `$FF`. O ifstream ainda entra em fail state, então os
`seekg` seguintes falham e **toda** leitura do MSU vira `$FF` até reiniciar.

Com a página inteira em `$FF`, cada pixel vira índice 15 (os quatro planos
ligados). O índice 15 é justamente o realce da paleta de cada lutador — daí
o bege do Brian e o amarelo do Geese. A forma do bloco é o metasprite
correto desenhado com tiles chapados.

O Snes9x devolve `0` no fim do arquivo, e por isso o sintoma não aparece
nele (os lutadores ficariam transparentes). É um problema de arquivo
trocado durante a execução, não do motor.

## Repro (Mesen testRunner)

1. Copie ROM e `.msu` para uma pasta e chegue a uma luta com Brian × Geese.
2. Trunque o `.msu` aberto (ex.: `io.open(...,"wb")` com 8 bytes).
3. Force um novo upload (um golpe): os lutadores viram exatamente os blocos
   da captura do usuário.
4. Repita trocando o arquivo por `rename` (arquivo temporário + `mv`): a
   luta continua normal, porque o emulador segue no inode antigo, completo.

## Correção

- `Makefile.pvsnes`: o `.msu` é instalado em `$@.tmp` e movido com `mv -f`
  (rename atômico) em vez de `cp` direto sobre o alvo.
- `tools/build_fight.py`: grava `build/gen_fight/kof98-snes.msu` em
  `.tmp` + `os.replace`.
- README: documenta que um emulador aberto durante o build continua no
  arquivo antigo e passa a ler o novo no próximo lançamento.

Assim um build com o emulador aberto nunca deixa o `.msu` em estado
truncado. Se ainda aparecerem blocos numa sessão antiga, feche e reabra o
emulador depois do build.
