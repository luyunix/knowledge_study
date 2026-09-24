// Generate deterministic, editable SVG diagrams. No dependencies required.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dir = path.join(root, 'assets/index-structures');
fs.mkdirSync(dir, {recursive:true});
const W = 640;
const C = {ink:'#172c43', muted:'#425a70', line:'#b8c7d4', pale:'#eef3f7', blue:'#e2eefb', green:'#dcf2e6', orange:'#fff0db', white:'#ffffff'};
const esc = s => String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
function text(x,y,s,size=24,color=C.ink,weight=400) {
  return `<text x="${x}" y="${y}" font-size="${size}" fill="${color}" font-weight="${weight}">${esc(s)}</text>`;
}
function box(x,y,w,h,fill=C.pale) {
  return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="9" fill="${fill}"/>`;
}
function arrow(x1,y1,x2,y2) {
  return `<path d="M ${x1} ${y1} L ${x2} ${y2}" stroke="${C.muted}" stroke-width="2" fill="none" marker-end="url(#arrow)"/>`;
}
function panel(y,h,title,lines,fill=C.pale) {
  return box(24,y,592,h,fill)+text(42,y+37,title,25,C.ink,600)+lines.map((s,i)=>text(42,y+79+i*34,s,23)).join('');
}
function array(x,y,values,active=-1,width=72) {
  return values.map((v,i)=>box(x+i*(width+8),y,width,48,i===active?C.orange:C.pale)+text(x+i*(width+8)+16,y+33,String(v),25)).join('');
}
function save(name,title,h,body,desc) {
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${h}" viewBox="0 0 ${W} ${h}" role="img" aria-labelledby="title desc"><title id="title">${esc(title)}</title><desc id="desc">${esc(desc)}</desc><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M 0 0 L 8 4 L 0 8 Z" fill="${C.muted}"/></marker></defs><rect width="640" height="${h}" fill="${C.white}"/><g font-family="PingFang SC, Microsoft YaHei, sans-serif">${text(24,44,title,28,C.ink,600)}${body}</g></svg>\n`;
  fs.writeFileSync(path.join(dir, name+'.svg'),svg);
}

let b=text(24,83,'业务 ID 是名字；docID 是本段内的整数编号。',23,C.muted);
const docs=[['D1',0,['Python','部署','超时','排查']],['D2',1,['Java','部署','配置','指南']],['D3',2,['Python','请求','超时','超时','处理']],['D4',3,['Python','部署','参数','参数','参数','检查']]];
for(let j=0;j<docs.length;j++) {
  const [id,num,words]=docs[j], y=110+j*142;
  b+=box(24,y,592,128)+text(40,y+34,`${id} → docID ${num}`,24,C.ink,600);
  words.forEach((word,i)=>{
    b+=box(40+i*92,y+47,84,40,(word==='超时')?C.orange:C.white)+text(45+i*92,y+75,word,21);
    b+=text(72+i*92,y+111,String(i+1),22,C.muted);
  });
}
b+=text(24,712,'每个词下面的数字 = 它在文档里的位置。',23,C.muted);
save('01-document-ids','01 先给四条文档编号',744,b,'D1 到 D4 分别映射 docID 0 到 3。词位置从 1 开始；D3 的超时出现在位置 3 和 4。');

b=panel(80,122,'任务：已知 docID = 2，读取它的字段',['先找第 2 号记录，再读 D3 的内容与属性。'],C.blue);
b+=text(24,249,'按文档组织：同一篇文档的字段放在一起',23,C.ink,600);
['0 → D1 | A | v2','1 → D2 | A | v1','2 → D3 | B | v2','3 → D4 | A | v2'].forEach((s,i)=>{b+=box(24,271+i*53,592,45,i===2?C.orange:C.pale)+text(42,302+i*53,s,24);});
b+=text(24,525,'按字段组织：先选列，再定位下标 2',23,C.ink,600);
b+=text(24,569,'docID',23)+array(170,537,[0,1,2,3],2);
b+=text(24,634,'租户列',23)+array(170,602,['A','A','B','A'],2);
b+=text(24,699,'版本列',23)+array(170,667,['v2','v1','v2','v2'],2);
b+=panel(755,155,'两种布局，访问方向相同',['都是从 docID 出发取字段值。','列式适合批量读取同一个字段。'],C.green);
save('02-forward-layout','02 正排：给编号，取字段',938,b,'上半部按文档排记录；下半部按字段排数组。docID 2 在两种布局中都对应租户 B、SDK v2。');

b=panel(80,160,'把“超时”的出现记录挑出来',['D1 第 3 个词 → (超时, 0, 3)','D3 → (超时, 2, 3)、(超时, 2, 4)']);
b+=arrow(320,250,320,283);
b+=panel(294,187,'按词、docID、位置整理',['(超时, 0, 3)','(超时, 2, 3)','(超时, 2, 4)'],C.blue);
b+=arrow(320,491,320,524);
b+=panel(535,155,'相同 docID 合成一条记录',['docID 0 → 次数 1，位置 [3]','docID 2 → 次数 2，位置 [3, 4]'],C.green);
b+=panel(723,155,'没有改变：原文仍然存在',['新增的是另一种查找方式：','给“超时”，就能找到文档 0 和 2。']);
save('03-build-postings','03 倒排不是复制一遍正文',906,b,'将三个词出现记录分组为两个文档记录。D3 的重复词变成词频 2，而不是两个重复 docID。');

b=panel(80,154,'词典中的一个条目',['字段：content；词：超时','df = 2；总出现次数 = 3'],C.blue);
b+=arrow(320,244,320,285)+text(64,326,'该词的元信息定位下面这些数据',24,C.ink,600);
b+=text(24,390,'docID 流')+array(234,357,[0,2],-1,120);
b+=text(24,461,'词频流')+array(234,428,[1,2],-1,120);
b+=text(24,532,'位置流')+array(234,499,[3,3,4],-1,78);
b+=text(24,580,'先取 1 个位置给 docID 0，再取 2 个给 docID 2。',22,C.muted);
b+=panel(620,155,'解码后看到的逻辑记录',['docID 0 | tf 1 | positions [3]','docID 2 | tf 2 | positions [3, 4]'],C.green);
b+=text(24,818,'分流示意，不是 Lucene 文件的逐字节布局。',23,C.muted);
save('04-posting-streams','04 一个词后面，究竟存了什么',850,b,'词典通过元信息定位 docID、词频和位置数据。词频决定给每篇文档读多少个位置。');

function stage(y,n,ai,bi,note,result) {
 let s=box(24,y,592,194)+text(40,y+34,`第 ${n} 步`,24,C.ink,600);
 s+=text(40,y+81,'部署',23)+array(155,y+47,[0,1,3],ai);
 s+=text(40,y+140,'超时',23)+array(155,y+106,[0,2],bi);
 s+=text(412,y+84,'已收集',22,C.muted)+text(412,y+129,result,25);
 s+=text(40,y+180,note,22);
 return s;
}
b=text(24,83,'查询：部署 AND 超时；橙色 = 当前游标。',23,C.muted);
b+=stage(108,1,0,0,'0 = 0：收集 0；两个游标都前进。','[] → [0]');
b+=stage(323,2,1,1,'1 < 2：只前进“部署”的游标。','[0]');
b+=stage(538,3,2,1,'3 > 2：只前进“超时”的游标。','[0]');
b+=panel(760,155,'“超时”列表耗尽，立即停止',['交集为 [0]，对应业务文档 D1。','全程比较整数，不需要逐篇读取正文。'],C.green);
save('05-intersection','05 两个游标怎样求交集',943,b,'游标依次比较 0 与 0、1 与 2、3 与 2；命中 0 后右侧耗尽，返回 D1。');

b=panel(80,154,'有序 docID 可以换成差值',['原编号： [3, 10, 11, 20]','差值：   [3,  7,  1,  9]'],C.blue);
b+=text(24,275,'下面用另一条长列表，演示按块跳过：',23,C.muted);
const blocks=[['[2, 4, 7]','最大值 7 < 20：跳过'],['[12, 15, 18]','最大值 18 < 20：跳过'],['[25, 29, 31]','最大值 31 ≥ 20：解码']];
blocks.forEach((r,i)=>{b+=panel(300+i*150,130,r[0],[r[1]],i===2?C.green:C.pale);});
b+=panel(770,155,'advance(20) 的结果是 25',['它寻找的是“第一个 ≥ 20”的 docID。','不是要求列表里一定存在 20。'],C.orange);
b+=text(24,965,'块大小、元信息和编码方式由具体格式决定。',23,C.muted);
save('06-compress-skip','06 少存一些，少解码一些',995,b,'差值需配合紧凑编码才节省空间；块最大值和定位信息可跳过不可能命中的块。此处不是四条文档的数据。');

b=panel(80,124,'输入：部署 AND 超时',['两词都必须出现在同一篇文档。'],C.blue);
b+=arrow(320,214,320,251);
b+=panel(263,158,'先查词典，再读取两个列表',['部署 → [0, 1, 3]','超时 → [0, 2]']);
b+=arrow(320,431,320,468);
b+=panel(480,122,'求交集 → [0]',['0 是文档编号，不是相关性排名。'],C.orange);
b+=arrow(320,612,320,649);
b+=panel(661,157,'按 docID 0 读取结果字段',['D1：Python 部署 超时 排查','租户 A；SDK v2'],C.green);
b+=text(24,858,'倒排定位候选；按文档取值提供结果内容。',23,C.muted);
save('07-query-path','07 两种访问方向怎样配合',890,b,'从查询词经词典和倒排取交集得到 docID 0，再按文档读取 D1 字段。');

b=text(24,83,'用 car、cat、dog 展示共享前缀。',23,C.muted);
function node(x,y,label,fill=C.pale){return box(x,y,68,52,fill)+text(x+17,y+35,label,25);}
b+=arrow(92,239,170,166)+arrow(92,254,170,362);
b+=arrow(238,156,305,156)+arrow(238,362,305,362);
b+=arrow(373,147,443,127)+arrow(373,167,443,239);
b+=arrow(373,362,443,362);
b+=node(24,214,'根')+node(170,130,'c',C.blue)+node(305,130,'a',C.blue);
b+=node(443,101,'r')+node(443,213,'t',C.green);
b+=node(170,336,'d')+node(305,336,'o')+node(443,336,'g');
b+=text(526,138,'car',22)+text(526,250,'cat',22)+text(526,373,'dog',22);
b+=panel(431,154,'查 cat：根 → c → a → t',['若不存在对应分支，就可以停止。','路径节点表示词的字节或字符，不是文档。'],C.green);
b+=panel(617,155,'接到词典块，再接到倒排数据',['这张图只解释前缀查找。','不是某个 Lucene 版本的实际文件布局。']);
save('08-term-trie','08 词典也需要“目录”',800,b,'car 和 cat 共享 c、a 两层路径。词典索引用前缀信息帮助定位包含目标词的词典块。');

// Deeper word-dictionary and integer-codec illustrations.
b=text(24,84,'词集合：bar、bat、car、cat',23,C.muted);
b+=text(24,125,'Trie：相同后续路径，仍各存一份',24,C.ink,600);
b+=arrow(92,246,176,184)+arrow(92,260,176,342);
b+=arrow(244,184,318,184)+arrow(244,342,318,342);
b+=arrow(386,175,478,157)+arrow(386,193,478,237);
b+=arrow(386,333,478,317)+arrow(386,351,478,397);
b+=node(24,226,'根')+node(176,158,'b')+node(176,316,'c');
b+=node(318,158,'a',C.blue)+node(318,316,'a',C.blue);
b+=node(478,131,'r',C.green)+node(478,211,'t',C.green)+node(478,291,'r',C.green)+node(478,371,'t',C.green);
b+=text(24,477,'合并后：等价的后续结构共同指向同一状态',23,C.ink,600);
b+=node(24,547,'S0')+node(252,547,'S1',C.blue)+node(490,547,'S2',C.blue)+node(490,726,'S3',C.green);
b+=arrow(92,573,250,573)+text(118,550,'b 或 c',23);
b+=arrow(320,573,488,573)+text(390,550,'a',23);
b+=arrow(524,607,524,724)+text(393,676,'r 或 t',23);
b+=panel(811,155,'只回答“这个词在不在集合中”',['Trie：9 个状态；合并后：4 个状态。','S3 是接受态；走到 S1 / S2 还不算命中。'],C.green);
save('09-trie-fsa','09 从共享前缀到共享等价状态',995,b,'四个词的 trie 有九个状态。相同的剩余语言允许合并状态，得到四状态自动机；这是集合识别，不是带值映射。');

b=text(24,83,'bar→20，bat→21，car→10，cat→11',23,C.muted);
b+=node(24,178,'S0')+node(252,178,'S1',C.blue)+node(252,377,'S2',C.blue)+node(500,377,'S3',C.green);
b+=`<path d="M92 188 C140 112 208 112 252 188" stroke="${C.muted}" stroke-width="2" fill="none" marker-end="url(#arrow)"/>`;
b+=`<path d="M92 220 C140 298 208 298 252 220" stroke="${C.muted}" stroke-width="2" fill="none" marker-end="url(#arrow)"/>`;
b+=text(140,127,'b / +20',23)+text(140,315,'c / +10',23);
b+=arrow(286,240,286,370)+text(130,356,'a / +0',23);
b+=`<path d="M320 387 C368 311 448 311 500 387" stroke="${C.muted}" stroke-width="2" fill="none" marker-end="url(#arrow)"/>`;
b+=`<path d="M320 419 C368 494 448 494 500 419" stroke="${C.muted}" stroke-width="2" fill="none" marker-end="url(#arrow)"/>`;
b+=text(370,309,'r / +0',23)+text(370,510,'t / +1',23);
b+=panel(552,191,'沿 cat 路径，把输出累加起来',['读 c：S0 → S1，累计 10','读 a：S1 → S2，累计 10','读 t：S2 → S3，累计 11'],C.green);
b+=panel(780,155,'接受态 S3：终态输出为 0',['最终结果：10 + 0 + 1 + 0 = 11。','这是手工教学 FST，不是 Lucene 字节格式。']);
save('10-fst-outputs','10 FST：读字符，同时产生输出',963,b,'边标签的斜杠左侧是输入字符，右侧是本例要相加的输出。b 和 c 的路径输出不同，但剩余映射相同，故共享后续状态。');

b=panel(80,157,'300 = 44 + 2 × 128',['低 7 位是 44：0101100','余下部分是 2：0000010'],C.blue);
b+=arrow(320,247,320,284);
b+=panel(295,156,'先写低位组，再写高位组',['第 1 字节：1 | 0101100 = AC','第 2 字节：0 | 0000010 = 02'],C.orange);
b+=panel(488,155,'最高位不是数值的一部分',['1：后面还有字节，继续读。','0：当前整数结束。']);
b+=panel(680,188,'解码：剥掉最高位，再移位累加',['AC & 7F = 44','02 & 7F = 2；2 左移 7 位 = 256','44 + 256 = 300'],C.green);
b+=text(24,909,'这里采用 Lucene VInt 的延续位约定。',23,C.muted);
save('11-vint','11 一个整数怎样变成两个字节',940,b,'300 编码为十六进制 AC 02；每字节低七位是数据，高位一表示继续，高位零表示结束。');

b=panel(80,154,'先做差分，得到一块小整数',['docID：[3, 10, 11, 20]','差值： [3, 7, 1, 9]'],C.blue);
b+=panel(270,156,'最大值 9，需要 4 个二进制位',['3 → 0011；7 → 0111','1 → 0001；9 → 1001']);
b+=arrow(320,436,320,473);
b+=panel(484,155,'教学约定：按高位在前拼接',['0011 0111 0001 1001','得到两个字节：37 19'],C.green);
b+=panel(675,155,'解码需要知道：位宽 4、数量 4',['每次取 4 位 → 3、7、1、9','再做前缀和 → 3、10、11、20'],C.orange);
b+=text(24,872,'2 字节只计算载荷，不包含位宽与数量等元信息。',22,C.muted);
save('12-bitpacking','12 一块整数怎样紧凑排列',902,b,'差值数组四个数以四位宽打包，载荷十六进制为 37 19；取出后累加还原文档编号。');

b=panel(80,155,'换一块数据：[3, 7, 1, 129]',['只有最后一个数特别大。','统一位宽需要 8 bit × 4 = 32 bit。'],C.blue);
b+=panel(273,155,'尝试只给每个数 3 bit',['低位部分：[3, 7, 1, 1]','前三个数完整；129 的高位丢了。'],C.orange);
b+=panel(466,155,'另外记录异常位置与高位',['异常下标：3；额外高位：16','129 = 1 + (16 << 3)'],C.green);
b+=panel(659,188,'恢复时，把异常的高位补回去',['普通数：按 3 bit 解码。','下标 3：1 + 128 = 129。','总成本还要加异常位置、高位和头部。']);
b+=text(24,889,'这是 PFOR 类方法的思想，不是具体 codec 规范。',22,C.muted);
save('13-patched-block','13 一个异常值，不必拖累整块',920,b,'一个大值使整块位宽增加；可另存异常位置和高位。是否更小取决于额外元数据，不保证微型示例节省字节。');
console.log(`Generated 13 SVG diagrams in ${dir}`);
