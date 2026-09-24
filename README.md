# 知识学习库

用于持续整理各类知识点，按专题积累原理讲解、具体例子、实践记录和可运行实验。

## 专题目录

新增系统化阅读入口：[工程知识学习路线](工程知识学习路线.md)。包含九篇工程与应用专题，按具体问题选读；目录及正文都放在工程根目录。

| 专题 | 内容 | 阅读入口 |
|---|---|---|
| 检索引擎 | 索引结构、文本打分、向量检索与混合检索 | [检索引擎基础](检索引擎基础.md) |
| 数据链路与消息系统 | Kafka 生产消费、幂等、全量增量衔接与高可用 | [Kafka 到检索引擎](Kafka到检索引擎_数据链路与高可用.md) |
| JVM | 类加载、依赖隔离、卸载、Metaspace 与排查 | [类加载与内存回收](JVM_类加载隔离与内存回收.md) |
| Java | HashMap、并发组合、ThreadLocal、线程池与 LRU | [集合与并发](Java_集合并发与缓存正确性.md) |
| Redis | 数据结构、热点、缓存一致性与消息确认 | [Redis 专题](Redis_数据结构热点与缓存一致性.md) |
| MySQL | 索引、排序、Buffer Pool 与 MVCC | [MySQL 专题](MySQL_索引排序与事务可见性.md) |
| 运行与治理 | 容器隔离、Proxy、灰度、排空、容量与排障 | [容器与服务治理](容器与服务治理_隔离发布和故障定位.md) |
| 分布式任务 | 分片、恢复、幂等产物、租约与发布 | [任务构建与恢复](分布式任务_分片构建恢复与发布.md) |
| 搜推效果 | 特征时间、一致性、召回排序指标与 A/B | [特征与评估](搜推系统_特征时间与效果评估.md) |
| 智能应用 | Agent 工具执行、恢复、RAG 证据与评估 | [Agent 与 RAG](Agent与RAG_执行恢复知识检索和评估.md) |
| 算法与实现 | 最大子数组、LRU 与可检查的不变量 | [算法状态推导](算法_从状态推导LRU与最大子数组.md) |

新增图解：[正排与倒排究竟存了什么](索引结构图解_正排与倒排.md)。先沿八张结构图走一遍文档编号、词典定位和游标查找，再回到基础正文阅读其他主题。

底层进阶：[FST、词典压缩与倒排整数编码](索引结构进阶_FST与整数压缩.md)。用五张图继续拆解状态合并、路径输出、VInt、位打包和异常值编码，并区分不同 Lucene 版本的实现。

数据怎样进来：[Kafka 到检索引擎：数据链路与高可用](Kafka到检索引擎_数据链路与高可用.md)。用一次商品改价和七张图，逐步推演 Outbox、分区消费、崩溃重放、版本幂等、并发提交、全量追赶与副本故障；配套七组故障逻辑实验。

新增专题时，在这里添加入口；各专题独立成文，配套代码放在 `examples/` 中。

## 检索引擎专题

从四条文档出发，逐步理解一条文档怎样被索引、一个查询怎样返回结果。

建议顺序：**正排与倒排图解 → FST 与整数压缩 → 基础正文的其他主题**。每篇都可以配合实验核对结果。

| 内容 | 对应章节 |
|---|---|
| 文档与查询的基本关系 | 第 1 章 |
| 正排、倒排与 BitSet | 第 2—3 章 |
| Segment、更新、删除与可见性 | 第 4 章 |
| TF-IDF 与 BM25 手算 | 第 5 章 |
| 过滤与候选不足 | 第 6 章 |
| 向量距离、HNSW、IVF 与 PQ | 第 7 章 |
| 混合检索、RRF 与效果评估 | 第 8 章 |
| 完整查询链路与数据交付 | 第 9—10 章 |
| 理解检查与动手练习 | 第 11 章 |

建议按章节顺序阅读。正文用同一组数据贯穿倒排、过滤、BM25 和向量检索，相关章节附有官方文档或原始论文链接。

### 运行实验

环境：Python 3.9 或更新版本，无第三方依赖，不调用网络服务。

在工程根目录运行：

```bash
python3 examples/search_index_demo.py
```

检查默认数据的数值与集合结果：

```bash
python3 examples/search_index_demo.py --check
```

运行图解中的词典、倒排数据流与游标示例：

```bash
python3 examples/inverted_structure_demo.py
```

核对 FST 输出与整数编码的具体字节：

```bash
python3 examples/fst_compression_demo.py
```

复现 Kafka 到引擎链路中的提前提交、重复投递、乱序与查询可见性：

```bash
python3 examples/kafka_ingestion_demo.py
```

这是不联网的状态机模拟，无需安装 Kafka；不代替真实集群的持久化与故障演练。

程序演示：

- 从文档生成倒排列表，并计算 AND / OR 匹配结果。
- 用位运算组合租户与版本过滤条件。
- 计算教材形式的 BM25 与精确余弦相似度。
- 比较先取 Top-K 再过滤与在允许集合内检索的结果。
- 计算 RRF，观察候选窗口与重复命中带来的影响。

修改示例数据后，直接运行第一条命令观察变化；`--check` 的断言针对原始四条文档，不适用于任意修改后的数据。

## 目录

九篇新增专题的完整文件入口见上方表格与学习路线。以下列出原有检索专题及配套资源布局：

```text
knowledge_study/
├── README.md
├── 工程知识学习路线.md
├── 检索引擎基础.md
├── 索引结构图解_正排与倒排.md
├── 索引结构进阶_FST与整数压缩.md
├── Kafka到检索引擎_数据链路与高可用.md
├── assets/index-structures/       # SVG 源图与 PNG 插图
├── assets/kafka-ingestion/        # 数据链路的七张 SVG / PNG 图
├── assets/engineering-foundations/ # 工程专题的八张 SVG / PNG 图
├── scripts/
│   ├── build_index_figures.mjs   # 重建 SVG 的无依赖脚本
│   ├── build_kafka_figures.mjs   # 重建 Kafka 链路 SVG
│   ├── build_foundation_figures.mjs # 重建工程专题 SVG
│   └── render_index_figures.mjs  # PNG 导出与排版检查
└── examples/
    ├── search_index_demo.py
    ├── inverted_structure_demo.py
    ├── fst_compression_demo.py
    ├── kafka_ingestion_demo.py
    └── foundation_algorithms.py  # LRU、Kadane、拆桶与评估数值
```

## 示例边界

示例中的数据和向量是人为设定的教学数据。程序不实现 Lucene Segment、ANN 图索引、分布式调度或完整访问控制，也不是性能基准。

理解基础运算之后，可以在真实引擎中复现查询，再逐步增加数据量、并发、更新和过滤条件，观察效果与资源开销的变化。
