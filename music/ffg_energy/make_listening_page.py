"""Write a local offline playlist for the MP3 deliverables."""
import html,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_stages
stages={f'stg{i}':(Path(f).stem.replace('KOF98-',''),build_stages.stage_song(Path(f).stem)) for i,f in enumerate(build_stages.sorted_stage_paths())}
menus={'cipher':'Cipher — abertura','cipher_beta':'Cipher Beta — título','crystal':'Crystal — final Survivor','kof':'The King of Fighters — seleção','lastdance':'Last Dance','sunset':'Sunset','winner':'Vitória'}
rows=[]
for file in sorted((HERE/'candidates').glob('*.it'),key=lambda f:(f.stem.startswith('menu'),f.name)):
    key=file.stem
    if key in stages:title,source=stages[key]
    else:title=menus.get(key.removeprefix('menu_'),key);source='Frontend / finais'
    esc=html.escape
    rows.append(f'<section><h2>{esc(title)}</h2><p class="source">{esc(source)}</p><div class="pair"><div><label>Anterior</label><audio controls preload="none" src="previews/{key}_antes.mp3"></audio><a download href="previews/{key}_antes.mp3">MP3 anterior</a></div><div><label>Final Fight Guy — aprovada</label><audio controls preload="none" src="previews/{key}_ffg.mp3"></audio><a download href="previews/{key}_ffg.mp3">MP3 novo</a></div></div></section>')
refs=''.join(f'<div><label>Sequência {i:02d} da ROM</label><audio controls preload="none" src="previews/referencia_ffg_{i:02d}.mp3"></audio></div>' for i in [1,2,6,13])
page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>KOF · Timbres Final Fight Guy</title><style>
+:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#151719;color:#e6e7e8;font:16px/1.55 system-ui,sans-serif}main{max-width:1080px;margin:auto;padding:40px 24px}h1{font-size:28px;line-height:1.2;margin:0 0 12px}h2{font-size:19px;margin:0}p{max-width:800px}.intro{padding-bottom:24px;border-bottom:1px solid #42474b}.tag{font-size:12px;letter-spacing:1.5px;text-transform:uppercase;color:#baac8f}.source{font-size:13px;color:#a5a9ac;margin:3px 0 16px}section{padding:24px 0;border-bottom:1px solid #34383b}.pair{display:grid;grid-template-columns:1fr 1fr;gap:32px}label{display:block;margin-bottom:8px;font-size:14px}audio{display:block;width:100%;margin-bottom:8px}a{font-size:13px;color:#c7b387}.refs{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:20px}.note{font-size:14px;color:#bfc3c6}@media(max-width:650px){.pair,.refs{grid-template-columns:1fr}main{padding:24px 16px}}
+</style><main><div class="intro"><p class="tag">KOF98 / SNES · prévia de áudio</p><h1>Mais ataque. As mesmas notas.</h1><p>17 músicas com timbres e bateria derivados da ROM local de Final Fight Guy. Versões aprovadas para o jogo. Compare o áudio novo com os módulos anteriores à integração.</p><p class="note">60 segundos por faixa; vitória: 12 segundos. Áudio produzido pelo programa SPC700/S-DSP emulado a 32 kHz e convertido para MP3 192 kb/s. Não é uma gravação de um console físico. Sem equalização, compressor ou reverb acrescentados após a emulação.</p><p class="note">O volume global da proposta tem margem adicional para evitar saturação no DSP. O mesmo ganho de exportação foi usado nos dois MP3; os pares não foram normalizados para a mesma intensidade. O backup da ROM anterior está preservado em integration-backup-20261105-093142.tar.gz.</p></div>'''.replace('\n+','\n')
page+=''.join(rows)+f'<section><h2>Referência extraída da ROM</h2><p class="note">Trechos de 45 segundos. IDs internos; os nomes originais das faixas não foram inferidos.</p><div class="refs">{refs}</div></section></main><script>document.addEventListener("play",e=>{{if(e.target.tagName==="AUDIO")document.querySelectorAll("audio").forEach(a=>{{if(a!==e.target)a.pause()}})}},true)</script></html>'
(HERE/'ouvir.html').write_text(page)
