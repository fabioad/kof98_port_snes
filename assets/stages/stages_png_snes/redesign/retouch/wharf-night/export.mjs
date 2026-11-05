// Second pass on USAWharf only: dark, quiet skyline and continuous navy sky.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {deflateSync} from 'node:zlib';
const here=path.dirname(fileURLToPath(import.meta.url)),W=512,H=224;
const raw=f=>execFileSync('convert',[f,'-alpha','off','-filter','Box','-resize','512x224!','-depth','8','RGB:-']);
const file=fs.readFileSync(path.join(here,'before.png'));let palette=[];
for(let pos=8;pos<file.length;){const n=file.readUInt32BE(pos);if(file.toString('ascii',pos+4,pos+8)==='PLTE'){const p=file.subarray(pos+8,pos+8+n);palette=Array.from({length:n/3},(_,i)=>[...p.subarray(i*3,i*3+3)]);break;}pos+=12+n;}
const originalPalette=palette.map(c=>[...c]);
const lookup=new Map(palette.map((c,i)=>[c.join(','),i]));
const old=raw(path.join(here,'before.png')),source=raw(path.join(here,'source.png'));
const original=Buffer.alloc(W*H),pix=Buffer.alloc(W*H);
for(let p=0;p<W*H;p++)original[p]=lookup.get([...old.subarray(p*3,p*3+3)].join(','));
palette[6]=[0,16,41];palette[7]=[0,25,58];palette[10]=[8,41,74];palette[11]=[8,33,66];
const blue=[6,7,10,11,13],isBlue=i=>{const [r,g,b]=originalPalette[i];return b>r*1.15&&b>g*1.03;};
const dist=(a,b)=>.30*(a[0]-b[0])**2+.59*(a[1]-b[1])**2+.11*(a[2]-b[2])**2;
for(let y=0;y<H;y++)for(let x=0;x<W;x++){
 const p=y*W+x,i=original[p];pix[p]=i;
 // Warm sails/rigging remain exact; vehicles and foreground keep their indices.
 if(x<206||y>=144||!isBlue(i)||(y>=110&&x<350)||(y>=136&&x>=350))continue;
 const c=source.subarray(p*3,p*3+3);let best=Infinity;
 for(const j of blue){const d=dist(c,palette[j]);if(d<best){best=d;pix[p]=j;}}
}
// Merge only newly edited tiles if the combined background exceeds its budget.
const cells=[],locked=new Map(),pool=new Map();
for(let y=0;y<H;y+=8)for(let x=0;x<W;x+=8){const a=Buffer.alloc(64),b=Buffer.alloc(64);for(let r=0;r<8;r++){a.set(original.subarray((y+r)*W+x,(y+r)*W+x+8),r*8);b.set(pix.subarray((y+r)*W+x,(y+r)*W+x+8),r*8);}const edit=!a.equals(b),key=b.toString('hex');cells.push({x,y,t:b,key,edit});if(!edit)locked.set(key,b);else if(!pool.has(key))pool.set(key,b);}
const colors=palette.map(a=>palette.map(b=>dist(a,b)));
function error(a,b,limit=Infinity){let n=0;for(let i=0;i<64;i++){n+=colors[a[i]][b[i]]*((i<8||i>=56||i%8===0||i%8===7)?3:1);if(n>limit)return n;}return n;}
const centers=[...locked.values()],items=[...pool.entries()],nearest=items.map(()=>Infinity),assignment=items.map(()=>0);
function consider(t,k){items.forEach(([,a],i)=>{const e=error(a,t,nearest[i]);if(e<nearest[i]){nearest[i]=e;assignment[i]=k;}});}
centers.forEach(consider);
while(centers.length<512){let best=0,next=-1;nearest.forEach((e,i)=>{if(e>best){best=e;next=i;}});if(next<0)break;centers.push(items[next][1]);consider(items[next][1],centers.length-1);}
const replacements=new Map(items.map(([key],i)=>[key,centers[assignment[i]]]));
for(const c of cells)if(c.edit){const t=replacements.get(c.key);for(let r=0;r<8;r++)pix.set(t.subarray(r*8,r*8+8),(c.y+r)*W+c.x);}
const crcTable=Uint32Array.from({length:256},(_,n)=>{for(let k=0;k<8;k++)n=n&1?0xedb88320^(n>>>1):n>>>1;return n>>>0;});
function chunk(type,data){const body=Buffer.concat([Buffer.from(type),data]);let crc=0xffffffff;for(const b of body)crc=crcTable[(crc^b)&255]^(crc>>>8);const out=Buffer.alloc(data.length+12);out.writeUInt32BE(data.length);body.copy(out,4);out.writeUInt32BE((crc^0xffffffff)>>>0,out.length-4);return out;}
const used=[...new Set(pix)].sort((a,b)=>a-b),mapping=new Map(used.map((v,i)=>[v,i])),rows=Buffer.alloc(H*(W/2+1));
for(let y=0;y<H;y++)for(let x=0;x<W;x+=2)rows[y*(W/2+1)+1+x/2]=mapping.get(pix[y*W+x])*16+mapping.get(pix[y*W+x+1]);
const hdr=Buffer.alloc(13);hdr.writeUInt32BE(W);hdr.writeUInt32BE(H,4);hdr[8]=4;hdr[9]=3;
fs.writeFileSync(path.join(here,'../../ready/KOF98-USAWharfStage.png'),Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',hdr),chunk('PLTE',Buffer.from(used.flatMap(i=>palette[i]))),chunk('IDAT',deflateSync(rows,{level:9})),chunk('IEND',Buffer.alloc(0))]));
console.log({colors:used.length,maximumTiles:centers.length});
