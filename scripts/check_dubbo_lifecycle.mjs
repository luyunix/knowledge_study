// Source fingerprints, editable figures and rendered documents; not RPC integration.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const privateRoot=path.resolve(root,'../victory_study');
const {marked}=await import(process.env.MARKED_MODULE||'marked');
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const lock=JSON.parse(fs.readFileSync(path.join(root,'sources/dubbo-lifecycle-lock.json'),'utf8'));
assert.equal(lock.commit,'1dd6a4aaa8816cf3f1585769dfff4f325e4ecd15');
assert.equal(new Set(lock.files.map(f=>f.path)).size,25);
for(const file of lock.files){
 const bytes=fs.readFileSync(path.join(root,'.source-cache/dubbo',lock.commit,file.path));
 assert.equal(createHash('sha256').update(bytes).digest('hex'),file.sha256,file.path);
 const lines=bytes.toString('utf8').split('\n');
 for(const [symbol,numbers] of Object.entries(file.symbols))assert.ok(numbers.length&&numbers.every(n=>lines[n-1].includes(symbol)),symbol);
}
const tutorial='Dubbo多版本服务_发布发现路由与下线全链路.md';
const privateDoc='业务研发平台_Dubbo完整链路与源码追问.md';
const publicText=fs.readFileSync(path.join(root,tutorial),'utf8');
assert.ok(!/面试|倪裕禄|蚂蚁|得物|working\/transcripts/.test(publicText),'Private context leaked into knowledge article');
const privateText=fs.readFileSync(path.join(privateRoot,privateDoc),'utf8');
assert.deepEqual([...privateText.matchAll(/^### (D\d{2})｜/gm)].map(m=>m[1]),Array.from({length:20},(_,i)=>'D'+String(i+1).padStart(2,'0')));
assert.equal((fs.readFileSync(path.join(root,'examples/dubbo_lifecycle_model.py'),'utf8').match(/^    def test_/gm)||[]).length,14);
const figures=['01-shared-runtime','02-dubbo-runtime','03-publish-discovery','04-request-path','05-drain','06-control-and-discovery'];
const docs=[...[[root,tutorial],[root,'README.md'],[root,'多版本研发平台_部署路由与Dubbo服务发现.md'],[root,'实现详解_22_Dubbo目录路由与版本候选.md']],
 [privateRoot,privateDoc],[privateRoot,'业务研发平台_技术专家全景追问与回答.md'],[privateRoot,'00_目录.md']];
const output=fs.mkdtempSync(path.join(os.tmpdir(),'dubbo-lifecycle-qa-'));
const report={sourceFiles:lock.files.length,figures:[],documents:[],output};
const browser=await chromium.launch({headless:true});
try{
 const page=await browser.newPage({viewport:{width:1050,height:1000},deviceScaleFactor:2});
 for(const name of figures){
  const svg=path.join(root,'assets/dubbo-lifecycle',name+'.svg');
  await page.goto(pathToFileURL(svg).href);await page.evaluate(()=>document.fonts.ready);
  const issues=await page.evaluate(()=>{
   const s=document.querySelector('svg'),v=s.viewBox.baseVal,problems=[];
   const text=[...s.querySelectorAll('text')].map(e=>({s:e.textContent,b:e.getBBox()}));
   for(const t of text)if(t.b.x<0||t.b.y<0||t.b.x+t.b.width>v.width||t.b.y+t.b.height>v.height)problems.push('clip '+t.s);
   for(let i=0;i<text.length;i++)for(let j=i+1;j<text.length;j++){
    const a=text[i].b,b=text[j].b;
    if(Math.min(a.x+a.width,b.x+b.width)>Math.max(a.x,b.x)+1&&Math.min(a.y+a.height,b.y+b.height)>Math.max(a.y,b.y)+1)problems.push('text overlap '+text[i].s+'/'+text[j].s);
   }
   for(const p of s.querySelectorAll('[data-arrow]')){
    if(/[CQSA]/i.test(p.getAttribute('d')))problems.push('curved arrow');
    for(let n=0;n<=p.getTotalLength();n+=2){const point=p.getPointAtLength(n);for(const t of text)if(point.x>t.b.x-1&&point.x<t.b.x+t.b.width+1&&point.y>t.b.y-1&&point.y<t.b.y+t.b.height+1)problems.push('arrow over text '+t.s);}
    const start=p.getPointAtLength(0),end=p.getPointAtLength(p.getTotalLength());
    const rectangles=[...s.querySelectorAll('rect')].filter(r=>Number(r.getAttribute('width'))<v.width);
    const edgeDistance=point=>{
     let best=Infinity;
     for(const r of rectangles){
      const x=r.x.baseVal.value,y=r.y.baseVal.value,w=r.width.baseVal.value,h=r.height.baseVal.value;
      for(const [x1,y1,x2,y2] of [[x,y,x,y+h],[x+w,y,x+w,y+h],[x,y,x+w,y],[x,y+h,x+w,y+h]]){
       const nearestX=Math.max(Math.min(point.x,Math.max(x1,x2)),Math.min(x1,x2));
       const nearestY=Math.max(Math.min(point.y,Math.max(y1,y2)),Math.min(y1,y2));
       best=Math.min(best,Math.hypot(point.x-nearestX,point.y-nearestY));
      }
     }
     return best;
    };
    if(edgeDistance(start)>8||edgeDistance(end)>8)problems.push('unattached arrow');
   }
   if(s.querySelector('rect[rx],rect[ry]'))problems.push('rounded rectangle');
   return [...new Set(problems)];
  });
  assert.deepEqual(issues,[],name);
  await page.locator('svg').screenshot({path:path.join(root,'assets/dubbo-lifecycle',name+'.png')});
  report.figures.push({name,geometry:'passed',png:'generated'});
 }
 for(const [folder,name] of docs){
  const source=fs.readFileSync(path.join(folder,name),'utf8');
  const htmlBody=marked.parse(source);
  assert.ok(!htmlBody.includes('**'),'Unparsed bold '+name);
  const targets=[];
  marked.walkTokens(marked.lexer(source),token=>{if(token.type==='link'||token.type==='image')targets.push(token.href);if(token.type==='code'&&token.lang==='json')JSON.parse(token.text);});
  for(const target of targets){if(/^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|#)/.test(target))continue;assert.ok(fs.existsSync(path.resolve(folder,decodeURIComponent(target.split('#')[0]))),name+' '+target);}
  const html=`<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><base href="${pathToFileURL(folder+path.sep).href}"><meta name="viewport" content="width=device-width,initial-scale=1"><style>*{box-sizing:border-box}body{margin:0;background:white;color:#111;font:17px/1.85 'PingFang SC',sans-serif}main{max-width:940px;margin:auto;padding:24px}h1{font-size:28px}h2{font-size:23px}h3{font-size:20px}p,li,a,td,th{overflow-wrap:anywhere}pre{overflow:auto;padding:12px;background:#f8f8f8}img{display:block;width:100%;height:auto;margin:24px auto}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:7px;border-bottom:1px solid #ccc}blockquote{margin:16px 0;border-left:2px solid #bbb;padding-left:16px}ul,ol{padding-left:24px}@media(max-width:480px){main{padding:16px}body{font-size:16px}}</style></head><body><main>${htmlBody}</main></body></html>`;
  const preview=path.join(output,'document.html');fs.writeFileSync(preview,html);
  for(const width of [960,390]){
   await page.setViewportSize({width,height:1000});await page.goto(pathToFileURL(preview).href);await page.evaluate(()=>document.fonts.ready);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,name+' overflow '+width);
   assert.deepEqual(await page.evaluate(()=>[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src)),[],name+' missing images');
   if(name===tutorial||name===privateDoc){
    const titles=name===tutorial?['7. 地址与规则乱序：必须讲清本地保证','8. 下线：撤注册、拒新、排空和销毁不是同一个动作','11. Python扩展：协议互通与发现互通分开验证']:['D07｜Dubbo 3的refer是不是直接new RegistryDirectory？','D10｜收到空地址列表，为什么Proxy还可能继续调用旧地址？','D16｜撤注册后sleep几秒再杀Pod，为什么还不能叫无损？'];
    for(const [i,title] of titles.entries()){await page.getByRole('heading',{name:title,exact:true}).scrollIntoViewIfNeeded();await page.screenshot({path:path.join(output,(name===tutorial?'public':'private')+'-'+i+'-'+width+'.png')});}
   }
   report.documents.push({name,width,status:'passed'});
  }
 }
}finally{await browser.close();}
fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
