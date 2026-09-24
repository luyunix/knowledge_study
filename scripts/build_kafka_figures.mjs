// Deterministic SVG source figures for the Kafka ingestion walkthrough.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dir=path.join(root,'assets/kafka-ingestion');
fs.mkdirSync(dir,{recursive:true});
const C={ink:'#172c43',muted:'#425a70',pale:'#eef3f7',blue:'#e2eefb',green:'#dcf2e6',orange:'#fff0db',red:'#ffe2e0'};
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const text=(x,y,s,size=23,color=C.ink,weight=400)=>`<text x="${x}" y="${y}" font-size="${size}" fill="${color}" font-weight="${weight}">${esc(s)}</text>`;
const box=(x,y,w,h,fill=C.pale)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="10" fill="${fill}"/>`;
const arrow=(x1,y1,x2,y2)=>`<path d="M${x1} ${y1} L${x2} ${y2}" stroke="${C.muted}" stroke-width="2" fill="none" marker-end="url(#arrow)"/>`;
function panel(y,title,lines,fill=C.pale) {
  const h=72+lines.length*34;
  return box(24,y,592,h,fill)+text(42,y+37,title,25,C.ink,600)+lines.map((s,i)=>text(42,y+77+i*34,s)).join('');
}
function save(name,title,h,body,desc) {
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="640" height="${h}" viewBox="0 0 640 ${h}" role="img" aria-labelledby="title desc"><title id="title">${esc(title)}</title><desc id="desc">${esc(desc)}</desc><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="${C.muted}"/></marker></defs><rect width="640" height="${h}" fill="white"/><g font-family="PingFang SC,Microsoft YaHei,sans-serif">${text(24,44,title,28,C.ink,600)}${body}</g></svg>\n`;
  fs.writeFileSync(path.join(dir,name+'.svg'),svg);
}

let b=panel(78,'初始：P42 价格 100，业务版本 7',['目标：改成 80，并让搜索随后更新。'],C.blue);
b+=arrow(320,194,320,224);
b+=panel(236,'① 一个数据库事务，一起提交',['商品表：P42 → 价格 80，版本 8','Outbox：evt-P42-8 → 待发送'],C.green);
b+=arrow(320,386,320,418);
b+=panel(430,'② 独立搬运程序发送事件',['Kafka key = shopA:P42','收到确认后记录发送进度；允许重试。']);
b+=arrow(320,580,320,612);
b+=panel(624,'③ 消费并写入引擎，再变成可见',['引擎可靠保存：价格 80，版本 8','查询视图刷新后：搜索返回 80。'],C.blue);
b+=panel(794,'检查故障：搬运程序现在死了？',['商品与 Outbox 已一起提交，不会丢待办。','但再次发送可能重复，后面仍需幂等。'],C.orange);
save('01-outbox','01 改数据时，也留下可靠的待办',966,b,'数据库商品行与 Outbox 同事务；Kafka 与引擎在事务边界外，通过允许重试衔接。');

b=text(24,87,'同组成员分工；不是每人收到全部消息。',23,C.muted);
for(const [x,p,key,c] of [[24,'p0','P42','C1'],[332,'p1','P17','C2']]) {
  b+=box(x,116,284,138,C.blue)+text(x+18,153,`分区 ${p}`,25,C.ink,600)+text(x+18,194,`${key} 的变化`)+text(x+18,231,'各自有一串 offset');
  b+=arrow(x+142,264,x+142,304);
  b+=box(x,318,284,105,C.green)+text(x+18,356,`接入实例 ${c}`,25,C.ink,600)+text(x+18,397,'组：index-G1');
}
b+=arrow(166,435,260,485)+arrow(474,435,380,485);
b+=panel(499,'接入层按业务 ID 路由到引擎分片',['例如 C1 将 P42 写到引擎分片 S0。']);
b+=arrow(320,615,320,647);
b+=panel(659,'引擎分片 S0：自己维护副本',['主副本接收写入 → 按引擎协议复制','查询副本须恢复就绪，才能承接流量。'],C.blue);
b+=panel(829,'错误接法：完整副本 A/B 同组分工',['A 只收到 p0，B 只收到 p1，都会缺数据。','若独立重放，必须让每个副本读到所需流。'],C.orange);
save('02-consumer-routing','02 消费者分工，不等于引擎复制',1000,b,'p0 分配 C1，p1 分配 C2。消费者组分工后写引擎；引擎副本一致性由自己的复制协议负责。');

b=panel(78,'起点：恢复位置 100；价格 100',['p0 / offset 100：版本 8，价格设为 80'],C.blue);
b+=arrow(320,194,320,225);
b+=panel(237,'① 引擎写入成功',['引擎：价格 80，版本 8','组的恢复位置：仍然是 100'],C.green);
b+=panel(405,'② 宕机：还没来得及提交 101',['引擎状态保留；本机在途工作消失。'],C.red);
b+=arrow(320,520,320,552);
b+=panel(564,'③ 重启，从已提交位置 100 读取',['再次收到：版本 8，价格设为 80','发现相同版本和内容 → 无需再次改变状态。'],C.orange);
b+=arrow(320,714,320,746);
b+=panel(758,'④ 提交 101：下次从这里恢复',['投递尝试 2 次；状态变化 1 次。','重复投递 ≠ 重复生效。'],C.green);
save('03-crash-replay','03 把宕机放在两个成功之间',930,b,'写引擎后、提交前宕机导致重放。版本幂等使两次投递只改变一次状态。');

b=text(24,88,'原子保存：业务版本 + 正文 + 删除状态。',23,C.muted);
const rows=[
 ['起始状态','版本 7，价格 100',C.pale],
 ['收到版本 8，价格 80','8 > 7：应用 → (8, 80)',C.green],
 ['又收到版本 8，价格 80','版本和内容相同：不再改变',C.blue],
 ['收到版本 9，价格 75','9 > 8：应用 → (9, 75)',C.green],
 ['迟来版本 8，价格 80','8 < 9：拒绝旧状态，仍是 75',C.orange],
 ['收到版本 10，删除','保留 (10, 已删除)，搜索不返回',C.green],
 ['再来版本 8，价格 80','8 < 10：不允许商品复活',C.orange]
];
rows.forEach(([title,line,fill],i)=>{b+=panel(112+i*131,title,[line],fill);});
b+=text(24,1057,'同版本内容不同：报冲突，不当作正常重试。',23,C.muted);
save('04-version-guard','04 去重之外，还要防旧状态覆盖',1088,b,'七个状态逐步显示重复、旧版本、删除与旧消息重放。相同版本不同内容属于异常。');

b=panel(78,'p0 已投递：100、101、102',['初始恢复位置为 100；工作线程并行执行。'],C.blue);
const cell=(x,label,status,fill)=>box(x,235,184,116,fill)+text(x+16,274,label,25,C.ink,600)+text(x+16,319,status);
b+=cell(24,'offset 100','还在重试',C.orange)+cell(228,'offset 101','可靠完成',C.green)+cell(432,'offset 102','可靠完成',C.green);
b+=panel(390,'现在最多只能保留恢复位置 100',['如果提交 103，重启会跳过未完成的 100。','成功的最大编号 ≠ 安全提交位置。'],C.red);
b+=arrow(320,541,320,574);
b+=panel(586,'稍后：100 也可靠完成了',['100 ✓    101 ✓    102 ✓','已完成前缀覆盖全部三条，才可提交 103。'],C.green);
b+=panel(756,'真实日志的 offset 可能不连续',['按实际投递顺序跟踪，不等待缺失整数。','不同分区分别计算，不能共用一个最大值。']);
save('05-commit-frontier','05 提交进度不能越过未完成的洞',928,b,'100 未完成而 101、102 完成时不能提交 103。100 也完成后才推进到 103。');

b=panel(78,'① 一致性快照 + 可追溯重放边界',['快照 S：P42 = (版本 7，价格 100)','简化示例：后续从 p0 / offset 100 重放。'],C.blue);
b+=arrow(320,228,320,260);
b+=panel(272,'② G1 服务；用快照构建新代次 G2',['构建期间业务继续变化，Kafka 保留增量：','100 → (8, 80)；101 → (9, 75)'],C.orange);
b+=arrow(320,422,320,454);
b+=panel(466,'③ G2 加载后，从 100 追赶',['G2：(7, 100) → (8, 80) → (9, 75)','安全恢复位置推进到 102，继续跟随新数据。'],C.green);
b+=arrow(320,616,320,648);
b+=panel(660,'④ 达到切换门槛，路由到 G2',['校验各分区进度、查询可见与数据完整性。','继续增量消费；保留可恢复的旧代次。'],C.blue);
b+=panel(830,'图中只画一个分区，便于推演',['真实边界通常是位置向量，不是一个时间。','G1 已处理，不能成为 G2 跳过事件的理由。']);
save('06-full-and-incremental','06 构建期间的变化，靠重放补齐',1002,b,'快照与源日志协议建立边界；G2 构建时保留增量，加载后追赶再验证切换。');

b=text(24,87,'教学条件：3 副本，minISR=2，acks=all',23,C.muted);
b+=text(24,123,'传统 ISR 模型；未启用 ELR。',23,C.muted);
const replicaRow=(y,labels,colors)=>labels.map((v,i)=>box(24+i*204,y,184,62,colors[i])+text(39+i*204,y+39,v,24)).join('');
b+=text(24,181,'情况 A：三个副本都在 ISR',25,C.ink,600);
b+=replicaRow(205,['B1 主','B2 同步','B3 同步'],[C.blue,C.green,C.green]);
b+=text(24,307,'当前 ISR = {B1, B2, B3}；都确认才成功。');
b+=text(24,376,'情况 B：B3 故障，已移出 ISR',25,C.ink,600);
b+=replicaRow(400,['B1 主','B2 同步','B3 故障'],[C.blue,C.green,C.red]);
b+=text(24,502,'当前 ISR = {B1, B2}；满足 2，仍可写。');
b+=text(24,571,'情况 C：再失去 B2，只剩一个',25,C.ink,600);
b+=replicaRow(595,['B1 主','B2 故障','B3 故障'],[C.blue,C.red,C.red]);
b+=text(24,697,'当前 ISR = {B1}；不足 2，不能确认成功。');
b+=panel(738,'这是一种取舍，不是绝对不出故障',['副本不足时停止承诺成功写入。','选主过程仍可能短暂不可用，需要重试。'],C.orange);
b+=panel(908,'另一套机制：KRaft 控制器仲裁',['三个投票控制器需要多数派存活。','不要把控制器仲裁当成数据分区的 ISR。'],C.blue);
save('07-replicas-and-isr','07 副本数、ISR、确认门槛分开看',1080,b,'三种状态分别显示 ISR 为 3、2、1 时的写入确认条件。控制器多数派属于独立机制。');
console.log(`Generated 7 SVG figures in ${dir}`);
