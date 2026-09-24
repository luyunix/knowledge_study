// Batch article QA; renders shared figures once, then checks every document.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const documents=[
  'JVM_类加载隔离与内存回收.md','Java_集合并发与缓存正确性.md',
  'Redis_数据结构热点与缓存一致性.md','MySQL_索引排序与事务可见性.md',
  '容器与服务治理_隔离发布和故障定位.md','分布式任务_分片构建恢复与发布.md',
  '搜推系统_特征时间与效果评估.md','Agent与RAG_执行恢复知识检索和评估.md',
  '算法_从状态推导LRU与最大子数组.md','工程知识学习路线.md','README.md'
];
const reports=[];
for(const [i,name] of documents.entries()) {
  const source=fs.readFileSync(path.join(root,name),'utf8');
  assert.ok(!/面试|简历|蚂蚁|得物|倪裕禄|标准录音/.test(source),`personal context leaked: ${name}`);
  if(i<9) {
    assert.ok(source.includes('理解检查'),`missing self-check: ${name}`);
    assert.ok(source.includes('```')||source.includes('|---'),`missing concrete trace: ${name}`);
  }
  const result=spawnSync(process.execPath,['scripts/render_index_figures.mjs',name],{
    cwd:root,env:{...process.env,SKIP_FIGURES:i===0?'':'1'},encoding:'utf8'
  });
  if(result.status!==0) throw new Error(`${name}\n${result.stdout}\n${result.stderr}`);
  const report=JSON.parse(result.stdout);
  reports.push(report);
  console.log(JSON.stringify({document:name,previewDir:report.previewDir,status:'passed'}));
}
const reportDir=fs.mkdtempSync(path.join(os.tmpdir(),'knowledge-foundations-qa-'));
fs.writeFileSync(path.join(reportDir,'report.json'),JSON.stringify(reports,null,2));
console.log(`All ${documents.length} documents passed. Report: ${reportDir}/report.json`);
