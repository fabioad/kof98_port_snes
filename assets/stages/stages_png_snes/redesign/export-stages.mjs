// Export generated artwork to the existing SNES background budget.
// Requires Node.js and ImageMagick. No changes to the game's converter.
import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {deflateSync} from 'node:zlib';
import {fileURLToPath} from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const manifest = JSON.parse(fs.readFileSync(path.join(here, 'manifest.json')));
const W = 512, H = 224, LIMIT = 512;
// Keep large flat areas close in value without changing any pixel indices or tiles.
// These RGB values are exact SNES RGB555 expansions.
const paletteSoftening = {
  'KOF98-JpnStreetStage.png': {8:[148,115,66], 12:[99,90,74], 13:[115,107,90], 14:[165,148,99]},
  'KOF98-USAWharfStage.png': {7:[8,58,123], 11:[16,74,140]},
  'KOF98-USAWharfStage-B.png': {10:[156,16,33], 11:[165,25,41], 12:[197,33,49]},
};
const crcTable = Uint32Array.from({length:256}, (_, n) => {
  for (let k=0;k<8;k++) n=(n&1)?0xedb88320^(n>>>1):n>>>1;
  return n>>>0;
});
function chunk(type, data) {
  const body=Buffer.concat([Buffer.from(type),data]);
  let crc=0xffffffff;
  for(const b of body) crc=crcTable[(crc^b)&255]^(crc>>>8);
  const out=Buffer.alloc(data.length+12);
  out.writeUInt32BE(data.length); body.copy(out,4);
  out.writeUInt32BE((crc^0xffffffff)>>>0,out.length-4); return out;
}
function png(pix,palette) {
  // Dense indices are required by build_stage()'s lossless palette path.
  const used=[...new Set(pix)].sort((a,b)=>a-b);
  const mapping=new Map(used.map((v,i)=>[v,i]));
  const rows=Buffer.alloc(H*(W/2+1));
  for(let y=0;y<H;y++) for(let x=0;x<W;x+=2)
    rows[y*(W/2+1)+1+x/2]=(mapping.get(pix[y*W+x])<<4)|mapping.get(pix[y*W+x+1]);
  const hdr=Buffer.alloc(13);hdr.writeUInt32BE(W);hdr.writeUInt32BE(H,4);hdr[8]=4;hdr[9]=3;
  return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',hdr),
    chunk('PLTE',Buffer.from(used.flatMap(i=>palette[i]))),chunk('IDAT',deflateSync(rows,{level:9})),chunk('IEND',Buffer.alloc(0))]);
}
function tileImage(pix) {
  const pool=[],counts=[],map=[],lookup=new Map();
  for(let y=0;y<H;y+=8) for(let x=0;x<W;x+=8) {
    const t=Buffer.alloc(64);
    for(let j=0;j<8;j++) t.set(pix.subarray((y+j)*W+x,(y+j)*W+x+8),j*8);
    const key=t.toString('hex'); let i=lookup.get(key);
    if(i===undefined){i=pool.length;lookup.set(key,i);pool.push(t);counts.push(0);}
    counts[i]++;map.push(i);
  }
  return {pool,counts,map};
}
function compressTiles(pix,palette) {
  const {pool,counts,map}=tileImage(pix),n=pool.length;
  if(n<=LIMIT)return {pix,before:n,after:n};
  const dist=palette.map(a=>palette.map(b=>
    0.30*(a[0]-b[0])**2+0.59*(a[1]-b[1])**2+0.11*(a[2]-b[2])**2));
  const weights=Float64Array.from({length:64},(_,p)=>
    (p%8===0||p%8===7||p<8||p>=56)?1.5:1);
  function error(a,b,best=Infinity) {
    let s=0;
    for(let p=0;p<64;p++) {s+=dist[a[p]][b[p]]*weights[p];if(s>best)return s;}
    return s;
  }
  // Weighted farthest-point initialization keeps rare strong contours.
  const centers=[],nearest=new Float64Array(n).fill(Infinity);
  let next=counts.indexOf(Math.max(...counts));
  for(let k=0;k<LIMIT;k++) {
    const c=Buffer.from(pool[next]);centers.push(c);
    let score=-1;
    for(let i=0;i<n;i++) {
      nearest[i]=Math.min(nearest[i],error(pool[i],c,nearest[i]));
      const s=nearest[i]*Math.sqrt(counts[i]);
      if(s>score){score=s;next=i;}
    }
  }
  const assignment=new Uint16Array(n);
  for(let iteration=0;iteration<7;iteration++) {
    let changed=0;
    const sums=Array.from({length:LIMIT},()=>new Float64Array(64*3));
    const totals=new Float64Array(LIMIT);
    for(let i=0;i<n;i++) {
      let best=Infinity,cluster=0;
      for(let c=0;c<LIMIT;c++) {
        const e=error(pool[i],centers[c],best);
        if(e<best){best=e;cluster=c;}
      }
      if(assignment[i]!==cluster)changed++;
      assignment[i]=cluster;totals[cluster]+=counts[i];
      for(let p=0;p<64;p++) for(let ch=0;ch<3;ch++)
        sums[cluster][p*3+ch]+=palette[pool[i][p]][ch]*counts[i];
    }
    if(iteration===6||(!changed&&iteration>0))break;
    for(let c=0;c<LIMIT;c++) {
      if(!totals[c])continue;
      for(let p=0;p<64;p++) {
        const r=sums[c][p*3]/totals[c],g=sums[c][p*3+1]/totals[c],b=sums[c][p*3+2]/totals[c];
        let best=Infinity,index=0;
        palette.forEach((rgb,i)=>{
          const d=.30*(r-rgb[0])**2+.59*(g-rgb[1])**2+.11*(b-rgb[2])**2;
          if(d<best){best=d;index=i;}
        });
        centers[c][p]=index;
      }
    }
  }
  const out=Buffer.alloc(W*H);
  map.forEach((i,t)=>{
    const tile=centers[assignment[i]],x=(t%64)*8,y=Math.floor(t/64)*8;
    for(let j=0;j<8;j++) out.set(tile.subarray(j*8,j*8+8),(y+j)*W+x);
  });
  return {pix:out,before:n,after:tileImage(out).pool.length};
}

const selected=process.argv[2];
fs.mkdirSync(path.join(here,'ready'),{recursive:true});
const report=[];
for(const item of manifest.filter(i=>!selected||i.name===selected)) {
  const raw=execFileSync('convert',[item.source,'-alpha','off','-filter','Box','-resize','512x224!',
    '+dither','-colors','15','-depth','8','RGB:-'],{maxBuffer:4*1024*1024});
  if(raw.length!==W*H*3)throw Error('Incorrect dimensions');
  const pix=Buffer.alloc(W*H),palette=[],lookup=new Map();
  for(let i=0;i<pix.length;i++) {
    // SNES stores five bits per channel; expanded values match its display.
    const rgb=[0,1,2].map(c=>Math.round(Math.round(raw[i*3+c]*31/255)*255/31));
    const key=rgb.join(',');let index=lookup.get(key);
    if(index===undefined){index=palette.length;palette.push(rgb);lookup.set(key,index);}
    pix[i]=index;
  }
  if(palette.length>15)throw Error('Palette exceeds 15 colors');
  const result=compressTiles(pix,palette);
  if(result.after>LIMIT)throw Error('Tile budget exceeded');
  for(const [index,rgb] of Object.entries(paletteSoftening[item.name]||{}))
    palette[Number(index)]=rgb;
  const output=png(result.pix,palette);
  fs.writeFileSync(path.join(here,'ready',item.name),output);
  const row={file:item.name,width:W,height:H,colors:new Set(result.pix).size,
    tilesBefore:result.before,tiles:result.after,chrBytes:result.after*32,
    mapBytes:4096,paletteBytes:32,pngBytes:output.length};
  report.push(row);console.log(JSON.stringify(row));
}
fs.writeFileSync(path.join(here,selected?'sample-metrics.json':'metrics.json'),JSON.stringify(report,null,2)+'\n');
