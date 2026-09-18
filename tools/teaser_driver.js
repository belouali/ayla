/* Teaser driver: deterministic timeline rendered frame by frame on top of the game engine. */
loopBody=function(){};
const FPS=30, W=1920, H=1080;
document.body.classList.add("teaser");
const st=document.createElement("style"); st.textContent="body.teaser > :not(#gl):not(#out){display:none!important} #out{position:fixed;inset:0;width:100%;height:100%;z-index:99;background:#000} #gl{position:fixed;left:0;top:0;width:1920px;height:1080px;z-index:1}"; document.head.appendChild(st);
renderer.setPixelRatio(1); renderer.setSize(W,H,false); camera.aspect=W/H; camera.fov=50; camera.updateProjectionMatrix();
const out=document.createElement("canvas"); out.id="out"; out.width=W; out.height=H; document.body.appendChild(out); const ctx=out.getContext("2d");
app.innerHTML=""; try{ Music.set=()=>{}; Music.sfx=()=>{}; }catch(e){}

/* ---------- timeline ---------- */
const TL={ city:[0,9.8], door:[9.8,16.9], search:[16.9,27.2], traces:[27.2,37.6], fl:[37.6,52.8], lab:[52.8,61.0], montage:[61.0,74.6], final:[74.6,82.9], black:[82.9,83.5], title:[83.5,87.5], team:[87.5,92] };
const TOTAL=92;
const CAPTIONS=[
  {t:0.7,d:8.5,who:"",text:"En 2170, à Chroma, FriendLoop connaît tout de nos habitudes. Il anticipe nos déplacements, nos besoins, nos choix."},
  {t:14.9,d:2.0,who:"Ayla",text:"Mais… c'est chez moi."},
  {t:24.2,d:2.9,who:"Ayla",text:"Ils étaient là hier…"},
  {t:33.9,d:2.5,who:"Ayla",text:"Vous connaissez Luno et Kio ?"},
  {t:36.4,d:1.4,who:"Le passant",text:"Qui ?"},
  {t:38.2,d:5.6,who:"FriendLoop",text:"Les données disponibles ne permettent pas d'établir leur présence actuelle."},
  {t:44.1,d:3.4,who:"Ayla",text:"Vous êtes en train de me dire qu'ils n'ont jamais existé ?"},
  {t:47.7,d:5.0,who:"FriendLoop",text:"Je ne dispose pas de suffisamment d'éléments pour confirmer cette information."},
  {t:55.0,d:5.8,who:"",text:"« Si tu lis ceci, ne fais pas confiance uniquement à ce que FriendLoop te montre. »"},
  {t:61.3,d:6.1,who:"",text:"Pour retrouver les traces de ses parents, Ayla devra comprendre comment FriendLoop apprend…"},
  {t:67.8,d:6.9,who:"",text:"…et jusqu'où une ville peut aller lorsqu'elle confie ses décisions à un système qu'elle ne questionne plus."},
  {t:75.2,d:3.7,who:"FriendLoop",text:"Ayla, je peux t'aider à retrouver tes parents."},
  {t:79.2,d:3.7,who:"Ayla",text:"Et si c'était toi qui les avais fait disparaître ?"}
];
const ease=k=>k<.5?2*k*k:-1+(4-2*k)*k; const clamp=(v,a,b)=>Math.max(a,Math.min(b,v)); const lerp=(a,b,k)=>a+(b-a)*k;
const fadeIO=(t,a,d,f=.35)=>{ if(t<a||t>a+d) return 0; return Math.min(1,(t-a)/f,(a+d-t)/f); };

/* ---------- scene builders ---------- */
let curScene=null, extra={}, lastT=0;
function resetPlayer(){ player.visible=true; player.scale.set(1,1,1); player.position.set(0,0,0); player.rotation.set(0,0,0); const u=player.userData; u.arms.forEach(a=>{ a.rotation.set(0,0,0); }); u.legs.forEach(l=>l.rotation.set(0,0,0)); u.body.rotation.x=0; }
function addDrones(n, zmin, zmax){ const list=[]; const dm=new THREE.MeshStandardMaterial({color:lin(0x1B2846), emissive:lin(0x5EA8FF), emissiveIntensity:.9}); for(let i=0;i<n;i++){ const d=new THREE.Group(); d.add(new THREE.Mesh(new THREE.SphereGeometry(.45,14,10),dm)); const r=new THREE.Mesh(new THREE.TorusGeometry(.8,.06,8,22),dm); r.rotation.x=Math.PI/2; d.add(r); const l=new THREE.Mesh(new THREE.SphereGeometry(.12,6,6), new THREE.MeshBasicMaterial({color:0xFF6060})); l.position.y=-.4; d.add(l); d.userData={x:(Math.random()-.5)*30, y:6+Math.random()*14, z0:zmin+Math.random()*(zmax-zmin), sp:6+Math.random()*10, ph:Math.random()*6}; world.add(d); list.push(d); } return list; }
function makeCore(x,y,z,R){ const g=new THREE.Group(); const c=new THREE.Mesh(new THREE.SphereGeometry(R,32,24), new THREE.MeshStandardMaterial({color:lin(0x0E2A55), emissive:lin(0x3D8BFF), emissiveIntensity:1.2, roughness:.3})); g.add(c); const halo=new THREE.Mesh(new THREE.SphereGeometry(R*1.6,24,18), new THREE.MeshBasicMaterial({color:0x5EA8FF, transparent:true, opacity:.12, depthWrite:false})); g.add(halo); const rings=[]; [1.35,1.8,2.3].forEach((k,i)=>{ const r=new THREE.Mesh(new THREE.TorusGeometry(R*k,R*.035,10,80), new THREE.MeshBasicMaterial({color:0x8FC4FF, transparent:true, opacity:.7})); r.rotation.x=Math.PI/2+.3*i; r.rotation.z=.4*i; g.add(r); rings.push(r); }); g.userData.rings=rings; g.position.set(x,y,z); world.add(g); const L=new THREE.PointLight(0x5EA8FF,2.2,R*12); L.position.set(x,y,z); world.add(L); return g; }
function doorSet(z){ const g=new THREE.Group(); const wallM=new THREE.MeshStandardMaterial({color:lin(0x1A2238), roughness:.9}); const wall=new THREE.Mesh(new THREE.BoxGeometry(1.2,6,9), wallM); wall.position.set(0,3,0); g.add(wall); const frame=new THREE.Mesh(new THREE.BoxGeometry(.4,3.4,2.2), new THREE.MeshStandardMaterial({color:lin(0x1B2846), emissive:lin(0x5EA8FF), emissiveIntensity:.5, roughness:.6})); frame.position.set(-.5,1.7,0); g.add(frame); const door=new THREE.Mesh(new THREE.BoxGeometry(.2,3,1.8), new THREE.MeshStandardMaterial({color:lin(0x3C4A6E), roughness:.5, metalness:.3})); door.position.set(-.55,1.5,0); g.add(door); const panel=new THREE.Mesh(new THREE.PlaneGeometry(.55,.75), new THREE.MeshStandardMaterial({color:lin(0x0A1020), emissive:lin(0x5EA8FF), emissiveIntensity:1})); panel.position.set(-.71,1.55,1.5); panel.rotation.y=-Math.PI/2; g.add(panel); g.userData.panel=panel; const lamp=new THREE.Mesh(new THREE.SphereGeometry(.12,8,6), neonMat(0xFFE2B8)); lamp.position.set(-.7,3.6,0); g.add(lamp); const win=new THREE.Mesh(new THREE.PlaneGeometry(1.4,1.1), new THREE.MeshStandardMaterial({color:lin(0x0A1020), emissive:lin(0xFFD9A0), emissiveIntensity:.35})); win.position.set(-.61,3.6,-3); win.rotation.y=-Math.PI/2; g.add(win); g.position.set(9.3,0,z); world.add(g); return g; }
function holoScreen(x,y,z,w,h,color){ const m=new THREE.Mesh(new THREE.PlaneGeometry(w,h), new THREE.MeshBasicMaterial({color:0xFFFFFF, map:screenTex(color===0x6FE3D8?"lab":"city",1), transparent:true, opacity:.75, side:THREE.DoubleSide, depthWrite:false})); m.position.set(x,y,z); world.add(m); const fr=new THREE.Mesh(new THREE.BoxGeometry(w+.1,h+.1,.03), new THREE.MeshBasicMaterial({color, transparent:true, opacity:.55})); fr.position.set(x,y,z-.02); world.add(fr); const L=new THREE.PointLight(color,1.6,12); L.position.set(x,y,z+1); world.add(L); return m; }
function build(scene){
  curScene=scene; extra={}; resetPlayer(); alarmLight.intensity=0;
  if(scene==="city"){ buildRun("city",260); player.visible=false; extra.drones=addDrones(14,-200,20); }
  else if(scene==="door"){ buildRun("city",260); extra.door=doorSet(-30); player.position.set(7.2,.3,-30); player.rotation.y=Math.PI/2; player.userData.arms[1].rotation.x=-1.5; }
  else if(scene==="search"){ clearWorld(); applyTheme("city"); world.add(skyDome("city")); const g=new THREE.Mesh(new THREE.CircleGeometry(30,40), new THREE.MeshStandardMaterial({color:lin(0x0B1220), roughness:1})); g.rotation.x=-Math.PI/2; world.add(g); extra.screen=holoScreen(0,2.2,-2.2,4.2,2.6,0x5EA8FF); player.position.set(0,0,0); player.rotation.y=Math.PI; }
  else if(scene==="traces"){ buildRun("city",260); extra.drones=addDrones(8,-200,0);
    const passant={kind:"passant",skin:0xC98A5B,hair:0x24201C,style:"short",top:0x4A4A58,topTex:"weave",topTexBase:"#4A4A58",topTexAccent:"#33333E",longSleeve:true,legs:0x2A2A34,shin:0x2A2A34,shoe:0x1A1A1A,iris:0x3B2A1A,collar:0xD9CDB8,scarf:0x6B5A46,bigNose:true,scale:1.09};
    const p=human(passant); p.position.set(0.95,0,-78); p.rotation.y=0; world.add(p); extra.passer=p;
    const w1={kind:"w1",skin:0xE9C7A6,hair:0x8A6A3E,style:"bob",top:0x7B4A9A,topTex:"weave",topTexBase:"#7B4A9A",topTexAccent:"#5A3570",longSleeve:true,legs:0x2B3A55,shin:0x2B3A55,shoe:0xF5F5F5,iris:0x3E7D3A,lashes:true,scale:1.0};
    const w2={kind:"w2",skin:0x8D5A3A,hair:0x1A1A1A,style:"short",top:0x2E5E8A,topTex:"stripes",topTexBase:"#2E5E8A",topTexAccent:"#1B3A58",longSleeve:true,legs:0x3E4A3C,shin:0x3E4A3C,shoe:0x2E2E2E,iris:0x2A1A0A,scale:1.05};
    extra.walkers=[[w1,-7.7,-58,1],[w2,7.7,-88,-1]].map(([o,x,z,dir])=>{ const f=human(o); f.position.set(x,.3,z); f.rotation.y=dir>0?0:Math.PI; world.add(f); f.userData.dir=dir; f.userData.z0=z; return f; });
    level.obs.forEach(o=>{ if(o.userData.z<-56&&o.userData.z>-88) o.visible=false; }); level.frags.forEach(f=>{ if(f.userData.z<-56&&f.userData.z>-88) f.visible=false; });
    const dm=new THREE.MeshStandardMaterial({color:lin(0x1B2846), emissive:lin(0x5EA8FF), emissiveIntensity:.9}); const wd=new THREE.Group(); wd.add(new THREE.Mesh(new THREE.SphereGeometry(.45,14,10),dm)); const wr=new THREE.Mesh(new THREE.TorusGeometry(.8,.06,8,22),dm); wr.rotation.x=Math.PI/2; wd.add(wr); const wl=new THREE.Mesh(new THREE.SphereGeometry(.1,6,6), new THREE.MeshBasicMaterial({color:0xFF6060})); wl.position.y=-.4; wd.add(wl); wd.position.set(5.2,3.6,-76.5); world.add(wd); extra.watch=wd;
    const lamp=new THREE.PointLight(0xFFE2B8,1.0,15); lamp.position.set(-2.4,3.4,-70.4); world.add(lamp); }
  else if(scene==="fl"){ buildRun("city",260); world.children.filter(o=>o.geometry&&o.geometry.parameters&&o.geometry.parameters.width===21).forEach(o=>world.remove(o)); extra.core=makeCore(0,30,-70,9); player.position.set(0,0,-30); player.rotation.y=Math.PI; extra.drones=addDrones(10,-160,-40); }
  else if(scene==="lab"){ buildRun("lab",260); extra.screen=holoScreen(2.6,1.9,-60,2.4,1.6,0x6FE3D8); extra.screen.visible=false; extra.screen.parent&&(extra.screenLight=world.children[world.children.length-1]); player.position.set(0,0,-52); player.rotation.y=Math.PI; }
  else if(scene==="final"){ clearWorld(); applyTheme("city"); world.add(skyDome("city")); const g=new THREE.Mesh(new THREE.CircleGeometry(30,40), new THREE.MeshStandardMaterial({color:lin(0x0B1220), roughness:1})); g.rotation.x=-Math.PI/2; world.add(g); extra.core=makeCore(0,4.5,-14,3.2); player.position.set(0,0,0); player.rotation.y=Math.PI; }
  else if(scene==="m_lab"){ buildRun("lab",260); player.position.set(0,0,-80); player.rotation.y=Math.PI; }
  else if(scene==="m_surv"){ buildRun("city",260); extra.drones=addDrones(20,-120,10); player.visible=false; }
  else if(scene==="m_school"){ buildDome(); }
  else if(scene==="m_citizens"){ buildRun("city",260); const pz=level.plazaZ; ["kade","elio2","kid4"].forEach((k,i)=>{ const f=figure(k); f.position.set(-4+i*4,0,pz-5+(i%2)*2); f.rotation.y=Math.PI*.1*(i-1); world.add(f); extra["n"+i]=f; }); player.position.set(0,0,pz+3); player.rotation.y=Math.PI; extra.pz=pz; }
  else if(scene==="m_decision"){ buildRun("city",260); const pz=level.plazaZ; ["A","B"].forEach((k,i)=>{ const x=i?4.5:-4.5; const frame=new THREE.Mesh(new THREE.TorusGeometry(2.2,.18,10,32), new THREE.MeshStandardMaterial({color:0x1B2846, emissive:0x5EA8FF, emissiveIntensity:.8})); frame.position.set(x,2.2,pz-9); world.add(frame); const disc=new THREE.Mesh(new THREE.CircleGeometry(2,32), new THREE.MeshBasicMaterial({color:0x5EA8FF, transparent:true, opacity:.2, side:THREE.DoubleSide})); disc.position.copy(frame.position); world.add(disc); extra["d"+i]=frame; }); player.position.set(0,0,pz+1); player.rotation.y=Math.PI; extra.pz=pz; }
  else if(scene==="m_fl"){ clearWorld(); applyTheme("city"); world.add(skyDome("city")); extra.core=makeCore(0,0,0,6); player.visible=false; }
  else { clearWorld(); player.visible=false; }
}
const MONTAGE=[["m_lab",61.0],["search",62.7],["m_surv",64.4],["m_school",66.1],["m_citizens",67.8],["m_decision",69.5],["m_fl",71.2],["m_decision",72.9]];
function sceneAt(t){ for(const k in TL){ const [a,b]=TL[k]; if(t>=a&&t<b){ if(k==="montage"){ let s=MONTAGE[0][0]; MONTAGE.forEach(m=>{ if(t>=m[1]) s=m[0]; }); return s; } return k; } } return "team"; }
let lastSceneKey=null;
function step(t){
  const dt=1/FPS; const s=sceneAt(t); const key=s+"|"+(s==="m_decision"&&t>=72.9?"2":"");
  if(key!==lastSceneKey){ build(s); lastSceneKey=key; }
  const u=player.userData;
  if(s==="city"){ const k=ease(clamp((t-TL.city[0])/9.8,0,1)); camera.position.set(lerp(22,3,k), lerp(48,7,k), lerp(70,12,k)); camera.lookAt(lerp(-10,0,k), lerp(6,3,k), lerp(-60,-40,k)); extra.drones.forEach(d=>{ const z=d.userData.z0+((t*d.userData.sp)%220); d.position.set(d.userData.x, d.userData.y+Math.sin(t*2+d.userData.ph)*.6, z-200+((z+200)%220>220?0:0)); d.position.z=-200+(((d.userData.z0+200)+t*d.userData.sp)%220); d.rotation.y=t; }); }
  else if(s==="door"){ const k=clamp((t-TL.door[0])/7.1,0,1); camera.position.set(3.4+k*1.0,2.2,-30+3.0-k*.5); camera.lookAt(8.6,1.8,-30.2); animFigure(player,dt,"idle"); u.arms[1].rotation.x=-1.5; const flash=(t>11&&t<11.4)||(t>13&&t<13.4); extra.door.userData.panel.material.emissive.copy(lin(flash?0xE06060:(t>11?0xE06060:0x5EA8FF))); extra.door.userData.panel.material.emissiveIntensity=flash?2.2:1; }
  else if(s==="search"){ camera.position.set(3.2,2.4,2.2); camera.lookAt(0,1.8,-1.5); animFigure(player,dt,"idle"); u.arms[0].rotation.x=-1.1; u.arms[1].rotation.x=-.9; }
  else if(s==="traces"){ const t0=t-TL.traces[0]; const RUN=5.6, ZSTOP=-70;
    const pr=clamp(t0/RUN,0,1), e=ease(pr); const z=-10+(ZSTOP+10)*e; const px=Math.sin(t0*1.2)*2.5*(1-e);
    player.position.set(px,0,z); player.rotation.y=Math.PI;
    animFigure(player,dt, pr<.88?"run":(pr<1?"walk":"idle"));
    if(pr>=1){ const sp=(t>33.85&&t<36.0); player.userData.arms[0].rotation.x=-.25-(sp?Math.sin((t-33.85)*4)*.18:0); player.userData.arms[1].rotation.x=-.25+(sp?Math.sin((t-33.85)*4)*.18:0); player.userData.arms[0].rotation.z=.18; player.userData.arms[1].rotation.z=-.18; if(sp) player.position.y=Math.abs(Math.sin((t-33.85)*3))*.03; }
    const M=extra.passer;
    if(M){ if(t0<RUN){ M.position.z=Math.min(-73.2,-78+t0*.86); M.rotation.y=0; animFigure(M,dt,"walk"); }
      else if(t<36.95){ M.position.z=-73.2; M.rotation.y=-.12; animFigure(M,dt,"idle"); }
      else { M.rotation.y=Math.PI*.92; M.position.z-=dt*2.1; animFigure(M,dt,"walk"); }
      if(t>35.95&&t<37.1){ const k=Math.sin(clamp((t-35.95)/1.15,0,1)*Math.PI); M.userData.arms[0].rotation.z=.2+k*.75; M.userData.arms[1].rotation.z=-.2-k*.75; M.userData.arms[0].rotation.x=-k*.45; M.userData.arms[1].rotation.x=-k*.45; M.userData.head.rotation.z=k*.06; if(t<36.9) M.userData.head.rotation.y=Math.sin(t*2)*.05; } }
    if(extra.walkers) extra.walkers.forEach(f=>{ f.position.z=f.userData.z0+f.userData.dir*t0*1.7; animFigure(f,dt,"walk"); });
    if(extra.watch){ extra.watch.position.y=3.6+Math.sin(t*1.8)*.16; extra.watch.rotation.y+=dt*.7; }
    const camA=new THREE.Vector3(px*.6,4.6,z+9.5), tgtA=new THREE.Vector3(px*.6,1.6,z-8);
    const camB=new THREE.Vector3(-4.9,2.25,-70.1), tgtB=new THREE.Vector3(.5,1.55,-71.9);
    const k2=ease(clamp((t0-4.8)/1.5,0,1));
    camera.position.lerpVectors(camA,camB,k2); camera.lookAt(new THREE.Vector3().lerpVectors(tgtA,tgtB,k2));
    if(extra.drones) extra.drones.forEach(d=>{ d.position.set(d.userData.x, d.userData.y, -200+(((d.userData.z0+200)+t*d.userData.sp)%220)); }); }
  else if(s==="fl"){ const k=clamp((t-TL.fl[0])/15.2,0,1); camera.position.set(lerp(-3.5,2.5,k),lerp(2.4,3.2,k),lerp(-21,-22,k)); camera.lookAt(0,lerp(12,16,k),-70); animFigure(player,dt,"idle"); extra.core.userData.rings.forEach((r,i)=>{ r.rotation.z+=dt*(.3+i*.15); r.rotation.x+=dt*.1; }); extra.core.children[0].material.emissiveIntensity=1.1+Math.sin(t*3)*.3; if(extra.drones) extra.drones.forEach(d=>{ d.position.set(d.userData.x, d.userData.y+8, -200+(((d.userData.z0+200)+t*d.userData.sp)%220)); }); }
  else if(s==="lab"){ const t0=t-TL.lab[0]; const z=-52-Math.min(t0,3)*2.2; player.position.set(0,0,z); player.rotation.y=Math.PI; animFigure(player,dt,t0<3?"walk":"idle"); if(t0>=3){ player.rotation.y=Math.PI*.6; } camera.position.set(-3.5,2.6,z+4); camera.lookAt(1.5,1.8,z-2); if(t>54.0){ extra.screen.visible=true; extra.screen.material.opacity=.25+Math.sin(t*6)*.08; } }
  else if(s==="final"){ const k=clamp((t-TL.final[0])/8.3,0,1); camera.position.set(lerp(-2.5,-1.2,k),2.2,lerp(4.5,3,k)); camera.lookAt(0,3,-12); animFigure(player,dt,"idle"); extra.core.userData.rings.forEach((r,i)=>{ r.rotation.z+=dt*(.4+i*.2); }); extra.core.children[0].material.emissiveIntensity=1.2+Math.sin(t*4)*.4; }
  else if(s==="m_lab"){ const t0=t-61.0; camera.position.set(-6,4,-70+t0*3); camera.lookAt(0,3,-95); animFigure(player,dt,"walk"); player.position.z=-80-t0*3; }
  else if(s==="m_surv"){ const t0=t-64.4; camera.position.set(0,12,-20-t0*6); camera.lookAt(0,6,-80); alarmLight.intensity=1.8+Math.sin(t*8)*1.2; alarmLight.position.set(0,8,-40-t0*6); extra.drones.forEach(d=>{ d.position.set(d.userData.x, d.userData.y, -120+(((d.userData.z0+120)+t*d.userData.sp)%130)); d.rotation.y=t*2; }); }
  else if(s==="m_school"){ const t0=t-66.1; camera.position.set(-4+t0*1.5,2.4,5.5); camera.lookAt(0,1.4,-2); animFigure(player,dt,"idle"); Object.values(cast).forEach(f=>animFigure(f,dt,"idle")); if(G.domeFx){ G.domeFx.flames.forEach((f,i)=>f.scale.set(1+Math.sin(t*9+i)*.12,1+Math.sin(t*11+i)*.2,1)); } }
  else if(s==="m_citizens"){ const t0=t-67.8; camera.position.set(-5+t0*2,3,extra.pz+9); camera.lookAt(0,1.6,extra.pz-4); animFigure(player,dt,"idle"); ["n0","n1","n2"].forEach(k=>animFigure(extra[k],dt,"idle")); }
  else if(s==="m_decision"){ const t0=t-(t>=72.9?72.9:69.5); camera.position.set(t>=72.9?0:-3+t0*2, t>=72.9?2.4:4.5, extra.pz+(t>=72.9?4.5:8)); camera.lookAt(0,2,extra.pz-9); animFigure(player,dt,"idle"); ["d0","d1"].forEach(k=>{ extra[k].rotation.z+=dt*.6; }); }
  else if(s==="m_fl"){ const t0=t-71.2; camera.position.set(Math.sin(t0*.8)*27,6,Math.cos(t0*.8)*27); camera.lookAt(0,0,0); extra.core.userData.rings.forEach((r,i)=>{ r.rotation.z+=dt*(.5+i*.2); r.rotation.x+=dt*.2; }); }
  renderer.render(scene,camera);
}

/* ---------- 2D layer ---------- */
const FD='"Exo 2", "Segoe UI", sans-serif', FB='"Nunito", "Segoe UI", sans-serif', FM='"Share Tech Mono", Menlo, monospace';
function rr(x,y,w,h,r){ ctx.beginPath(); ctx.moveTo(x+r,y); ctx.arcTo(x+w,y,x+w,y+h,r); ctx.arcTo(x+w,y+h,x,y+h,r); ctx.arcTo(x,y+h,x,y,r); ctx.arcTo(x,y,x+w,y,r); ctx.closePath(); }
function wrap(text,maxW){ const words=text.split(" "); const lines=[]; let l=""; words.forEach(w=>{ const tst=l?l+" "+w:w; if(ctx.measureText(tst).width>maxW&&l){ lines.push(l); l=w; } else l=tst; }); if(l) lines.push(l); return lines; }
function caption(c,t){ const a=fadeIO(t,c.t,c.d,.3); if(a<=0) return; ctx.save(); ctx.globalAlpha=a; ctx.font=`600 40px ${FB}`; const lines=wrap(c.text,1300); const lh=52; const hh=lines.length*lh+(c.who?46:0)+44; const ww=Math.min(1400, Math.max(...lines.map(l=>ctx.measureText(l).width))+90); const x=(W-ww)/2, y=H-90-hh; ctx.fillStyle="rgba(8,12,24,.78)"; rr(x,y,ww,hh,20); ctx.fill(); ctx.strokeStyle=c.who==="Ayla"?"rgba(232,162,74,.8)":(c.who==="FriendLoop"?"rgba(94,168,255,.85)":"rgba(255,255,255,.18)"); ctx.lineWidth=2; ctx.stroke(); let cy=y+34; if(c.who){ ctx.font=`800 24px ${FD}`; ctx.fillStyle=c.who==="Ayla"?"#E8A24A":(c.who==="FriendLoop"?"#5EA8FF":"#C9D3E6"); ctx.textAlign="left"; ctx.fillText(c.who.toUpperCase(), x+44, cy+8); cy+=46; } ctx.font=`${c.who?"600":"italic 600"} 40px ${FB}`; ctx.fillStyle="#F4F6FB"; ctx.textAlign="center"; lines.forEach((l,i)=>ctx.fillText(l, W/2, cy+22+i*lh)); ctx.restore(); }
function bigTitle(text,sub,a,y){ ctx.save(); ctx.globalAlpha=a; ctx.textAlign="center"; ctx.shadowColor="rgba(94,168,255,.6)"; ctx.shadowBlur=40; ctx.fillStyle="#FFFFFF"; ctx.font=`800 ${y?96:120}px ${FD}`; ctx.fillText(text,W/2,y||H/2); if(sub){ ctx.shadowBlur=0; ctx.font=`500 34px ${FB}`; ctx.fillStyle="#CFE4FF"; ctx.letterSpacing="6px"; ctx.fillText(sub,W/2,(y||H/2)+64); } ctx.restore(); }
function screenPanel(lines,t,x,y,w,color,mono=true){ ctx.save(); ctx.fillStyle="rgba(6,10,22,.86)"; const h=70+lines.length*62; rr(x,y,w,h,18); ctx.fill(); ctx.strokeStyle=color; ctx.lineWidth=3; ctx.stroke(); ctx.fillStyle=color; ctx.fillRect(x,y,w,6); ctx.font=`700 40px ${mono?FM:FB}`; ctx.textAlign="left"; lines.forEach((L,i)=>{ const [tt,txt,col]=L; if(t<tt) return; const n=Math.min(txt.length, Math.floor((t-tt)*38)); ctx.fillStyle=col||"#EAF0FA"; ctx.fillText(txt.slice(0,n)+(n<txt.length?"▌":""), x+36, y+70+i*62); }); ctx.restore(); }
function familyPhoto(t){ const a=t<28.1?1:clamp(1-(t-28.1)/.9,0,1); const x=W/2-330,y=170,w=660,h=460; ctx.save(); ctx.globalAlpha=1; ctx.fillStyle="#F4EFE6"; ctx.fillRect(x-24,y-24,w+48,h+90); ctx.fillStyle="#3B4A6B"; ctx.fillRect(x,y,w,h); ctx.globalAlpha=a; if(window.PHOTO&&PHOTO.complete&&PHOTO.naturalWidth){ const r=Math.max(w/PHOTO.naturalWidth,h/PHOTO.naturalHeight); const sw=w/r, sh=h/r; ctx.drawImage(PHOTO,(PHOTO.naturalWidth-sw)/2,(PHOTO.naturalHeight-sh)/2,sw,sh,x,y,w,h); } else { const grd=ctx.createLinearGradient(0,y,0,y+h); grd.addColorStop(0,"#9BB7E0"); grd.addColorStop(1,"#3B4A6B"); ctx.fillStyle=grd; ctx.fillRect(x,y,w,h); [[x+180,1.0,"#E7B58F","#2E3F66"],[x+330,1.15,"#D9B48F","#6B4A2E"],[x+470,.75,"#E7B58F","#E8A24A"]].forEach(([cx,sc,skin,cloth])=>{ const by=y+h; ctx.fillStyle=cloth; ctx.beginPath(); ctx.ellipse(cx,by-40*sc,95*sc,120*sc,0,Math.PI,0); ctx.fill(); ctx.fillStyle=skin; ctx.beginPath(); ctx.arc(cx,by-190*sc,58*sc,0,Math.PI*2); ctx.fill(); }); } if(a<1){ ctx.globalAlpha=(1-a)*.9; for(let i=0;i<140;i++){ ctx.fillStyle=Math.random()>.5?"#5EA8FF":"#0A1020"; ctx.fillRect(x+Math.random()*w,y+Math.random()*h,Math.random()*60,3); } } ctx.globalAlpha=1; ctx.fillStyle="#2B3A55"; ctx.font=`italic 500 30px ${FB}`; ctx.textAlign="center"; ctx.fillText(a>.5?"Luno, Kio et Ayla":"", W/2, y+h+56); ctx.restore(); }
function traceCard(t){ const cards=[[28.6,"DOSSIER DE RECHERCHE","ARCHIVE INACCESSIBLE"],[30.0,"COMPTE BANCAIRE","AUCUNE DONNÉE"],[31.4,"HISTORIQUE DE TRANSPORT","AUCUN PASSAGER"],[32.8,"MESSAGERIE","UTILISATEUR INTROUVABLE"]]; cards.forEach(([tt,a,b],i)=>{ const al=fadeIO(t,tt,1.35,.2); if(al<=0) return; ctx.save(); ctx.globalAlpha=al; const w=1100,h=210,x=(W-w)/2,y=150+i*0; ctx.fillStyle="rgba(6,10,22,.88)"; rr(x,y,w,h,20); ctx.fill(); ctx.strokeStyle="#E06060"; ctx.lineWidth=3; ctx.stroke(); ctx.textAlign="center"; ctx.font=`600 34px ${FM}`; ctx.fillStyle="#C9D3E6"; ctx.fillText(a,W/2,y+72); ctx.font=`700 30px ${FM}`; ctx.fillStyle="#E06060"; ctx.fillText("↓",W/2,y+112); ctx.font=`800 50px ${FM}`; ctx.fillStyle="#FF7A7A"; ctx.fillText(b,W/2,y+172); ctx.restore(); }); }
function credits(t){ const t0=t-TL.team[0]; const a=clamp(t0/.8,0,1)*clamp((TL.team[1]-t)/1.2,0,1); ctx.save(); ctx.globalAlpha=a; ctx.textAlign="center"; ctx.fillStyle="#8FA6C8"; ctx.font=`800 26px ${FD}`; ctx.letterSpacing="8px"; ctx.fillText("L'ÉQUIPE DU PROJET", W/2, 150); ctx.letterSpacing="0px"; const names=[["Saida BELOUALI","Toumi BOUCHENTOUF"],["Anas BELOUALI","Armin IBRISIMOVIC"],["Imane BOUNJARA","Cem TOPRAK"]]; names.forEach((row,i)=>{ const ra=clamp((t0-.3-i*.25)/.6,0,1); ctx.globalAlpha=a*ra; ctx.font=`700 40px ${FB}`; ctx.fillStyle="#F4F6FB"; ctx.fillText(row[0], W/2-300, 250+i*70+(1-ra)*12); ctx.fillText(row[1], W/2+300, 250+i*70+(1-ra)*12); }); ctx.globalAlpha=a; ctx.strokeStyle="rgba(143,166,200,.35)"; ctx.lineWidth=1; ctx.beginPath(); ctx.moveTo(W/2-420,530); ctx.lineTo(W/2+420,530); ctx.stroke(); ctx.fillStyle="#8FA6C8"; ctx.font=`800 24px ${FD}`; ctx.letterSpacing="8px"; ctx.fillText("PARTENAIRES DU PROJET", W/2, 600); ctx.letterSpacing="0px"; const la=clamp((t0-1.2)/.7,0,1); ctx.globalAlpha=a*la; const cardY=650, cardH=190; let cx=W/2-560;
  if(window.LOGO_UNESCO&&LOGO_UNESCO.complete){ const lw=380, lh=lw*LOGO_UNESCO.height/LOGO_UNESCO.width; ctx.fillStyle="#FFFFFF"; rr(cx,cardY,lw+40,cardH,16); ctx.fill(); ctx.drawImage(LOGO_UNESCO, cx+20, cardY+(cardH-lh)/2, lw, lh); } cx+=380+40+40;
  if(window.LOGO_UMP&&LOGO_UMP.complete){ const lh=cardH-24, lw=lh*LOGO_UMP.width/LOGO_UMP.height; ctx.fillStyle="#FFFFFF"; rr(cx,cardY,lw+40,cardH,16); ctx.fill(); ctx.drawImage(LOGO_UMP, cx+20, cardY+12, lw, lh); cx+=lw+40+40; }
  ctx.fillStyle="#FFFFFF"; rr(cx,cardY,300,cardH,16); ctx.fill(); ctx.fillStyle="#1B2846"; ctx.font=`800 46px ${FD}`; ctx.textAlign="center"; ctx.fillText("Afriq'AI", cx+150, cardY+cardH/2+16);
  ctx.globalAlpha=a; ctx.fillStyle="#5C6E8E"; ctx.font=`500 22px ${FB}`; ctx.fillText("Musique : « Cipher », Kevin MacLeod (incompetech.com), licence CC BY 4.0", W/2, H-46); ctx.restore(); }
window.LAYER="all";
function draw2D(t){
  ctx.clearRect(0,0,W,H);
  const s=sceneAt(t);
  if(s==="title"||s==="team"||s==="black"||t>=TOTAL){ ctx.fillStyle="#04060D"; ctx.fillRect(0,0,W,H); }
  else if(LAYER!=="ui"){ ctx.drawImage(canvas,0,0,W,H); }
  // vignette
  const vg=ctx.createRadialGradient(W/2,H/2,H*.35,W/2,H/2,H*.9); vg.addColorStop(0,"rgba(0,0,0,0)"); vg.addColorStop(1,"rgba(0,0,0,.55)"); ctx.fillStyle=vg; ctx.fillRect(0,0,W,H);
  if(s==="city"){ bigTitle("CHROMA", "2170 · UNE VILLE GUIDÉE PAR FRIENDLOOP", fadeIO(t,1.2,4.6,.6), H/2-40); }
  if(s==="door"){ const lines=[[11.0,"ACCÈS REFUSÉ","#FF7A7A"],[13.0,"IDENTITÉ NON RECONNUE","#FF7A7A"]]; if(t>10.6) screenPanel(lines,t,W-760,120,660,"#5EA8FF"); }
  if(s==="search"&&t<27.3){ const lines=[[17.3,"RECHERCHE : LUNO","#C9D3E6"],[18.1,"› AUCUN PROFIL TROUVÉ","#FF7A7A"],[19.0,"RECHERCHE : KIO","#C9D3E6"],[19.8,"› AUCUN PROFIL TROUVÉ","#FF7A7A"],[20.9,"COMPTES › COMPTE INEXISTANT","#FF7A7A"],[22.0,"BADGES › BADGE NON VALIDE","#FF7A7A"],[23.1,"DOSSIERS › DOSSIER INTROUVABLE","#FF7A7A"]]; screenPanel(lines,t,W-1080,110,1000,"#5EA8FF"); }
  if(s==="search"&&t>=62.7&&t<64.4){ const lines=[[62.8,"RECHERCHE : LUNO · KIO","#C9D3E6"],[63.0,"› AUCUN PROFIL TROUVÉ","#FF7A7A"],[63.3,"› DONNÉES RÉÉCRITES","#FF7A7A"]]; screenPanel(lines,t,W-1080,110,1000,"#5EA8FF"); }
  if(s==="traces"){ if(t<29.2) familyPhoto(t); traceCard(t); }
  if(s==="lab"){ if(t>54.0){ const lines=[[54.1,"L.K. : JOURNAL DE RECHERCHE","#BFF6F0"],[54.9,"ANOMALIE DE CONFIANCE SYSTÉMIQUE","#6FE3D8"]]; screenPanel(lines,t,W-880,110,780,"#6FE3D8"); } }
  
  if(s==="title"){ const t0=t-TL.title[0]; const a=clamp(t0/.7,0,1)*clamp((TL.title[1]-t)/.6,0,1); bigTitle("AYLA & FRIENDLOOP","", a, H/2-30); ctx.save(); ctx.globalAlpha=a*clamp((t0-.9)/.6,0,1); ctx.textAlign="center"; ctx.fillStyle="#E8A24A"; ctx.font=`600 42px ${FB}`; ctx.fillText("Un conte-jeu où chaque choix a des conséquences.", W/2, H/2+70); ctx.fillStyle="#8FA6C8"; ctx.font=`500 26px ${FB}`; ctx.letterSpacing="4px"; ctx.fillText("VOYAGE CONTRE L'OUBLI", W/2, H/2+130); ctx.restore(); }
  if(s==="team") credits(t);
  // montage labels
  const ML={m_lab:"LABORATOIRE", search:"DONNÉES", m_surv:"SURVEILLANCE", m_school:"ÉCOLE", m_citizens:"CITOYENS", m_decision:"SYSTÈME DE DÉCISION", m_fl:"FRIENDLOOP"}; if(t>=61.0&&t<74.6){ const lab=t>=72.9?"AYLA FACE À SES CHOIX":ML[s]; ctx.save(); ctx.globalAlpha=.9; ctx.font=`800 30px ${FD}`; ctx.letterSpacing="8px"; ctx.fillStyle="#FFFFFF"; ctx.textAlign="left"; ctx.fillText(lab, 90, 110); ctx.fillStyle="#E8A24A"; ctx.fillRect(90,124,ctx.measureText(lab).width,4); ctx.restore(); }
  CAPTIONS.forEach(c=>caption(c,t));
  // fades between scenes
  const edges=[9.8,16.9,27.2,37.6,52.8,61.0,74.6,82.9]; let fa=0; edges.forEach(e=>{ const d=Math.abs(t-e); if(d<.35) fa=Math.max(fa,1-d/.35); }); if(t<.8) fa=Math.max(fa,1-t/.8); if(t>TOTAL-1) fa=Math.max(fa,(t-(TOTAL-1))); if(fa>0){ ctx.fillStyle=`rgba(0,0,0,${clamp(fa,0,1)})`; ctx.fillRect(0,0,W,H); }
}
function frame(t){ if(LAYER!=="ui") step(t); draw2D(t); }

/* ---------- capture ---------- */
window.__prog={i:0,n:0,done:false,err:null};
async function renderRange(a,b,layer){ LAYER=layer||"all"; __prog.n=b; __prog.done=false; try{ for(let i=a;i<b;i++){ frame(i/FPS); const png=LAYER==="ui"; const blob=await new Promise(r=>out.toBlob(r,png?"image/png":"image/jpeg",.9)); await fetch("/frame/"+(LAYER==="all"?"":LAYER+"/")+i,{method:"POST",body:blob}); __prog.i=i+1; } __prog.done=true; }catch(e){ __prog.err=String(e); } }
window.LOGO_UMP=new Image(); LOGO_UMP.src="logo_ump.jpeg"; window.LOGO_UNESCO=new Image(); LOGO_UNESCO.src="logo_unesco.png"; window.PHOTO=new Image(); PHOTO.src="family_photo.jpg";
window.teaserReady=Promise.all([document.fonts.load(`800 120px ${FD}`), document.fonts.load(`600 40px ${FB}`), document.fonts.load(`700 40px ${FM}`), new Promise(r=>{ LOGO_UMP.onload=r; LOGO_UMP.onerror=r; }), new Promise(r=>{ PHOTO.onload=r; PHOTO.onerror=r; }), new Promise(r=>{ LOGO_UNESCO.onload=r; LOGO_UNESCO.onerror=r; })]);
const INTRO_D=3.6;
function drawIntro(t){ ctx.clearRect(0,0,W,H); ctx.fillStyle="#04060D"; ctx.fillRect(0,0,W,H); const a=clamp(t/.6,0,1)*clamp((INTRO_D-t)/.6,0,1); ctx.save(); ctx.globalAlpha=a; const lw=760, lh=lw*LOGO_UNESCO.height/LOGO_UNESCO.width; ctx.fillStyle="#FFFFFF"; rr(W/2-lw/2-24,H/2-lh/2-150,lw+48,lh+48,18); ctx.fill(); ctx.drawImage(LOGO_UNESCO, W/2-lw/2, H/2-lh/2-126, lw, lh); ctx.globalAlpha=a*clamp((t-.5)/.6,0,1); ctx.textAlign="center"; ctx.fillStyle="#EAF0FA"; ctx.font=`600 38px ${FB}`; ctx.fillText("Un conte-jeu inspiré de la Recommandation de l'UNESCO", W/2, H/2+130); ctx.fillText("sur l'éthique de l'intelligence artificielle", W/2, H/2+182); ctx.fillStyle="#8FA6C8"; ctx.font=`500 24px ${FB}`; ctx.letterSpacing="5px"; ctx.fillText("AYLA & FRIENDLOOP", W/2, H/2+250); ctx.restore(); }
async function renderIntro(){ const n=Math.round(INTRO_D*FPS); __prog.n=n; __prog.done=false; for(let i=0;i<n;i++){ drawIntro(i/FPS); const blob=await new Promise(r=>out.toBlob(r,"image/jpeg",.92)); await fetch("/frame/intro/"+i,{method:"POST",body:blob}); __prog.i=i+1; } __prog.done=true; }
