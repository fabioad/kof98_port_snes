// Localized imagegen retouches. Animation source tiles remain exact.
// Usage: node export.mjs (sources and before/ must exist beside this script).
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {deflateSync} from 'node:zlib';
const here=path.dirname(fileURLToPath(import.meta.url)), W=512,H=224;
const rgb=f=>execFileSync('convert',[f,'-alpha','off','-filter','Box','-resize','512x224!','-depth','8','RGB:-']);
const crcTable=Uint32Array.from({length:256},(_,n)=>{for(let k=0;k<8;k++)n=n&1?0xedb88320^(n>>>1):n>>>1;return n>>>0;});
function chunk(type,data){const body=Buffer.concat([Buffer.from(type),data]);let crc=0xffffffff;for(const b of body)crc=crcTable[(crc^b)&255]^(crc>>>8);const out=Buffer.alloc(data.length+12);out.writeUInt32BE(data.length);body.copy(out,4);out.writeUInt32BE((crc^0xffffffff)>>>0,out.length-4);return out;}
function png(pix,palette){const used=[...new Set(pix)].sort((a,b)=>a-b), map=new Map(used.map((v,i)=>[v,i]));const rows=Buffer.alloc(H*(W/2+1));for(let y=0;y<H;y++)for(let x=0;x<W;x+=2)rows[y*(W/2+1)+1+x/2]=map.get(pix[y*W+x])*16+map.get(pix[y*W+x+1]);const hdr=Buffer.alloc(13);hdr.writeUInt32BE(W);hdr.writeUInt32BE(H,4);hdr[8]=4;hdr[9]=3;return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',hdr),chunk('PLTE',Buffer.from(used.flatMap(i=>palette[i]))),chunk('IDAT',deflateSync(rows,{level:9})),chunk('IEND',Buffer.alloc(0))]);}
// Masks use full native tiles. The crowd/rower and their source margins are excluded.
function editable(name,x,y){
 if(name.includes('China')) return x>=272&&x<448&&y<144;
 if(name.includes('JpnStreet')) return y>=176&&x<320;
 if(name.includes('Spain')) return y>=184;
 if(name.includes('USAWharfStage-B')) return y<96&&x>=192&&!(x>=272&&x<384&&y>=16);
 if(name.includes('USAWharf')) return y<144&&x>=216&&!(x<344&&y>=16)&&!(x>=344&&y>=112);
 return false;
}
const report=[];
for(const name of fs.readdirSync(path.join(here,'sources')).filter(f=>f.endsWith('.png')).sort()){
 const old=rgb(path.join(here,'before',name)), generated=rgb(path.join(here,'sources',name));
 const originalFile=fs.readFileSync(path.join(here,'before',name));let palette=[];
 for(let pos=8;pos<originalFile.length;){const n=originalFile.readUInt32BE(pos);if(originalFile.toString('ascii',pos+4,pos+8)==='PLTE'){const p=originalFile.subarray(pos+8,pos+8+n);palette=Array.from({length:n/3},(_,i)=>[...p.subarray(i*3,i*3+3)]);break;}pos+=12+n;}
 const active=new Set();for(let p=0;p<W*H;p++)active.add([...old.subarray(p*3,p*3+3)].join(','));palette=palette.filter(c=>active.has(c.join(',')));
 const lookup=new Map(palette.map((c,i)=>[c.join(','),i])),original=Buffer.alloc(W*H),candidate=Buffer.alloc(W*H);
 for(let p=0;p<W*H;p++)original[p]=lookup.get([...old.subarray(p*3,p*3+3)].join(','));
 const dist=(a,b)=>.30*(a[0]-b[0])**2+.59*(a[1]-b[1])**2+.11*(a[2]-b[2])**2;
 for(let p=0;p<W*H;p++){let best=Infinity;for(let i=0;i<palette.length;i++){const d=dist(generated.subarray(p*3,p*3+3),palette[i]);if(d<best){best=d;candidate[p]=i;}}}
 if(name.includes('China'))for(let p=0;p<W*H;p++)if(original[p]<5||original[p]>9)candidate[p]=original[p];
 // Avoid newly introduced colored specks in the neutral Japanese asphalt.
 if(name.includes('JpnStreet'))for(let p=0;p<W*H;p++)if(![8,11,12,13,14].includes(candidate[p]))candidate[p]=original[p];
 const colors=palette.map(a=>palette.map(b=>dist(a,b))),locked=new Map(),pool=new Map(),cells=[];
 for(let y=0;y<H;y+=8)for(let x=0;x<W;x+=8){const edit=editable(name,x,y),t=Buffer.alloc(64);for(let r=0;r<8;r++)t.set((edit?candidate:original).subarray((y+r)*W+x,(y+r)*W+x+8),r*8);const key=t.toString('hex');cells.push({x,y,edit,key,t});if(edit){if(!pool.has(key))pool.set(key,{t,count:0});pool.get(key).count++;}else locked.set(key,t);}
 const error=(a,b,limit=Infinity)=>{let s=0;for(let p=0;p<64;p++){s+=colors[a[p]][b[p]]*((p<8||p>=56||p%8===0||p%8===7)?3:1);if(s>limit)return s;}return s;};
 // Reclaim at most 48 slots by merging the closest static tile pairs.
 // Unlike averaging pixels, choosing a real tile retains intentional contours.
 const spec=JSON.parse(fs.readFileSync(path.join(here,'..','..','animations','stage_animations.json')));
 const protectedRegions=spec.clips.filter(c=>c.stage+'.png'===name&&c.target.target_region_xywh).map(c=>c.target.target_region_xywh);
 const protectedKeys=new Set(cells.filter(c=>protectedRegions.some(([x,y,w,h])=>c.x<x+w&&c.x+8>x&&c.y<y+h&&c.y+8>y-8)).map(c=>c.key));
 const usage=new Map();for(const c of cells)if(!c.edit)usage.set(c.key,(usage.get(c.key)||0)+1);
 const merge=new Map();
 const entries=[...locked.entries()],pairs=[];
 for(let i=0;i<entries.length;i++)for(let j=i+1;j<entries.length;j++){
  const [a,ta]=entries[i],[b,tb]=entries[j],d=error(ta,tb);
  if(!protectedKeys.has(a))pairs.push({a,b,cost:d*usage.get(a)});
  if(!protectedKeys.has(b))pairs.push({a:b,b:a,cost:d*usage.get(b)});
 }
 pairs.sort((a,b)=>a.cost-b.cost);
 for(const {a,b} of pairs){if(locked.size<=464)break;if(!locked.has(a)||!locked.has(b)||[...merge.values()].includes(a))continue;locked.delete(a);merge.set(a,b);}
 const centers=[...locked.values()], items=[...pool.values()],nearest=items.map(()=>Infinity),assign=items.map(()=>0);
 function consider(c,k){items.forEach((a,i)=>{const d=error(a.t,c,nearest[i]);if(d<nearest[i]){nearest[i]=d;assign[i]=k;}});}
 centers.forEach(consider);
 while(centers.length<512){let best=0,next=-1;items.forEach((a,i)=>{const score=nearest[i]*Math.sqrt(a.count);if(score>best){best=score;next=i;}});if(next<0)break;const c=items[next].t;centers.push(c);consider(c,centers.length-1);}
 const replacements=new Map([...pool.keys()].map((key,i)=>[key,centers[assign[i]]]));
 const out=Buffer.from(original);let changed=0;
 for(const c of cells){if(!c.edit&&!merge.has(c.key))continue;const t=c.edit?replacements.get(c.key):locked.get(merge.get(c.key));for(let r=0;r<8;r++)for(let k=0;k<8;k++){const p=(c.y+r)*W+c.x+k;out[p]=t[r*8+k];if(out[p]!==original[p])changed++;}}
 const output=path.join(here,'..','ready',name);fs.writeFileSync(output,png(out,palette));
 const tiles=new Set(cells.map(c=>{const t=Buffer.alloc(64);for(let r=0;r<8;r++)t.set(out.subarray((c.y+r)*W+c.x,(c.y+r)*W+c.x+8),r*8);return t.toString('hex');})).size;
 if(tiles>512)throw Error('Tile budget exceeded');
 const row={name,tiles,colors:palette.length,lockedTiles:locked.size,editedCells:cells.filter(c=>c.edit).length,changedPixels:changed};report.push(row);console.log(row);
}
fs.writeFileSync(path.join(here,'metrics.json'),JSON.stringify(report,null,2)+'\n');
