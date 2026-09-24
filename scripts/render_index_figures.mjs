// Render diagrams to PNG and validate the Markdown with a local browser.
// Requires playwright (with Chromium) and marked. Optional module-path overrides:
// PLAYWRIGHT_MODULE=/absolute/path/to/playwright/index.mjs
// MARKED_MODULE=/absolute/path/to/marked/lib/marked.esm.js
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';

const {chromium} = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const {marked} = await import(process.env.MARKED_MODULE || 'marked');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const documentName=process.argv[2] || '索引结构图解_正排与倒排.md';
const configs={
  '索引结构图解_正排与倒排.md':{images:8,dir:'assets/index-structures'},
  '索引结构进阶_FST与整数压缩.md':{images:5,dir:'assets/index-structures'},
  'Kafka到检索引擎_数据链路与高可用.md':{images:7,dir:'assets/kafka-ingestion'},
  'JVM_类加载隔离与内存回收.md':{images:1,dir:'assets/engineering-foundations'},
  'Java_集合并发与缓存正确性.md':{images:1,dir:'assets/engineering-foundations'},
  'Redis_数据结构热点与缓存一致性.md':{images:1,dir:'assets/engineering-foundations'},
  'MySQL_索引排序与事务可见性.md':{images:1,dir:'assets/engineering-foundations'},
  '容器与服务治理_隔离发布和故障定位.md':{images:1,dir:'assets/engineering-foundations'},
  '分布式任务_分片构建恢复与发布.md':{images:1,dir:'assets/engineering-foundations'},
  '搜推系统_特征时间与效果评估.md':{images:1,dir:'assets/engineering-foundations'},
  'Agent与RAG_执行恢复知识检索和评估.md':{images:1,dir:'assets/engineering-foundations'},
  '算法_从状态推导LRU与最大子数组.md':{images:0,dir:'assets/engineering-foundations'},
  '工程知识学习路线.md':{images:0,dir:'assets/engineering-foundations'},
  'README.md':{images:0,dir:'assets/engineering-foundations'}
};
const config=configs[documentName];
assert.ok(config,'Unknown document');
const expectedImages=config.images;
const dir = path.join(root, config.dir);
const browser = await chromium.launch({headless:true});
const diagnostics = [];
try {
  const page = await browser.newPage({viewport:{width:640,height:1000},deviceScaleFactor:2});
  for (const name of (process.env.SKIP_FIGURES ? [] : fs.readdirSync(dir).filter(x=>x.endsWith('.svg')).sort())) {
    await page.goto(pathToFileURL(path.join(dir,name)).href);
    await page.evaluate(()=>document.fonts.ready);
    const issues = await page.evaluate(()=>{
      const svg = document.querySelector('svg');
      const view = svg.viewBox.baseVal;
      const texts = [...svg.querySelectorAll('text')].map(t=>({label:t.textContent,rect:t.getBBox()}));
      const errors=[];
      for (const {label,rect:r} of texts) {
        if(r.x<0||r.y<0||r.x+r.width>view.width||r.y+r.height>view.height) errors.push('clipped: '+label);
      }
      for(let i=0;i<texts.length;i++) for(let j=i+1;j<texts.length;j++) {
        const a=texts[i].rect,b=texts[j].rect;
        if(Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x)>1 &&
           Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y)>1)
          errors.push('overlap: '+texts[i].label+' / '+texts[j].label);
      }
      return errors;
    });
    assert.deepEqual(issues,[],name);
    await page.locator('svg').screenshot({path:path.join(dir,name.replace('.svg','.png'))});
    diagnostics.push({file:name,textBounds:'passed'});
  }
  const docPath=path.join(root,documentName);
  const markdown=fs.readFileSync(docPath,'utf8');
  for (const match of markdown.matchAll(/!?\[[^\]]*\]\(([^)]+)\)/g)) {
    if (/^https?:|^#/.test(match[1])) continue;
    assert.ok(fs.existsSync(path.resolve(root,decodeURIComponent(match[1]))),match[1]);
  }
  const body=marked.parse(markdown);
  assert.ok(!body.includes('**'),'unparsed strong markers');
  assert.equal((body.match(/<img /g)||[]).length,expectedImages);
  const previewDir=fs.mkdtempSync(path.join(os.tmpdir(),'knowledge-index-preview-'));
  const html=`<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><base href="${pathToFileURL(root+path.sep).href}"><title>${documentName.replace(/\.md$/, '')}</title><style>
    *{box-sizing:border-box}body{margin:0;background:#fff;color:#172c43;font:17px/1.8 'PingFang SC',sans-serif}
    main{max-width:820px;margin:auto;padding:28px 24px 80px}h1{font-size:30px;line-height:1.4}h2{font-size:25px;margin-top:50px}h3{font-size:21px}
    img{display:block;width:min(100%,640px);height:auto;margin:24px auto}a{color:#1758a4}pre{padding:16px;overflow:auto;background:#eef3f7;font-size:15px}code{font-family:ui-monospace,monospace}table{width:100%;border-collapse:collapse;font-size:15px}th,td{padding:8px;border-bottom:1px solid #cbd5e1;text-align:left;overflow-wrap:anywhere}p,li{overflow-wrap:anywhere}ul,ol{padding-left:25px}
    @media(max-width:480px){main{padding:18px 16px 50px}body{font-size:16px}h1{font-size:26px}h2{font-size:23px}}
  </style></head><body><main>${body}</main></body></html>`;
  const preview=path.join(previewDir,'index.html');
  fs.writeFileSync(preview,html);
  for(const width of [960,390]) {
    await page.setViewportSize({width,height:900});
    await page.goto(pathToFileURL(preview).href);
    await page.evaluate(()=>document.fonts.ready);
    assert.equal(await page.locator('img').count(),expectedImages);
    const result=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,
      missing:[...document.images].filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.src)}));
    assert.equal(result.overflow,false);
    assert.deepEqual(result.missing,[]);
    await page.screenshot({path:path.join(previewDir,`article-${width}.png`)});
    if(expectedImages) {
      await page.locator('img').first().scrollIntoViewIfNeeded();
      await page.screenshot({path:path.join(previewDir,`figure-${width}.png`)});
    }
    diagnostics.push({width,...result});
  }
  console.log(JSON.stringify({documentName,diagnostics,previewDir},null,2));
} finally {
  await browser.close();
}
