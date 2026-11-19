# Lucia — falas do `Lucia.snd`

Transcrição das falas gravadas no banco de voz de **Lucia**. Cada linha é um
sample do `.snd`, identificado pelo par `grupo,índice` usado nos estados.

- Arquivos: `chars/Lucia/voice/<grupo>_<índice>.wav`, mono 44,1 kHz.
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
| `10,0` | `10_00.wav` | 0.53 s | "Hey." | "Ei." | golpes fracos (soco/chute em pé, agachado e no ar) |
| `10,4` | `10_04.wav` | 0.85 s | "Bad luck, I guess." | "Azar, eu acho." | variante dos golpes fracos |
| `10,1` | `10_01.wav` | 0.45 s | "Trust me!" | "Confia em mim!" | golpes fortes e CD |
| `10,5` | `10_05.wav` | 1.18 s | "…is by sticking together." | "…é ficando juntos." | variante dos golpes fortes |
| `10,2` | `10_02.wav` | 1.71 s | "…this place is just the start for us." | "…esse lugar é só o começo para nós." | especiais |
| `10,6` | `10_06.wav` | 1.08 s | "We're gonna get through this." | "A gente vai superar isso." | variante dos especiais |
| `10,3` | `10_03.wav` | 0.45 s | "Trust me!" | "Confia em mim!" | investidas |

## Dano (grupo 11)

| Som | Arquivo | Duração | Fala | Tradução | Onde toca |
|---|---|---:|---|---|---|
| `11,0` | `11_00.wav` | 0.22 s | grunhido curto | — | dano leve |
| `11,1` | `11_01.wav` | 0.31 s | grunhido médio | — | dano forte |
| `11,2` | `11_02.wav` | 0.44 s | grunhido longo, com cauda | — | queda |
| `11,3` | `11_03.wav` | 0.20 s | grunhido curto alternativo | — | dano leve (variante) |
| `11,4` | `11_04.wav` | 0.25 s | grunhido médio alternativo | — | dano forte (variante) |

## Deboche, vitória e intro (grupo 12)

| Som | Arquivo | Duração | Fala | Tradução | Onde toca |
|---|---|---:|---|---|---|
| `12,0` | `12_00.wav` | 0.85 s | "Bad luck, I guess." | "Azar, eu acho." | deboche (taunt) |
| `12,1` | `12_01.wav` | 3.96 s | "The only thing that matters is who you know and what you got." | "O que importa é quem você conhece e o que você tem." | vitória |
| `12,2` | `12_02.wav` | 1.61 s | "Are we gonna be okay?" | "A gente vai ficar bem?" | intro |
| `12,3` | `12_03.wav` | 3.37 s | "The only way we're gonna get through this…" | "O único jeito de a gente superar isso…" | vitória (variante) |

## Super, arremesso e MAX (grupo 13)

| Som | Arquivo | Duração | Fala | Tradução | Onde toca |
|---|---|---:|---|---|---|
| `13,0` | `13_00.wav` | 2.19 s | "Trust me, this place is just the start for us." | "Confia: esse lugar é só o começo para nós." | super (Atraco Total) |
| `13,1` | `13_01.wav` | 0.45 s | "Trust me!" | "Confia em mim!" | arremesso e finalizador do super |
| `13,2` | `13_02.wav` | 1.08 s | "We're gonna get through this!" | "A gente vai superar isso!" | ativação de MAX |

## Grito de batalha (grupo 14)

| Som | Arquivo | Duração | Fala | Tradução | Onde toca |
|---|---|---:|---|---|---|
| `14,0` | `14_00.wav` | 0.53 s | "Hey." | "Ei." | grito de batalha (início da luta) |
| `14,1` | `14_01.wav` | 0.45 s | "Trust me!" | "Confia em mim!" | grito de batalha (variante) |

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
