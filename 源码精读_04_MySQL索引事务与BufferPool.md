# 源码精读：MySQL 索引、排序、MVCC 与 Buffer Pool

本篇解决：一个查询怎样选访问路径、何时排序、读取哪个行版本，以及读入的数据页为什么没有简单地按精确 LRU 淘汰。源码锁定 MySQL 8.0.36，commit 49ef33f7edadef3ae04665e73d1babd40179a4f1；计划与性能仍受数据、配置和统计影响。

## 1. 先还原两种任务查询

查询 A：指定 cluster_id 与 status，按 priority DESC、created_at ASC、id ASC 取前 100 个。查询 B：指定失败状态，查最近一小时创建的任务。

A 可以评估 `(cluster_id,status,priority DESC,created_at ASC,id ASC)`，B 可以评估 `(status,created_at)`。这里只是候选，需要看字段类型、选择性、写放大和实际执行计划。不能按“created_at 区分度高，所以任何查询都放第一列”选索引。

![查询计划、索引记录与可见性判断之间的关系](assets/source-level/mysql.svg)

## 2. B+Tree 读到哪个层次才算理解

从[btr0cur.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/storage/innobase/btr/btr0cur.cc)的 btr_cur_search_to_nth_level 进入页级搜索，结合游标、页锁存与搜索模式理解如何定位叶子记录。

聚簇索引叶子包含行记录，二级索引记录携带索引列和用于定位聚簇记录的主键信息。内部页组织分隔键与子页引用。字段长度、页大小、记录头与页填充影响扇出，不用“永远三层”代替测量。

覆盖索引能减少部分聚簇访问，但一致性读取或记录状态等具体路径仍要看引擎实现；不能仅看 SELECT 列都在索引里，就对所有事务场景承诺零聚簇访问。

## 3. 优化器与执行器分开读

[sql_optimizer.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/sql/sql_optimizer.cc)中的 test_if_skip_sort_order 检查访问路径能否满足排序；[range_optimizer.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/sql/range_optimizer/range_optimizer.cc)的 test_quick_select 研究范围路径与代价。优化器选择不等于引擎已经读取了全部目标记录。

对于 A，等值限定前两列后，后续顺序可用于 ORDER BY；若缺少 status 条件，多个 status 分组各自有序，不自动构成全局 priority 顺序。若先对某列做范围，后续列是否还能服务排序与过滤要看具体模式，而非一句“范围之后索引全部失效”。

索引条件下推可以在二级索引扫描阶段判断部分条件，减少回表；它与用于定位扫描范围、用于满足排序是不同能力。执行计划里 key_len、rows、filtered 与 Extra 也分别表达不同信息。

## 4. filesort：内存排序、优先队列与归并

沿[filesort.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/sql/filesort.cc)的 filesort → check_if_pq_applicable → 输入读取与排序/归并路径。filesort 表示额外排序机制，不意味着必然写磁盘文件。

check_if_pq_applicable 会检查 LIMIT、记录长度、内存与行数估计等条件。LIMIT 100 可能维护有界优先队列，避免保留所有排序记录；没有 LIMIT 或收益不足时可选择其他排序路径。超过内存时可能产生有序段再归并。

排序记录可能包含 rowid，也可能包含附加字段。前者节省排序记录空间却增加后续取行，后者增宽排序记录、可能减少再次取行。需要按字段、长度和代价判断，不能从某一次 sort_mode 推导所有查询。

### 完整推导：为什么 LIMIT 不一定让扫描也只读 100 行

若没有满足排序的访问路径，需要从很多候选中决定前 100。优先队列可以限制保留的数据量，但仍可能检查大量候选。满足过滤且有序的索引扫描则可能较早停止，收益机制不同。

用 EXPLAIN/optimizer trace 研究路径，实验环境下再用 EXPLAIN ANALYZE 观察实际行数和时间；后者会执行查询。不能只比优化器估计就宣布线上性能改善。

## 5. MVCC：ReadView 的真实判断顺序

源码入口是[read0types.h](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/storage/innobase/include/read0types.h)的 ReadView::changes_visible，名字容易反直觉：m_up_limit_id 是快照中较早的活动边界，m_low_limit_id 是未来事务边界。

逻辑是：比 up_limit 更早，或属于创建者自己的修改，可见；达到 low_limit 或更晚，不可见；两者中间再查活动事务 ID 集合，不在集合中才可见。

用 up=40、low=60、活动集合 {40,50}、创建者 55 推演：30 可见，40 不可见，45 可见，50 不可见，55 可见，60 不可见。不是“事务 ID 小于当前事务 ID 就都可见”。

[row0sel.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/storage/innobase/row/row0sel.cc)的 row_search_mvcc 与[row0vers.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/storage/innobase/row/row0vers.cc)的 row_vers_build_for_consistent_read 衔接记录读取、可见性和历史版本重建。ReadView 判当前版本不可见后，还要沿适用的版本信息寻找符合快照的记录。

## 6. RR、RC、当前读与锁

[read0read.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/storage/innobase/read/read0read.cc)的 view_open 管理视图；具体隔离语义还取决于调用方何时创建、关闭与复用。RR 的一致性读通常复用事务快照，RC 在语句之间重新取得相应视图，不能把单一 changes_visible 方法当全部事务隔离实现。

UPDATE/锁定读与普通快照读不同。[lock0lock.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/storage/innobase/lock/lock0lock.cc)处理记录、间隙等锁状态；锁范围受索引、条件和隔离级别影响。MVCC 不意味着更新无锁，行锁也不保证所有查询只锁恰好一条逻辑行。

预算扣减应把条件检查和更新纳入正确事务协议。先普通 SELECT 看余额，再无条件 UPDATE，仍有并发窗口；分布式锁不能替代数据库中的约束与原子条件更新。

## 7. Buffer Pool：LRU 的结构与晋升条件

[buf0lru.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/storage/innobase/buf/buf0lru.cc)维护 old/new 相关链表位置；[buf0buf.ic](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/storage/innobase/include/buf0buf.ic)的 buf_page_peek_if_too_old 结合 old 标记、访问时间阈值与 freed_page_clock 等条件判断是否应变年轻。

目的之一是减少扫描把大量只读一次的页迅速提升到最热位置。大范围顺序读时，新读页进入相应位置，只有满足使用与时间条件才晋升；不是每访问一次就无条件移到全局头。

还要区分 LRU 链、flush list、free list。脏页、正在 I/O 的页与其他不可立即释放状态影响淘汰，不能抽象成“链尾删除即可”。命中率高也可能伴随锁等待或写盘瓶颈。

## 8. 提交与持久性边界

[trx0trx.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/storage/innobase/trx/trx0trx.cc)的 trx_commit_for_mysql 与[binlog.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/sql/binlog.cc)的 ordered_commit 展示引擎提交与服务层日志的协调入口。redo、undo、binlog 分别承担恢复、历史/回滚与复制等不同职责，刷盘与组提交的具体条件还受配置影响。

本篇不把源码路径推导成任意配置下的零丢失承诺。客户端提交超时仍需核对业务结果；主从切换后的可见性还取决于复制与故障协议。

## 9. 验证范围

本组核验了固定源码、方法与分支，并以本地 Python 模型复现 ReadView 条件。没有在本机启动 MySQL 或执行真实 SQL 计划，不能称已经验证优化器必选某索引、实际锁范围或崩溃恢复。

在数据库实验中应构造相同 DDL/数据、事务交错与统计条件，再检查计划、锁等待和结果。源码解释、模型测试与数据库集成验证分别记录。

## 自测

filesort 一定落盘吗？LIMIT 一定只扫描 N 行吗？MVCC 等于没有锁吗？Buffer Pool 是精确普通 LRU 吗？都不是。分别从排序分支、访问路径、读取语义和页状态说明原因。
