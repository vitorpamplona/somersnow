/* Gentle snowfall behind the hero. Draws one still frame when the viewer prefers reduced motion. */
export function snowfall(canvas){
const c=canvas;const x=c.getContext('2d');let W,H,flakes=[];
  const still=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function size(){const r=c.getBoundingClientRect();W=c.width=r.width*devicePixelRatio;H=c.height=r.height*devicePixelRatio;
    flakes=Array.from({length:Math.round(r.width/9)},()=>({x:Math.random()*W,y:Math.random()*H,r:(Math.random()*2.2+.8)*devicePixelRatio,s:Math.random()*.6+.3,d:Math.random()*Math.PI*2}));}
  function draw(){x.clearRect(0,0,W,H);x.fillStyle='rgba(255,255,255,.75)';flakes.forEach(f=>{x.beginPath();x.arc(f.x,f.y,f.r,0,7);x.fill();});}
  function tick(){flakes.forEach(f=>{f.y+=f.s*devicePixelRatio;f.d+=.01;f.x+=Math.sin(f.d)*.4;if(f.y>H){f.y=-5;f.x=Math.random()*W;}});draw();requestAnimationFrame(tick);}
  size();window.addEventListener('resize',size);if(still)draw();else tick();}
