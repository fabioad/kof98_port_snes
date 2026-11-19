# Jason — falas do `Jason.snd`

Transcrição das falas gravadas no banco de voz de **Jason**. Cada linha é um
sample do `.snd`, identificado pelo par `grupo,índice` usado nos estados.

- Arquivos: `chars/Jason/voice/<grupo>_<índice>.wav`, mono 44,1 kHz.
- Fonte: recortes do vocal isolado dos trailers de GTA VI (Demucs), não são
  falas sintetizadas.
- O texto abaixo é a fala pretendida daquele trecho, como registrada em
  `audio/voice_manifest.json`. Vários clipes são **fragmentos** de uma frase
  (começam ou terminam no meio); a frase completa está em
  `documentation/VOICE_LINES.md`, e eu a uso quando o fragmento sozinho não faz
  sentido.
- O Whisper foi rodado nos clipes para conferência, mas em trechos de 0,5–1,5 s
  ele alucina com frequência (chegou a inventar frases inteiras). Por isso o
  texto aqui não é a saída bruta do reconhecedor.
- Os grupos `11,x` não têm fala: são grunhidos feitos a partir da vogal de uma
  fala curta do próprio personagem, com pitch descido.

## Resumo

| Grupo | Conteúdo | Samples |
|---|---|---|
| `10` | falas dos golpes normais e especiais | 0–6 |
| `11` | grunhidos de dano | 0–4 |
| `12` | deboche, vitória e intro | 0–3 |
| `13` | super, arremesso e MAX | 0–2 |
| `14` | grito de batalha | 0–1 |

## Golpes (grupo 10)

| Som | Arquivo | Duração | Fala | Tradução | Onde toca |
|---|---|---:|---|---|---|
| `10,0` | `10_00.wav` | 0.48 s | "Hey." | "Ei." | golpes fracos (soco/chute em pé, agachado e no ar) |
| `10,4` | `10_04.wav` | 0.59 s | "We got it." | "A gente dá conta." | variante dos golpes fracos |
| `10,1` | `10_01.wav` | 0.68 s | "You might have." | "Você talvez tenha." | golpes fortes e CD |
| `10,5` | `10_05.wav` | 1.02 s | "Oh, that's why you came by?" | "Ah, foi por isso que você veio?" | variante dos golpes fortes |
| `10,2` | `10_02.wav` | 1.14 s | "I'm just fixing some leaks." | "Só estou consertando uns vazamentos." | especiais |
| `10,6` | `10_06.wav` | 1.60 s | "We're doing it right." | "A gente está fazendo certo." | variante dos especiais |
| `10,3` | `10_03.wav` | 0.64 s | "See you, Brian." | "Até mais, Brian." | investidas (Getaway Rush) |

## Dano (grupo 11)

| Som | Arquivo | Duração | Fala | Tradução | Onde toca |
|---|---|---:|---|---|---|
| `11,0` | `11_00.wav` | 0.28 s | grunhido curto | — | dano leve |
| `11,1` | `11_01.wav` | 0.40 s | grunhido médio | — | dano forte |
| `11,2` | `11_02.wav` | 0.54 s | grunhido longo, com cauda | — | queda |
| `11,3` | `11_03.wav` | 0.26 s | grunhido curto alternativo | — | dano leve (variante) |
| `11,4` | `11_04.wav` | 0.33 s | grunhido médio alternativo | — | dano forte (variante) |

## Deboche, vitória e intro (grupo 12)

| Som | Arquivo | Duração | Fala | Tradução | Onde toca |
|---|---|---:|---|---|---|
| `12,0` | `12_00.wav` | 1.02 s | "Oh, that's why you came by?" | "Ah, foi por isso que você veio?" | deboche (taunt) |
| `12,1` | `12_01.wav` | 2.89 s | "Stuck together through everything. Gotta get through it." | "Juntos em tudo. Temos que superar isso." | vitória |
| `12,2` | `12_02.wav` | 2.64 s | "I got in some trouble in the army. Didn't leave on the best of terms." | "Arranjei problema no exército. Não saí em bons termos." | intro |
| `12,3` | `12_03.wav` | 2.54 s | "They don't give loans or anything to people like me." | "Eles não dão empréstimo nem nada para gente como eu." | vitória (variante) |

## Super, arremesso e MAX (grupo 13)

| Som | Arquivo | Duração | Fala | Tradução | Onde toca |
|---|---|---:|---|---|---|
| `13,0` | `13_00.wav` | 2.93 s | "I'm here for Lucia Caminos. She's supposed to be getting out." | "Vim buscar a Lucia Caminos. Era para ela estar saindo." | super (Lead Rain) |
| `13,1` | `13_01.wav` | 0.59 s | "We got it." | "A gente dá conta." | arremesso e finalizador do super |
| `13,2` | `13_02.wav` | 1.60 s | "We're doing it right." | "A gente está fazendo certo." | ativação de MAX |

## Grito de batalha (grupo 14)

| Som | Arquivo | Duração | Fala | Tradução | Onde toca |
|---|---|---:|---|---|---|
| `14,0` | `14_00.wav` | 0.48 s | "Hey." | "Ei." | grito de batalha (início da luta) |
| `14,1` | `14_01.wav` | 0.59 s | "We got it." | "A gente dá conta." | grito de batalha (variante) |

## Observações

- Normais e especiais sorteiam entre as variantes com `random % N`, então a
  mesma fala pode não sair em todo golpe.
- `10,4`–`10,6`, `11,3`–`11,4`, `12,3` e `14,0`–`14,1` são variantes criadas
  depois; os índices `10,0`–`10,3` são os originais.
- **Licença:** as vozes pertencem à Rockstar Games / Take-Two e aos atores.
  Uso pessoal neste projeto de fã; não redistribua os WAVs nem um pacote que os
  contenha. Para publicar, troque os grupos `10`–`14` pelas vozes sintéticas de
  `tools/sfx.py` ou por gravações próprias.
- Para regravar: edite `audio/voice_manifest.json` e rode
  `python3 tools/voice_build.py` (remonta o `.snd` mantendo os efeitos).
