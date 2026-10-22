# 类卸载与Metaspace回收

版本已经摘流，为什么旧加载器和元数据仍可能留在进程里？

源码基线：openjdk/jdk17u · jdk-17.0.14+7。[固定源文件](https://github.com/openjdk/jdk17u/blob/c5c90ffa45d0c14bcb013164f0992938eb4740ab/src/hotspot/share/classfile/classLoaderDataGraph.cpp)；方法名是导航，下面逐步解释条件与状态。

![类卸载与Metaspace回收的关键状态](assets/deep-points/03.svg)

## 先区分三种“释放”

移除路由引用是应用动作；类卸载是 GC/VM 生命周期动作；把已提交的元数据内存归还操作系统是分配器动作。三个动作不同时发生，统计口径也不同。URLClassLoader.close 关闭其打开资源，并不会把已定义类变成失效类型。

对普通可卸载版本类，重点看定义加载器相关的存活关系。一个业务对象不只是占一块堆，它的类身份还关联版本的元数据与加载器生命周期。

## 源码上看哪条链

ClassLoaderDataGraph::do_unloading 遍历 CLD，按存活性把不再存活的数据移到卸载处理；不是收到一个平台“删除版本”事件就逐类 free。MetaspaceArena 的分配与 arena 生命周期说明元数据以分配单元组织，而非每个 Class 都对应一次独立 malloc/free。

因此，堆中一个 Class 镜像、类的元数据与 OS 页不应画成一一立即释放关系。还要分清 boot、长期存活公共加载器和可退役版本加载器。

## 完整推导：一条线程池引用怎样留住旧版本

```text
宿主长期线程
  -> threadLocals
  -> Entry.value：旧版 RequestContext
  -> 旧版类身份 / 定义加载器 L1
```

路由表已删除 L1，也没有业务新请求，但 value 未 remove。只要宿主线程与这条引用链存活，关 jar 文件就不解决问题。若 Entry 的弱 key 先被收集，value 也未必立刻释放；需要相关清理路径或线程终结等条件。

另一个常见路径是宿主线程的 contextClassLoader=L1。还有父层静态 Map 缓存旧 Class、注册的回调、监控任务、执行中的异步任务。不能只搜索一个叫 classLoader 的字段：任务闭包也可能间接捕获版本对象。

## 退役协议要能解释“谁还在用”

```text
ACTIVE -> DRAINING -> QUIESCENT -> CLOSED -> 可回收候选
```

DRAINING 停新流量；QUIESCENT 确认在途任务结束；CLOSED 取消定时器、注销监听、关闭客户端、清理线程上下文并移除宿主引用。仅排空 HTTP 请求不代表后台定时任务也停止。

若业务不遵守资源生命周期契约，宿主很难安全地猜测哪些线程可以停。不能用强停线程作为通用卸载手段。独立进程将最后的生命周期边界交给 OS，但代价是启动、网络与基础内存。

## 怎样用指标证明趋势

| 观察 | 能说明什么 | 不能直接说明什么 |
|---|---|---|
| unloaded classes 增加 | 出现了类卸载 | 所有旧版本都已卸载 |
| Metaspace used 回落 | 使用中的元数据下降 | RSS 必须同步下降 |
| committed 不变 | VM 仍保留部分提交内存 | 必然还有旧对象引用 |
| RSS 上升 | 进程驻留内存增加 | 增长必定来自元数据 |

固定 N 个版本的发布/退役循环，在相同负载和适当回收观察点比较“退役后的基线”是否持续抬升。对旧加载器找 GC Roots 引用路径，比只看一次总 RSS 更接近因果证据。NMT、jcmd 与 GC 类卸载日志需匹配运行版本和启动配置；不要承诺一次 System.gc 就让测试必过。

## 自测

close 成功但旧加载器仍存活，下一步不是重复 close，而是找谁保留它。若 used 已下降但 RSS 未降，继续分解分配器、提交粒度和其他 native 内存，不应直接判定类泄漏修复失败。

[查看可编辑 SVG](assets/deep-points/03.svg) · [查看 PNG](assets/deep-points/03.png) · [返回知识点目录](实现详解_00_知识点目录.md)

