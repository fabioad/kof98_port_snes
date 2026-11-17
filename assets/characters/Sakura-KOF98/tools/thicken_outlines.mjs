// Indexed SFF v1 contour conversion. No RGB quantization or palette changes.
import fs from 'node:fs';
import path from 'node:path';
const source=process.argv[2] || 'backups/Sakura.original.sff';
const dest=process.argv[3] || 'Sakura.sff';
const data=fs.readFileSync(source);
if(data.toString('ascii',0,11)!=='ElecbyteSpr' || data[15]!==1) throw Error('Expected SFF v1');
const count=data.readUInt32LE(20), first=data.readUInt32LE(24);
let offset=first, paletteOwner=-1; const records=[];
for(let i=0;i<count;i++){
 const header=Buffer.from(data.subarray(offset,offset+32));
 const size=header.readUInt32LE(4), same=header[18];
 if(size && (!same || paletteOwner<0)) paletteOwner++;
 records.push({header,body:Buffer.from(data.subarray(offset+32,offset+32+size)),paletteOwner});
 offset=header.readUInt32LE(0);
}
function decode(body){
 const prefix=body.toString('ascii',0,11)==='ElecbytePcx'?12:0;
 const h=body.subarray(prefix,prefix+128);
 if(h[0]!==10 || h[3]!==8 || h[65]!==1) throw Error('Expected indexed 8-bit PCX');
 const w=h.readUInt16LE(8)-h.readUInt16LE(4)+1, height=h.readUInt16LE(10)-h.readUInt16LE(6)+1, stride=h.readUInt16LE(66);
 const raw=Buffer.alloc(stride*height); let pos=prefix+128,j=0;
 while(j<raw.length){let v=body[pos++], n=1;if((v&192)===192){n=v&63;v=body[pos++];}if(!n || j+n>raw.length)throw Error('Invalid PCX run');raw.fill(v,j,j+n);j+=n;}
 const pixels=Buffer.alloc(w*height); for(let y=0;y<height;y++)raw.copy(pixels,y*w,y*stride,y*stride+w);
 return {prefix,h,w,height,pixels,tail:body.subarray(pos)};
}
function encode(f,pixels,w,height){
 const stride=(w+1)&~1, h=Buffer.from(f.h);h.writeUInt16LE(h.readUInt16LE(4)+w-1,8);h.writeUInt16LE(h.readUInt16LE(6)+height-1,10);h.writeUInt16LE(stride,66);
 const out=[];
 for(let y=0;y<height;y++){
  const row=Buffer.alloc(stride);pixels.copy(row,0,y*w,(y+1)*w);
  for(let x=0;x<stride;){const v=row[x];let n=1;while(x+n<stride&&n<63&&row[x+n]===v)n++;if(n>1||v>=192)out.push(192|n,v);else out.push(v);x+=n;}
 }
 return Buffer.concat([f.prefix?Buffer.from('ElecbytePcx\0\0','ascii'):Buffer.alloc(0),h,Buffer.from(out),f.tail]);
}
// Index ramps in Sakura's shared character palette: skin 1..5, red 6..8,
// cloth 10..15. Reuse their existing shadow colors in every ACT palette.
function ink(index){return index>=1&&index<=5?5:index>=6&&index<=8?8:15;}
let changed=0,linked=0,added=0; const groups={};
for(const r of records){
 const group=r.header.readUInt16LE(12);
 if(r.paletteOwner!==1 || group>=6000) continue;
 if(!r.body.length){linked++;continue;}
 const f=decode(r.body),w=f.w+2,h=f.height+2,p=Buffer.alloc(w*h);
 for(let y=0;y<f.height;y++)f.pixels.copy(p,(y+1)*w+1,y*f.w,(y+1)*f.w);
 // Add one 4-connected pixel outside the existing silhouette. Do not eat
 // highlights or ink interior facial details; diagonal corners remain crisp.
 for(let y=0;y<f.height;y++)for(let x=0;x<f.w;x++){
  const index=f.pixels[y*f.w+x];if(!index)continue;
  const cx=x+1,cy=y+1;
  for(const [dx,dy] of [[-1,0],[1,0],[0,-1],[0,1]]){
   const nx=cx+dx,ny=cy+dy,ox=nx-1,oy=ny-1;
   if(ox>=0&&ox<f.w&&oy>=0&&oy<f.height&&f.pixels[oy*f.w+ox])continue;
   const at=ny*w+nx, v=ink(index);
   if(!p[at]){p[at]=v;added++;}else if(v===15)p[at]=15;
  }
 }
 r.body=encode(f,p,w,h);r.header.writeInt16LE(r.header.readInt16LE(8)+1,8);r.header.writeInt16LE(r.header.readInt16LE(10)+1,10);
 changed++; groups[group]=(groups[group]||0)+1;
}
// Linked frames inherit their source's expanded image and need the same axis
// shift, irrespective of the palette owner recorded at the link's position.
for(const r of records)if(!r.body.length){
 let src=records[r.header.readUInt16LE(16)],seen=new Set();
 while(src&&!src.body.length){if(seen.has(src))throw Error('Cyclic link');seen.add(src);src=records[src.header.readUInt16LE(16)];}
 if(src&&src.paletteOwner===1&&src.header.readUInt16LE(12)<6000){r.header.writeInt16LE(r.header.readInt16LE(8)+1,8);r.header.writeInt16LE(r.header.readInt16LE(10)+1,10);}
}
let cursor=first; const parts=[data.subarray(0,first)];
for(let i=0;i<records.length;i++){const r=records[i];const next=cursor+32+r.body.length;r.header.writeUInt32LE(i===records.length-1?0:next,0);r.header.writeUInt32LE(r.body.length,4);parts.push(r.header,r.body);cursor=next;}
fs.writeFileSync(dest,Buffer.concat(parts));
const report={source,dest,entries:count,modifiedImages:changed,addedOutlinePixels:added,groups,policy:'One native pixel, four-connected outer contour; original indexed pixels and palette bytes retained; canvas and axes expanded by one pixel.'};
fs.mkdirSync('output',{recursive:true});fs.writeFileSync('output/conversion.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({...report,groups:Object.keys(groups).length}));
