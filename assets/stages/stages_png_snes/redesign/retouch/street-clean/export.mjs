// Apply the clean asphalt direction with exact indexed pixels; no resampling.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {inflateSync,deflateSync} from 'node:zlib';
const here=path.dirname(fileURLToPath(import.meta.url));
const input=fs.readFileSync(path.join(here,'before.png'));
const chunks=[];let palette,hdr;
for(let pos=8;pos<input.length;){const n=input.readUInt32BE(pos),type=input.toString('ascii',pos+4,pos+8),data=input.subarray(pos+8,pos+8+n);if(type==='IHDR')hdr=Buffer.from(data);if(type==='PLTE')palette=Buffer.from(data);if(type==='IDAT')chunks.push(data);pos+=n+12;}
if(hdr.readUInt32BE(0)!==512||hdr.readUInt32BE(4)!==224||hdr[8]!==4||hdr[9]!==3||hdr[12]!==0)throw Error('Expected existing native 4-bit indexed export');
const rows=inflateSync(Buffer.concat(chunks)),pix=Buffer.alloc(512*224);
for(let y=0;y<224;y++){if(rows[y*257]!==0)throw Error('Expected unfiltered rows');for(let x=0;x<512;x++)pix[y*512+x]=(rows[y*257+1+(x>>1)]>>(x%2?0:4))&15;}
const before=Buffer.from(pix);
// Keep the white lane markings, manhole, crossing and pavement edge intact.
// A single existing warm gray gives a quiet plane without extra tile detail.
const asphalt=13;
for(let y=176;y<224;y++)for(let x=0;x<344;x++){
 if(x>=304&&y>=200)continue;
 const p=y*512+x,i=pix[p];
 if((x<304&&y>=184)||[11,12,13].includes(i))pix[p]=asphalt;
}
const used=[...new Set(pix)].sort((a,b)=>a-b),map=new Map(used.map((v,i)=>[v,i]));
for(let y=0;y<224;y++)for(let x=0;x<512;x+=2)rows[y*257+1+x/2]=map.get(pix[y*512+x])*16+map.get(pix[y*512+x+1]);
palette=Buffer.from(used.flatMap(i=>[...palette.subarray(i*3,i*3+3)]));
const crcTable=Uint32Array.from({length:256},(_,n)=>{for(let k=0;k<8;k++)n=n&1?0xedb88320^(n>>>1):n>>>1;return n>>>0;});
function chunk(type,data){const body=Buffer.concat([Buffer.from(type),data]);let crc=0xffffffff;for(const b of body)crc=crcTable[(crc^b)&255]^(crc>>>8);const out=Buffer.alloc(data.length+12);out.writeUInt32BE(data.length);body.copy(out,4);out.writeUInt32BE((crc^0xffffffff)>>>0,out.length-4);return out;}
const tiles=new Set();for(let y=0;y<224;y+=8)for(let x=0;x<512;x+=8){const t=Buffer.alloc(64);for(let r=0;r<8;r++)t.set(pix.subarray((y+r)*512+x,(y+r)*512+x+8),r*8);tiles.add(t.toString('hex'));}
if(tiles.size>512||used.length>15)throw Error('SNES budget exceeded');
fs.writeFileSync(path.join(here,'../../ready/KOF98-JpnStreetStage.png'),Buffer.concat([input.subarray(0,8),chunk('IHDR',hdr),chunk('PLTE',palette),chunk('IDAT',deflateSync(rows,{level:9})),chunk('IEND',Buffer.alloc(0))]));
const report={tiles:tiles.size,colors:used.length,changedPixels:pix.reduce((n,v,i)=>n+(v!==before[i]),0)};
fs.writeFileSync(path.join(here,'metrics.json'),JSON.stringify(report,null,2)+'\n');console.log(report);
