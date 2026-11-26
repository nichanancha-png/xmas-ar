(() => {
  const canvas = document.querySelector('#tree');
  const ctx = canvas.getContext('2d', { alpha: true });
  const video = document.querySelector('#camera');
  const stage = document.querySelector('#stage');
  const intro = document.querySelector('#intro');
  const hud = document.querySelector('#hud');
  const toast = document.querySelector('#toast');
  let stream = null;
  let facing = 'environment';
  let started = false;
  let t = 0;
  let w = 0, h = 0, dpr = 1;

  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    w = window.innerWidth; h = window.innerHeight;
    canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
    canvas.style.width = `${w}px`; canvas.style.height = `${h}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  addEventListener('resize', resize, { passive: true }); resize();

  function message(text) {
    toast.textContent = text; toast.classList.add('show');
    clearTimeout(message.timer); message.timer = setTimeout(() => toast.classList.remove('show'), 3600);
  }

  async function openCamera() {
    if (!navigator.mediaDevices?.getUserMedia) throw new Error('กล้องต้องเปิดผ่านเว็บไซต์ HTTPS บน Safari หรือ Chrome');
    if (stream) stream.getTracks().forEach(track => track.stop());
    stream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: { facingMode: { ideal: facing }, width: { ideal: 1280 }, height: { ideal: 720 } }
    });
    video.srcObject = stream;
    await video.play();
    stage.classList.add('camera-on');
  }

  document.querySelector('#start').addEventListener('click', async () => {
    if (started) return;
    try {
      await openCamera();
      started = true; intro.hidden = true; hud.hidden = false;
      message('ต้นไม้กำลังหมุนอยู่กลางภาพกล้อง ✦');
    } catch (error) {
      started = true; intro.hidden = true; hud.hidden = false;
      message(error.name === 'NotAllowedError' ? 'เปิดสิทธิ์กล้องให้ Safari ใน Settings > Safari > Camera แล้วลองใหม่' : `${error.message || 'เปิดกล้องไม่ได้'} — กำลังแสดงฉากตัวอย่าง`);
    }
  });

  document.querySelector('#flip').addEventListener('click', async () => {
    facing = facing === 'environment' ? 'user' : 'environment';
    try { await openCamera(); } catch { message('สลับกล้องไม่สำเร็จ'); }
  });

  const palette = { green:'#24b76f', light:'#65e68f', dark:'#10764f', shade:'#0b493e', red:'#f15155', gold:'#ffca52', cream:'#fff2b5', blue:'#60d9ef', purple:'#b68cff' };
  const ornaments = [[-1,3,palette.red],[1,4,palette.gold],[0,6,palette.blue],[-2,7,palette.gold],[2,8,palette.red],[-1,10,palette.purple],[1,11,palette.gold],[0,13,palette.red]];

  function polygon(points, color) {
    ctx.beginPath(); ctx.moveTo(points[0][0], points[0][1]);
    for (let i=1;i<points.length;i++) ctx.lineTo(points[i][0], points[i][1]);
    ctx.closePath(); ctx.fillStyle=color; ctx.fill();
  }
  function project(x,y,z,angle,cx,base,unit) {
    const rx=x*Math.cos(angle)-z*Math.sin(angle), rz=x*Math.sin(angle)+z*Math.cos(angle);
    const depth=1+(rz*.018);
    return [cx+rx*unit*depth, base-y*unit*depth+rz*unit*.42];
  }
  function cube(x,y,z,size,angle,cx,base,unit,colors) {
    const q=[[-1,-1],[-1,1],[1,1],[1,-1]].map(([a,b])=>project(x+a*size/2,y,z+b*size/2,angle,cx,base,unit));
    const top=q.map(([px,py])=>[px,py-unit*size*.72]);
    polygon([q[0],q[1],top[1],top[0]],colors[0]);
    polygon([q[1],q[2],top[2],top[1]],colors[1]);
    polygon([top[0],top[1],top[2],top[3]],colors[2]);
  }
  function treeFrame(now) {
    requestAnimationFrame(treeFrame);
    const delta = Math.min(45, now - (treeFrame.last || now)); treeFrame.last = now;
    if (started) t += delta * .0003;
    ctx.clearRect(0,0,w,h);
    const cx=w*.5, base=h*.76, unit=Math.min(w*.065,h*.039);
    const angle=t;

    // Soft pixel halo and floating snow
    const glow=ctx.createRadialGradient(cx,base-unit*7,unit,cx,base-unit*7,unit*10);
    glow.addColorStop(0,'#63f4c22b'); glow.addColorStop(1,'#63f4c200');
    ctx.fillStyle=glow; ctx.fillRect(0,0,w,h);
    for(let i=0;i<20;i++){
      const sx=(i*79+Math.sin(t*2+i)*13)%w, sy=(i*131+now*.012*(1+i%3))%h;
      ctx.fillStyle=i%4===0?'#d9fff9bb':'#c9fff55c'; ctx.fillRect(sx,sy,2,2);
    }

    // Golden star, in chunky 8-bit facets
    const starY=base-unit*17;
    const flicker=.82+Math.sin(t*5)*.12;
    ctx.save();ctx.translate(cx,starY);ctx.scale(1,flicker);
    ctx.fillStyle='#ffd45e33';ctx.fillRect(-unit*3,-unit*3,unit*6,unit*6);
    polygon([[0,-unit*2],[unit*.55,-unit*.55],[unit*2,0],[unit*.55,unit*.55],[0,unit*2],[-unit*.55,unit*.55],[-unit*2,0],[-unit*.55,-unit*.55]],palette.gold);
    ctx.fillStyle=palette.cream;ctx.fillRect(-unit*.38,-unit*.7,unit*.76,unit*1.15);ctx.restore();

    // Layered voxel branches: each tier narrows toward the top.
    for(let tier=0;tier<4;tier++){
      const top=3+tier*3.35, bottom=top+4.4, radius=3.45-tier*.55;
      for(let row=0;row<5;row++){
        const y=top+row*.82, r=radius*(1-row/6.3);
        for(let x=-Math.ceil(r);x<=Math.ceil(r);x++){
          for(let z=-Math.ceil(r);z<=Math.ceil(r);z++){
            if(x*x+z*z>r*r) continue;
            const front=x*Math.sin(angle)+z*Math.cos(angle)>-.45;
            const side=x*Math.cos(angle)-z*Math.sin(angle)>0;
            const shade=front?(side?palette.light:palette.green):(side?palette.green:palette.dark);
            cube(x,y,z,.94,angle,cx,base,unit,[side?palette.dark:palette.shade,shade,front?palette.light:palette.green]);
          }
        }
      }
    }
    // Trunk, chunky presents and baubles
    for(let y=0;y<3;y++) for(let x=-1;x<=1;x++) for(let z=-1;z<=1;z++) cube(x,y,z,.95,angle,cx,base,unit,['#8b4e31','#ba7040','#d89954']);
    for(const [x,y,color] of ornaments){
      const p=project(x,y,2.95,angle,cx,base,unit);ctx.fillStyle=color;ctx.fillRect(Math.round(p[0]/4)*4,Math.round(p[1]/4)*4,unit*.55,unit*.55);
      ctx.fillStyle='#fff7c9';ctx.fillRect(Math.round(p[0]/4)*4,Math.round(p[1]/4)*4,unit*.16,unit*.16);
    }
    // pixel gift boxes at the base
    const presents=[[-3.5,0,1.8,palette.red],[3.3,0,1.3,palette.blue],[0,0,-3,palette.purple]];
    for(const [x,y,z,color] of presents){
      cube(x,y,z,2.3,angle,cx,base,unit,[color,color==palette.red?'#b63445':'#397fbd','#ffc969']);
      const p=project(x,y+1.1,z,angle,cx,base,unit);ctx.fillStyle='#fff0a9';ctx.fillRect(p[0]-2,p[1],4,unit*.8);
    }
    // subtle projected shadow
    ctx.fillStyle='#70ffd01b';ctx.beginPath();ctx.ellipse(cx,base+unit*.2,unit*7,unit*1.15,0,0,Math.PI*2);ctx.fill();
  }
  requestAnimationFrame(treeFrame);
})();
