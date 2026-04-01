#!/usr/bin/env node
import readline from "node:readline";

const w = process.stdout.columns || 80;
const h = Math.max(24, (process.stdout.rows || 24) - 2);

const stars = Array.from({length: Math.floor((w*h)*0.02)}, () => ({
  x: Math.random()*w, y: Math.random()*h, z: Math.random()*1+0.2
}));

readline.emitKeypressEvents(process.stdin);
if (process.stdin.isTTY) process.stdin.setRawMode(true);

process.stdout.write("\x1b[?25l"); // hide cursor
let running = true;

process.stdin.on("keypress", (_str, key)=>{
  if (key.name === "q" || (key.ctrl && key.name==="c")) running=false;
});

function draw(){
  let buf = [];
  for (let y=0;y<h;y++){
    let row = "";
    for (let x=0;x<w;x++) row+=" ";
    buf.push(row.split(""));
  }
  for (const s of stars){
    const sx = (s.x/s.z)|0, sy=(s.y/s.z)|0;
    if (sx>=0 && sy>=0 && sx<w && sy<h){
      const b = 1.2 - s.z;
      const ch = b>0.9 ? "✶" : b>0.6 ? "*" : ".";
      buf[sy][sx] = ch;
    }
    s.z -= 0.02; if (s.z<=0.1){ s.x=Math.random()*w; s.y=Math.random()*h; s.z=1; }
  }
  process.stdout.write("\x1b[H");
  for (let y=0;y<h;y++) process.stdout.write(buf[y].join("")+"\n");
  process.stdout.write(" ASCII Starfield — press 'q' to quit \n");
}

async function loop(){
  process.stdout.write("\x1b[2J\x1b[H");
  const tick = ()=> new Promise(r=> setTimeout(r, 33));
  while(running){ draw(); await tick(); }
  process.stdout.write("\x1b[?25h");
  process.exit(0);
}
loop();