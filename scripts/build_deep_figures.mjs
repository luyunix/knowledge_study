// Deterministic, editable SVG diagrams. PNG rendering uses render_index_figures.mjs.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const dir=path.join(root,'assets/deep-points');
const specs=JSON.parse(fs.readFileSync(path.join(dir,'spec.json'),'utf8'));
const selectedIds=process.env.FIGURE_IDS?.split(',').map(Number);
const selectedSpecs=selectedIds?specs.filter(s=>selectedIds.includes(s.n)):specs;
const esc=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
// Rows encode separate states/comparisons; only explicit edges denote transitions.
const edges={
  1:[[[0,0],[0,1]],[[1,0],[0,1]],[[1,1],[0,1]]],
  2:[[[0,0],[0,1]],[[0,1],[0,2]],[[0,1],[1,0]],[[0,1],[1,1]]],
  3:[[[0,0],[0,1]],[[0,1],[0,2]],[[1,0],[1,1]],[[1,1],[1,2]]],
  4:[[[0,0],[1,0]],[[0,0],[1,1]]],
  5:[[[0,0],[1,0]],[[0,0],[1,1]],[[2,0],[1,0]],[[2,0],[1,1]]],
  6:[[[1,0],[1,1]],[[2,0],[2,1]]],
  8:[[[0,0],[0,1]],[[0,1],[0,2]]],
  11:[[[0,0],[0,1]],[[0,1],[0,2]],[[0,2],[0,3]],[[1,0],[2,0]]],
  12:[],13:[],14:[[[0,0],[0,1]],[[0,1],[0,2]]],
  18:[[[0,0],[0,1]],[[0,1],[0,2]]],
  19:[[[1,0],[1,1]],[[1,1],[1,2]]],
  20:[],23:[[[2,0],[2,1]],[[2,1],[2,2]]],
  25:[[[0,0],[0,1]],[[1,0],[1,1]]],26:[[[1,0],[1,1]],[[1,1],[1,2]]],27:[],
  29:[[[0,0],[0,1]],[[1,0],[1,1]],[[2,0],[2,1]]],30:[],31:[],33:[[[0,0],[0,1]],[[1,0],[1,1]],[[2,0],[2,1]]],
  35:[],36:[],37:[[[0,0],[0,1]],[[0,1],[0,2]],[[1,0],[1,1]],[[1,1],[1,2]],[[2,0],[2,2]],[[2,1],[2,2]]],
  41:[[[0,0],[0,1]],[[0,1],[0,2]],[[1,0],[1,1]],[[1,1],[1,2]]],
  42:[[[0,0],[0,1]],[[1,0],[1,1]],[[1,1],[1,2]]],
  43:[[[1,0],[1,1]],[[1,1],[1,2]]],
  44:[],49:[],53:[],56:[],60:[],
  51:[[[0,0],[0,1]],[[0,1],[0,2]],[[1,0],[1,1]],[[1,1],[1,2]],[[2,0],[2,1]],[[2,1],[2,2]]],
  57:[[[1,0],[1,1]],[[1,1],[1,2]],[[2,0],[2,1]],[[2,1],[2,2]]],
  64:[[[0,0],[0,1]],[[1,0],[1,1]],[[2,0],[2,1]]]
};
function wrap(text,width){
  const max=(width-18)/18,lines=[];let line='',used=0;
  for(const c of text){const u=/[\u0000-\u007f]/.test(c)?0.58:1;
    if(used+u>max&&line){lines.push(line);line='';used=0;}line+=c;used+=u;
  }if(line)lines.push(line);return lines;
}
for(const s of selectedSpecs){
  let custom='';
  const box=(x,y,w,h,label)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="white" stroke="#444"/><text x="${x+w/2}" y="${y+h/2+6}" text-anchor="middle" font-size="18">${esc(label)}</text>`;
  const label=(x,y,t)=>`<text x="${x}" y="${y}" text-anchor="middle" font-size="17">${esc(t)}</text>`;
  const arrow=d=>`<path d="${d}" fill="none" stroke="#444" marker-end="url(#a)"/>`;
  if(s.n===67){
    custom='<rect x="20" y="20" width="260" height="260" fill="none" stroke="#444"/>'+label(150,48,'同一解释器')+
      box(40,75,220,55,'sys.modules')+box(40,175,220,55,'调用方旧绑定')+
      arrow('M150 130 V170')+
      '<rect x="340" y="20" width="280" height="115" fill="none" stroke="#444"/>'+label(480,47,'版本 A 进程')+box(365,65,230,48,'模块缓存 A')+
      '<rect x="340" y="165" width="280" height="115" fill="none" stroke="#444"/>'+label(480,192,'版本 B 进程')+box(365,210,230,48,'模块缓存 B');
  }else if(s.n===69){
    custom=box(20,100,110,60,'请求信封')+box(175,100,110,60,'Proxy')+
      '<rect x="335" y="20" width="285" height="260" fill="none" stroke="#444"/>'+label(478,48,'版本 Pod')+
      '<rect x="355" y="70" width="245" height="80" fill="none" stroke="#444"/>'+label(478,101,'SDK')+label(478,132,'契约 + 上下文')+
      box(355,195,245,55,'业务实现')+arrow('M130 130 H170')+arrow('M285 130 H350')+arrow('M478 150 V190');
  }else if(s.n===70){
    custom='<rect x="20" y="20" width="285" height="260" fill="none" stroke="#444"/>'+label(162,48,'Codex 会话')+
      box(45,75,235,55,'Skill')+box(45,195,235,55,'CLI 子进程')+arrow('M162 130 V190')+
      '<rect x="405" y="20" width="215" height="260" fill="none" stroke="#444"/>'+label(512,48,'平台服务')+
      box(425,195,175,55,'操作状态')+arrow('M280 210 H420')+arrow('M425 237 H285')+label(355,189,'op_id');
  }else if(s.n===72){
    custom='<rect x="20" y="20" width="255" height="260" fill="none" stroke="#444"/>'+label(148,48,'平台')+
      box(40,75,215,55,'run / attempt')+box(40,200,215,55,'manifest')+
      '<rect x="355" y="20" width="265" height="140" fill="none" stroke="#444"/>'+label(488,48,'Job')+
      box(380,75,215,55,'构建 Pod')+box(380,200,215,55,'OSS 分片产物')+
      arrow('M255 102 H375')+arrow('M488 130 V195')+arrow('M380 228 H260')+label(315,88,'调和');
  }else if(s.n===73){
    custom=box(20,115,85,60,'N=10')+box(155,25,120,60,'[0,4)')+box(155,115,120,60,'[4,7)')+box(155,205,120,60,'[7,10)')+
      box(330,25,130,60,'对象 0')+box(330,115,130,60,'对象 1')+box(330,205,130,60,'对象 2')+box(520,115,100,60,'清单')+
      arrow('M105 135 H130 V55 H150')+arrow('M105 145 H150')+arrow('M105 155 H130 V235 H150')+
      arrow('M275 55 H325')+arrow('M275 145 H325')+arrow('M275 235 H325')+
      arrow('M460 55 H490 V135 H515')+arrow('M460 145 H515')+arrow('M460 235 H490 V155 H515');
  }else if(s.n===44){
    custom='<rect x="20" y="15" width="600" height="270" fill="none" stroke="#444"/>'+label(320,43,'同一把锁')+
      box(45,65,200,50,'Map：A → node A')+box(395,65,200,50,'Map：B → node B')+
      box(45,175,85,50,'head')+box(205,175,75,50,'A')+box(355,175,75,50,'B')+box(505,175,85,50,'tail')+
      arrow('M130 190 H200')+arrow('M205 210 H135')+arrow('M280 190 H350')+arrow('M355 210 H285')+
      arrow('M430 190 H500')+arrow('M505 210 H435')+arrow('M245 115 V170')+arrow('M495 115 H393 V170');
  }else if(s.n===32){
    custom=box(20,35,230,55,'127 × 1 + 1000')+box(305,35,140,55,'b=2')+box(500,35,120,55,'35 B')+
      arrow('M250 62 H300')+arrow('M445 62 H495')+
      box(20,145,230,55,'127 × 1 + 129')+box(305,145,140,55,'低部全 1')+box(500,145,120,55,'4 B')+
      arrow('M250 172 H300')+arrow('M445 172 H495')+
      box(20,245,600,40,'头部 + 主体 / 常量 + 异常位置与高部');
  }else if(s.n===39){
    custom=box(20,30,110,55,'User')+box(180,30,110,55,'A：c1')+box(340,30,110,55,'T：c1')+box(500,30,120,55,'Assistant')+
      arrow('M130 57 H175')+arrow('M290 57 H335')+arrow('M450 57 H495')+
      '<rect x="20" y="125" width="600" height="150" fill="none" stroke="#444"/>'+label(320,151,'运行状态')+
      box(45,180,155,55,'消息与观察')+box(245,180,150,55,'目标 / 版本')+box(440,180,155,55,'操作 ID');
  }else if(s.n===49){
    custom=box(20,105,130,60,'路由快照')+
      '<rect x="200" y="25" width="420" height="250" fill="none" stroke="#444"/>'+label(410,53,'版本句柄')+
      box(225,100,170,70,'接纳门 + 在途')+box(445,100,145,70,'执行资源')+
      arrow('M150 135 H220')+arrow('M395 135 H440')+
      box(225,215,170,40,'beginDrain')+arrow('M310 215 V175')+label(510,239,'在途=0 后释放')+
      box(20,340,120,55,'控制面 G9')+
      '<rect x="210" y="310" width="185" height="100" fill="none" stroke="#444"/>'+label(302,337,'Proxy 1')+box(230,355,145,38,'已装 G9')+
      '<rect x="430" y="310" width="190" height="100" fill="none" stroke="#444"/>'+label(525,337,'Proxy 2')+box(450,355,150,38,'仍为 G8')+
      arrow('M140 367 H205')+
      box(20,455,270,50,'G8 迟到：拒绝')+box(350,455,270,50,'回滚：新代次 G10');
  }else if(s.n===53){
    custom=box(25,115,110,60,'A 导出')+box(265,35,110,60,'B 构建')+
      box(265,205,110,60,'C 校验')+box(505,115,110,60,'D 发布')+
      arrow('M135 135 H195 V65 H260')+arrow('M135 155 H195 V235 H260')+
      arrow('M375 65 H445 V135 H500')+arrow('M375 235 H445 V155 H500');
  }else if(s.n===56){
    custom=box(20,35,145,50,'WriteBatch')+box(245,35,145,50,'WAL')+box(470,35,150,50,'memtable')+
      arrow('M165 60 H240')+arrow('M390 60 H465')+
      box(470,140,150,50,'immutable')+box(245,140,145,50,'SST L0')+box(20,140,145,50,'SST L1+')+
      arrow('M545 85 V135')+arrow('M470 165 H395')+arrow('M245 165 H170')+
      box(20,235,600,45,'读：snapshot → mem / imm / Version');
  }else if(s.n===60){
    custom=box(20,120,125,60,'调度器')+
      '<rect x="205" y="25" width="410" height="250" fill="none" stroke="#444"/>'+label(410,53,'持久化任务')+
      box(230,80,160,50,'plan revision')+box(430,80,160,50,'lease + epoch')+
      box(230,200,160,50,'RUNNING')+box(430,200,160,50,'SUCCEEDED')+
      arrow('M145 150 H180 V105 H225')+arrow('M390 105 H425')+
      arrow('M510 130 V165 H310 V195')+arrow('M390 225 H425');
  }else if(s.n===30){
    custom=box(20,80,80,80,'起点')+box(285,80,70,80,'Q')+box(550,80,70,80,'终态')+
      arrow('M100 100 H280')+arrow('M100 140 H280')+arrow('M355 100 H545')+arrow('M355 140 H545')+
      label(190,89,'a / 5')+label(190,133,'d / 9')+label(450,89,'b / 0')+label(450,133,'c / 2');
  }else if(s.n===12){
    custom=label(20,52,'原')+box(55,22,50,42,'A')+box(535,22,50,42,'C')+arrow('M105 43 H530')+label(320,29,'span=2')+
      label(20,144,'新')+box(55,114,50,42,'A')+box(355,114,50,42,'X')+box(535,114,50,42,'C')+
      arrow('M105 135 H350')+arrow('M405 135 H530')+label(230,121,'span=2')+label(470,121,'span=1')+
      box(55,218,50,42,'A')+box(205,218,50,42,'B')+box(355,218,50,42,'X')+box(535,218,50,42,'C')+
      arrow('M105 239 H200')+arrow('M255 239 H350')+arrow('M405 239 H530');
  }else if(s.n===11){
    custom='<rect x="20" y="18" width="600" height="90" fill="none" stroke="#444"/>'+label(90,41,'listpack')+
      box(35,52,100,38,'头部6B')+box(150,52,220,38,'编码与值')+box(385,52,125,38,'backlen')+box(525,52,80,38,'FF')+
      arrow('M320 108 V140')+label(407,131,'超出阈值')+
      '<rect x="20" y="145" width="600" height="125" fill="none" stroke="#444"/>'+label(96,174,'quicklist')+
      box(55,192,230,52,'节点：[a b]')+box(355,192,230,52,'节点：[c d]')+arrow('M285 218 H350');
  }else if(s.n===20){
    custom='<rect x="15" y="15" width="610" height="270" fill="none" stroke="#444"/>'+label(320,43,'共享宿主内核')+
      '<rect x="35" y="65" width="265" height="190" fill="none" stroke="#444"/>'+label(168,94,'容器 A / namespace A')+
      box(55,115,225,52,'独立进程 / 运行时')+box(55,190,225,44,'cgroup 预算 A')+
      '<rect x="340" y="65" width="265" height="190" fill="none" stroke="#444"/>'+label(472,94,'容器 B / namespace B')+
      box(360,115,225,52,'独立进程 / 运行时')+box(360,190,225,44,'cgroup 预算 B');
  }else if(s.n===25){
    custom=box(20,115,160,60,'Kafka 分区 P2')+
      '<rect x="330" y="20" width="285" height="110" fill="none" stroke="#444"/>'+label(470,49,'引擎副本 R0')+box(365,65,215,43,'独立位点：100')+
      '<rect x="330" y="170" width="285" height="110" fill="none" stroke="#444"/>'+label(470,199,'引擎副本 R1')+box(365,215,215,43,'独立位点：70')+
      arrow('M180 135 H250 V75 H325')+arrow('M180 155 H250 V225 H325');
  }else if(s.n===27){
    custom=box(260,20,120,50,'leader A')+box(75,125,150,50,'follower B')+box(415,125,150,50,'follower C')+
      arrow('M290 70 V98 H150 V120')+arrow('M350 70 V98 H490 V120')+
      box(75,225,230,50,'ISR：A B')+box(345,225,230,50,'C：落后');
  }
  if(custom){
    const customHeight=s.n===49?530:300;
    const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="640" height="${customHeight}" viewBox="0 0 640 ${customHeight}"><title>${esc(s.name)}</title><defs><marker id="a" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M1 1 L6 3.5 L1 6" fill="none" stroke="#444"/></marker></defs><rect width="640" height="${customHeight}" fill="white"/><g font-family="PingFang SC,sans-serif" fill="black">${custom}</g></svg>`;
    fs.writeFileSync(path.join(dir,String(s.n).padStart(2,'0')+'.svg'),svg+'\n');continue;
  }
  const h=s.rows.length*92+20,boxes=[];
  let svg=`<svg xmlns="http://www.w3.org/2000/svg" width="640" height="${h}" viewBox="0 0 640 ${h}"><title>${esc(s.name)}</title><defs><marker id="a" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M1 1 L6 3.5 L1 6" fill="none" stroke="#444"/></marker></defs><rect width="640" height="${h}" fill="white"/>`;
  s.rows.forEach((row,r)=>{const w=(600-22*(row.length-1))/row.length;
    boxes[r]=row.map((label,c)=>({x:20+c*(w+22),y:18+r*92,w,h:58,label}));});
  const selected=edges[s.n]??boxes.flatMap((row,r)=>row.slice(1).map((_,c)=>[[r,c],[r,c+1]]));
  for(const[[r,c],[rr,cc]]of selected){const a=boxes[r][c],b=boxes[rr][cc];let d;
    if(r===rr)d=`M${a.x+a.w} ${a.y+29} H${b.x-5}`;
    else{const ay=rr>r?a.y+a.h:a.y,by=rr>r?b.y-5:b.y+b.h+5;
      const mid=(ay+by)/2;d=`M${a.x+a.w/2} ${ay} V${mid} H${b.x+b.w/2} V${by}`;}
    svg+=`<path d="${d}" fill="none" stroke="#444" stroke-width="1" marker-end="url(#a)"/>`;
  }
  for(const row of boxes)for(const b of row){
    svg+=`<rect x="${b.x}" y="${b.y}" width="${b.w}" height="${b.h}" fill="white" stroke="#444" stroke-width="1"/>`;
    const lines=wrap(b.label,b.w),y=b.y+29-(lines.length-1)*11+6;
    svg+=`<text x="${b.x+b.w/2}" y="${y}" font-family="PingFang SC,sans-serif" font-size="18" text-anchor="middle" fill="black">`;
    lines.forEach((line,i)=>svg+=`<tspan x="${b.x+b.w/2}" dy="${i?22:0}">${esc(line)}</tspan>`);svg+='</text>';
  }
  svg+='</svg>';fs.writeFileSync(path.join(dir,String(s.n).padStart(2,'0')+'.svg'),svg+'\n');
}
console.log(`Built ${selectedSpecs.length} editable SVG figures`);
