// Editable repo-native diagram for the marketing creation walkthrough.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dir=path.join(root,'assets/agent-marketing');
fs.mkdirSync(dir,{recursive:true});
const escape=value=>String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const text=(x,y,value,size=25,weight=400)=>`<text x="${x}" y="${y}" font-size="${size}" font-weight="${weight}" fill="#172c43">${escape(value)}</text>`;
const panel=(x,y,width,height,title,lines,fill)=>`<rect x="${x}" y="${y}" width="${width}" height="${height}" fill="${fill}" stroke="#9eafbf"/>${text(x+20,y+37,title,27,600)}${lines.map((line,index)=>text(x+20,y+78+index*36,line)).join('')}`;
const arrow=(x,y1,y2)=>`<path d="M ${x} ${y1} L ${x} ${y2}" fill="none" stroke="#425a70" stroke-width="2" marker-end="url(#arrow)"/>`;
const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="800" height="1040" viewBox="0 0 800 1040" role="img" aria-labelledby="title description">
<title id="title">商家活动确认执行与恢复</title><desc id="description">确认草案后持久化唯一操作，业务短事务预占预算并创建活动；响应丢失后查询原操作，复用成功结果或继续等待恢复。</desc>
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#425a70"/></marker></defs>
<rect width="800" height="1040" fill="white"/><g font-family="PingFang SC,Heiti SC,Microsoft YaHei,sans-serif">
${text(32,48,'商家活动：确认、执行与恢复',32,600)}
${text(32,91,'教学设定：可用预算 1000 元，申请预占 600 元。',25)}
${panel(32,120,736,136,'① 草案 D17 / v3',['商品、优惠、时间、600 元额度','尚未确认，不允许创建活动。'],'#eef3f7')}
${arrow(400,265,296)}
${panel(32,310,736,136,'② 商家确认，保存唯一操作 O9',['冻结参数、确认人和规则版本。','重复确认仍返回 O9；此时预算尚未预占。'],'#e2eefb')}
${arrow(400,455,486)}
${panel(32,500,736,172,'③ worker 执行短事务',['锁 O9 → 条件预占 → 创建活动','预占明细、活动、结果和 outbox 一起提交。','技术异常整体回滚，O9 仍可恢复。'],'#dcf2e6')}
${arrow(400,681,712)}
${text(32,752,'④ 响应丢失后，按 O9 查询权威状态',27,600)}
${panel(32,778,354,128,'SUCCEEDED',['返回原活动 A88。','不再次预占 600 元。'],'#dcf2e6')}
${panel(414,778,354,128,'PENDING',['等待或同编号恢复。','不换新操作编号。'],'#fff0db')}
${text(32,955,'O9 成功后：可用 400 元，预占 600 元。',25,600)}
${text(32,997,'查询暂时不可用：保留结果待确认，继续核对原操作。',25)}
</g></svg>\n`;
const target=path.join(dir,'activity-creation.svg');
fs.writeFileSync(target,svg);
console.log(target);
