// Repo-native, editable diagrams. Each panel advances one concrete state.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dir=path.join(root,'assets/engineering-foundations');
fs.mkdirSync(dir,{recursive:true});
const C={ink:'#172c43',muted:'#425a70',blue:'#e2eefb',green:'#dcf2e6',orange:'#fff0db',red:'#ffe2e0',pale:'#eef3f7'};
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const text=(x,y,s,size=23,weight=400)=>`<text x="${x}" y="${y}" font-size="${size}" fill="${C.ink}" font-weight="${weight}">${esc(s)}</text>`;
function figure(name,title,subtitle,steps) {
  let body=text(24,44,title,28,600)+text(24,86,subtitle),y=112;
  for(let i=0;i<steps.length;i++) {
    const [heading,lines,color='pale']=steps[i],h=76+lines.length*34;
    body+=`<rect x="24" y="${y}" width="592" height="${h}" rx="10" fill="${C[color]}"/>`;
    body+=text(42,y+37,heading,25,600);
    body+=lines.map((s,j)=>text(42,y+79+j*34,s)).join('');
    y+=h;
    if(i<steps.length-1) body+=`<path d="M320 ${y+9} L320 ${y+35}" stroke="${C.muted}" stroke-width="2" marker-end="url(#arrow)"/>`;
    y+=48;
  }
  const height=y-16;
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="640" height="${height}" viewBox="0 0 640 ${height}" role="img" aria-labelledby="title desc"><title id="title">${esc(title)}</title><desc id="desc">${esc(steps.map(s=>s[0]+': '+s[1].join('；')).join('。'))}</desc><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="${C.muted}"/></marker></defs><rect width="640" height="${height}" fill="white"/><g font-family="PingFang SC,Microsoft YaHei,sans-serif">${body}</g></svg>\n`;
  fs.writeFileSync(path.join(dir,name+'.svg'),svg);
}
figure('01-classloader','01 路由删了，引用可能还在','只删一条路径，不等于旧对象已经不可达。',[
 ['开始：版本 A 正在服务',['路由表 → 旧对象 A → 类 A / LoaderA','长寿命线程 T → ThreadLocal → 旧对象 A'],'blue'],
 ['切换：路由改成版本 B',['路由表 → 新对象 B','旧对象 A 不再接收新路由请求。'],'green'],
 ['但线程 T 还活着',['T → ThreadLocal → A 的路径仍在。','因此 LoaderA 相关对象可能仍然可达。'],'orange'],
 ['清理与验证',['停止旧任务、解除注册、清理线程关联。','检查外部可达路径，再观察实际回收。'],'green']
]);
figure('02-lru','02 LRU：读取也会改变顺序','容量 2；左边最近使用，右边最久未用。',[
 ['① put(A,1)',['顺序：[A]；Map：A → 节点 A'],'blue'],
 ['② put(B,2)',['顺序：[B, A]；容量刚好为 2。'],'blue'],
 ['③ get(A) → 返回 1',['摘下 A，再放到头部：顺序 [A, B]。','get 并非纯读取，它修改了链表。'],'orange'],
 ['④ put(C,3)',['先成 [C, A, B]，超容量，淘汰尾部 B。','最终 [C, A]；Map 也必须删除 B。'],'green']
]);
figure('03-cache-race','03 先改库再删缓存，仍有并发窗口','数据库初值 100；缓存未命中。',[
 ['① 读请求 R 查数据库',['读到旧价格 100，尚未回填缓存。'],'blue'],
 ['② 写请求 W 更新并失效缓存',['数据库改为 80，提交成功。','随后删除缓存中的旧条目。'],'green'],
 ['③ 先前的 R 此时才回填',['R 把自己先前读到的 100 放入缓存。','数据库 = 80；缓存 = 100。'],'red'],
 ['这说明什么',['TTL 限制部分陈旧窗口，不是原子一致性。','需先确定陈旧容忍度，再选缓存协议。'],'orange']
]);
figure('04-mysql-order','04 联合索引是一种具体的排列','任务查询：集群 7、READY、优先级降序。',[
 ['先固定前缀 (cluster_id, status)',['只看 (7, READY) 这一段。','集群 8、DONE 状态不在目标段。'],'blue'],
 ['后续按 priority↓、time↑、id↑',['(9, 10:00, 10)','(9, 10:01, 11)','(3, 09:00, 12)'],'green'],
 ['取前两条：id 10、11',['当前条目顺序满足查询的排序要求。','是否采用此路径，还要看实际执行计划。'],'green'],
 ['若先按时间排，会怎样',['09:00 的 id 12 先出现，但优先级较低。','时间有序不等于目标优先级有序。'],'orange']
]);
figure('05-rollout','05 发布成功与接管流量分开看','旧版本 A 在服务；准备新版本 B。',[
 ['① 启动 B，还不接业务流量',['完成代码、依赖、配置与业务预热。','进程 Running 不等于业务就绪。'],'blue'],
 ['② 就绪后，小流量进入 B',['记录实际命中版本、实例与路由代次。','观察错误、延迟和业务验收。'],'green'],
 ['③ B 出错，路由回退到 A',['停止向 B 发送新请求，控制配置传播。','B 中已有请求并不会自动消失。'],'orange'],
 ['④ 排空或按协议处理在途请求',['已产生的副作用不能靠改路由撤销。','截止时间、幂等与补偿分别处理。'],'red']
]);
figure('06-build-recovery','06 重试失败片，不混用不同运行','同一运行 R8：快照 S3、构建定义 C5。',[
 ['① 稳定分成三个逻辑分片',['shard 0:[0,3,6]；shard 1:[1,4,7]','shard 2:[2,5,8]'],'blue'],
 ['② 各片独立生成隔离产物',['shard 0 ✓；shard 1 ✓；shard 2 ×','成功片：有完整 manifest 与已提交状态。'],'orange'],
 ['③ shard 2 发起新 attempt',['继续使用 S3/C5，校验后提交该片完成。','不可拿其他快照的文件凑齐数量。'],'green'],
 ['④ 完整性通过，再走加载与发布',['分片齐全 ≠ 内容正确 ≠ 查询已就绪。','逐层核验后才能切换在线目标。'],'green']
]);
figure('07-feature-time','07 不要把未来信息带回过去','目标：重现用户在 10:00 时的一次预测。',[
 ['① 已发生且当时可用',['09:50 点击；09:51 已到达系统。','10:00 的样本可以使用这条记录。'],'green'],
 ['② 未来事件，不能使用',['10:05 又点击一次。','把它算进 10:00 特征，就是看到了未来。'],'red'],
 ['③ 迟到事件，要核对可用性',['另一事件发生于 09:58，10:03 才到。','只看发生时间，可能夸大线上当时的信息。'],'orange'],
 ['④ 按样本目标建立时间契约',['事件时间、到达时间、特征版本分开记录。','历史关联不能直接拿今天的最新值。'],'blue']
]);
figure('08-agent-recovery','08 工具结果未知，不等于执行失败','例子：已获授权，创建一个测试部署。',[
 ['① 先保存调用意图',['operation_id = op-42；目标环境 test','权限、参数与执行版本可追溯。'],'blue'],
 ['② 工具已创建部署，但响应丢失',['工具端：op-42 → 部署 D7 已成功','Agent 端：尚未记录成功，随后崩溃。'],'orange'],
 ['③ 恢复：先查询稳定操作 ID',['查询 op-42，得知 D7 已存在。','补记结果，不再次创建 D8。'],'green'],
 ['④ 工具没有查询/幂等能力呢',['未知状态可能需要人工核验或补偿。','整任务从头重跑不等于可靠断点恢复。'],'red']
]);
console.log(`Generated 8 foundation SVG figures in ${dir}`);
