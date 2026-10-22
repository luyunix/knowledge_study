// Editable, repo-native vector figures; no raster image generation.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.join(root,'assets/dubbo-lifecycle');
fs.mkdirSync(out,{recursive:true});
const esc=x=>String(x).replaceAll('&','&amp;').replaceAll('<','&lt;');
const rect=(x,y,w,h,fill='white')=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${fill}" stroke="#444" stroke-width="1"/>`;
const label=(x,y,s,size=18)=>`<text x="${x}" y="${y}" text-anchor="middle" font-size="${size}">${esc(s)}</text>`;
const box=(x,y,w,h,s,fill='white')=>rect(x,y,w,h,fill)+label(x+w/2,y+h/2+6,s);
const arrow=d=>`<path data-arrow="1" d="${d}" fill="none" stroke="#444" stroke-width="1" marker-end="url(#a)"/>`;
const pod=(x,y,name)=>rect(x,y,145,82)+label(x+72,y+22,name,16)+box(x+10,y+33,55,34,'SDK')+box(x+77,y+33,58,34,'业务');
const versions=()=>rect(490,30,490,120)+label(735,54,'版本 r1')+pod(615,60,'Pod A')+pod(805,60,'Pod B')+
 rect(490,180,490,120)+label(735,204,'版本 r2')+pod(615,210,'Pod D')+pod(805,210,'Pod E');
const figures=[
 ['01-shared-runtime',330,
  box(15,138,95,55,'请求')+rect(145,15,840,300)+label(285,40,'共享 JVM')+
  rect(170,70,260,220)+label(300,95,'平台运行时')+
  box(195,120,210,48,'版本规则')+box(195,218,210,48,'版本句柄')+
  rect(490,30,490,120)+label(735,54,'版本 r1')+rect(515,70,440,60)+label(615,106,'ClassLoader')+box(760,82,170,35,'业务')+
  rect(490,180,490,120)+label(735,204,'版本 r2')+rect(515,220,440,60)+label(615,256,'ClassLoader')+box(760,232,170,35,'业务')+
  arrow('M110 165 H165')+arrow('M300 168 V213')+arrow('M430 244 H510')],
 ['02-dubbo-runtime',330,
  box(15,138,95,55,'请求')+rect(145,30,285,270,'#f5f0fc')+label(288,57,'Proxy 进程')+
  box(170,83,235,45,'版本规则')+box(170,160,235,45,'引用缓存')+box(170,237,235,45,'Dubbo 客户端')+
  versions()+arrow('M110 165 H140')+arrow('M288 128 V155')+arrow('M288 205 V232')+arrow('M430 260 H610')],
 ['03-publish-discovery',245,
  box(20,25,140,55,'制品')+box(215,25,140,55,'启动 / 预热')+box(410,25,140,55,'服务导出')+
  box(605,25,140,55,'ZK 注册')+box(800,25,180,55,'目录更新')+
  arrow('M160 52 H210')+arrow('M355 52 H405')+arrow('M550 52 H600')+arrow('M745 52 H795')+
  box(800,165,180,55,'目标验证')+box(410,165,140,55,'规则发布')+box(20,165,140,55,'受控接流')+
  arrow('M890 80 V160')+arrow('M800 192 H555')+arrow('M410 192 H165')],
 ['04-request-path',230,
  rect(15,20,760,190)+label(395,48,'Proxy 进程')+
  box(35,95,118,55,'版本规则')+box(183,95,118,55,'r2 引用')+box(331,95,118,55,'Directory')+
  box(479,95,118,55,'Router')+box(627,95,118,55,'LB')+
  arrow('M153 122 H178')+arrow('M301 122 H326')+arrow('M449 122 H474')+arrow('M597 122 H622')+
  rect(820,20,165,190)+label(902,48,'Pod D')+box(840,95,125,55,'SDK')+box(840,175,125,25,'业务')+
  arrow('M745 122 H835')+arrow('M902 150 V170')],
 ['05-drain',260,
  rect(15,15,970,95)+label(500,40,'平台控制面')+
  box(45,55,210,40,'版本切流')+box(395,55,210,40,'撤注册')+box(745,55,210,40,'传播观测')+
  arrow('M255 75 H390')+arrow('M605 75 H740')+
  rect(15,155,970,90)+label(500,180,'业务进程')+
  box(45,192,210,38,'停止接纳')+box(395,192,210,38,'等待在途')+box(745,192,210,38,'关闭资源')+
  arrow('M255 211 H390')+arrow('M605 211 H740')+arrow('M150 110 V150')],
 ['06-control-and-discovery',430,
  rect(15,20,400,110)+label(215,45,'平台控制面')+
  box(35,65,150,40,'规则存储')+box(225,65,165,40,'发布任务')+
  box(580,40,175,70,'ZooKeeper')+
  rect(15,245,500,165)+label(265,273,'Proxy 进程')+
  box(45,300,180,45,'规则缓存')+box(305,300,180,45,'Dubbo 目录')+
  rect(800,220,185,180)+label(892,247,'版本 r2')+
  box(820,260,145,45,'Pod D')+box(820,335,145,45,'Pod E')+
  arrow('M110 105 V185 H135 V295')+
  arrow('M665 110 V180 H395 V295')+
  arrow('M965 282 H990 V75 H760')+
  arrow('M515 322 H740 V282 H815')]
];
for(const [name,height,body] of figures){
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="${height}" viewBox="0 0 1000 ${height}"><title>${name}</title><defs><marker id="a" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M1 1 L6 3.5 L1 6" fill="none" stroke="#444"/></marker></defs><rect width="1000" height="${height}" fill="white"/><g font-family="PingFang SC,sans-serif" fill="black">${body}</g></svg>\n`;
 fs.writeFileSync(path.join(out,name+'.svg'),svg);
}
console.log(JSON.stringify({figures:figures.map(([name])=>name),out}));
