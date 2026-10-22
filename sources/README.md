# 固定上游源码索引

由 fetch_source_audit.py 从公开仓库生成。commit 为 tag 解析结果，文件哈希校验下载内容。
符号行号为子串命中位置，用于定位，不保证每个命中都是方法定义。

## jdk · jdk-17.0.14+7

commit: `c5c90ffa45d0c14bcb013164f0992938eb4740ab`

| 文件 | 入口符号 | 校验 |
|---|---|---|
| [src/java.base/share/classes/java/lang/ClassLoader.java](https://github.com/openjdk/jdk17u/blob/c5c90ffa45d0c14bcb013164f0992938eb4740ab/src/java.base/share/classes/java/lang/ClassLoader.java) | loadClass: 124, 125, 171, 179, 184, 195, 199, 511; defineClass: 164, 165, 186, 196, 799, 800, 803, 806 | ok |
| [src/java.base/share/classes/java/net/URLClassLoader.java](https://github.com/openjdk/jdk17u/blob/c5c90ffa45d0c14bcb013164f0992938eb4740ab/src/java.base/share/classes/java/net/URLClassLoader.java) | close: 253, 255, 259, 268, 272, 273, 299, 300 | ok |
| [src/hotspot/share/oops/instanceKlass.cpp](https://github.com/openjdk/jdk17u/blob/c5c90ffa45d0c14bcb013164f0992938eb4740ab/src/hotspot/share/oops/instanceKlass.cpp) | initialize_impl: 727, 766, 804, 1077 | ok |
| [src/hotspot/share/classfile/classLoaderDataGraph.cpp](https://github.com/openjdk/jdk17u/blob/c5c90ffa45d0c14bcb013164f0992938eb4740ab/src/hotspot/share/classfile/classLoaderDataGraph.cpp) | do_unloading: 499, 534 | ok |
| [src/hotspot/share/memory/metaspace/metaspaceArena.cpp](https://github.com/openjdk/jdk17u/blob/c5c90ffa45d0c14bcb013164f0992938eb4740ab/src/hotspot/share/memory/metaspace/metaspaceArena.cpp) | allocate: 72, 87, 220, 221, 223, 225, 232, 238 | ok |
| [src/java.base/share/classes/java/util/HashMap.java](https://github.com/openjdk/jdk17u/blob/c5c90ffa45d0c14bcb013164f0992938eb4740ab/src/java.base/share/classes/java/util/HashMap.java) | resize: 264, 271, 385, 413, 505, 508, 627, 661; treeifyBin: 642, 753, 1234, 1332, 1403, 1914; find(int h: 2009 | ok |
| [src/java.base/share/classes/java/util/concurrent/ConcurrentHashMap.java](https://github.com/openjdk/jdk17u/blob/c5c90ffa45d0c14bcb013164f0992938eb4740ab/src/java.base/share/classes/java/util/concurrent/ConcurrentHashMap.java) | putVal: 1006, 1010, 1089, 1445, 1541, 4652, 4672, 4823; transfer: 377, 379, 390, 396, 400, 563, 805, 2229; computeIfAbsent: 137, 139, 285, 1691, 2266 | ok |
| [src/java.base/share/classes/java/util/LinkedHashMap.java](https://github.com/openjdk/jdk17u/blob/c5c90ffa45d0c14bcb013164f0992938eb4740ab/src/java.base/share/classes/java/util/LinkedHashMap.java) | afterNodeAccess: 306, 444, 456; afterNodeInsertion: 298 | ok |
| [src/java.base/share/classes/java/lang/ThreadLocal.java](https://github.com/openjdk/jdk17u/blob/c5c90ffa45d0c14bcb013164f0992938eb4740ab/src/java.base/share/classes/java/lang/ThreadLocal.java) | expungeStaleEntry: 459, 516, 562, 573, 590, 604, 674, 732; getEntry: 165, 185, 426, 433, 439, 443, 451 | ok |
| [src/java.base/share/classes/java/util/concurrent/ThreadPoolExecutor.java](https://github.com/openjdk/jdk17u/blob/c5c90ffa45d0c14bcb013164f0992938eb4740ab/src/java.base/share/classes/java/util/concurrent/ThreadPoolExecutor.java) | execute: 49, 83, 114, 205, 208, 220, 225, 519; runWorker: 599, 628, 633, 635, 1115; processWorkerExit: 434, 989, 1082, 1150 | ok |
| [src/java.base/share/classes/java/util/concurrent/locks/AbstractQueuedSynchronizer.java](https://github.com/openjdk/jdk17u/blob/c5c90ffa45d0c14bcb013164f0992938eb4740ab/src/java.base/share/classes/java/util/concurrent/locks/AbstractQueuedSynchronizer.java) | acquire: 53, 66, 71, 72, 73, 75, 77, 89; release: 32, 54, 87, 88, 185, 216, 217, 253 | ok |
| [src/java.base/share/classes/java/util/concurrent/locks/ReentrantLock.java](https://github.com/openjdk/jdk17u/blob/c5c90ffa45d0c14bcb013164f0992938eb4740ab/src/java.base/share/classes/java/util/concurrent/locks/ReentrantLock.java) | tryAcquire: 168, 241, 279; tryRelease: 172 | ok |
| [src/hotspot/share/classfile/classFileParser.cpp](https://github.com/openjdk/jdk17u/blob/c5c90ffa45d0c14bcb013164f0992938eb4740ab/src/hotspot/share/classfile/classFileParser.cpp) | ClassFileParser::ClassFileParser: 5503; parse_stream: 5598, 5689 | ok |
| [src/hotspot/share/interpreter/linkResolver.cpp](https://github.com/openjdk/jdk17u/blob/c5c90ffa45d0c14bcb013164f0992938eb4740ab/src/hotspot/share/interpreter/linkResolver.cpp) | resolve_method: 595, 610, 628, 630, 708, 1084, 1124, 1297; resolve_field: 938, 940, 943 | ok |
| [src/hotspot/share/classfile/verifier.cpp](https://github.com/openjdk/jdk17u/blob/c5c90ffa45d0c14bcb013164f0992938eb4740ab/src/hotspot/share/classfile/verifier.cpp) | Verifier::verify: 156, 178, 629, 707, 1867, 1919, 1943, 1983 | ok |

## redis · 7.2.4

commit: `d2c8a4b91e8c0e6aefd1f5bc0bf582cddbe046b7`

| 文件 | 入口符号 | 校验 |
|---|---|---|
| [src/t_list.c](https://github.com/redis/redis/blob/d2c8a4b91e8c0e6aefd1f5bc0bf582cddbe046b7/src/t_list.c) | listType: 42, 87, 132, 138, 141, 147, 149, 150 | ok |
| [src/quicklist.c](https://github.com/redis/redis/blob/d2c8a4b91e8c0e6aefd1f5bc0bf582cddbe046b7/src/quicklist.c) | quicklistPush: 552, 580, 1486, 1600, 1609, 1611, 1990, 1998 | ok |
| [src/listpack.c](https://github.com/redis/redis/blob/d2c8a4b91e8c0e6aefd1f5bc0bf582cddbe046b7/src/listpack.c) | lpInsert: 780, 929, 930, 933, 936, 938, 943, 950 | ok |
| [src/t_zset.c](https://github.com/redis/redis/blob/d2c8a4b91e8c0e6aefd1f5bc0bf582cddbe046b7/src/t_zset.c) | zslInsert: 135, 157, 298, 300, 1245, 1479, 1656, 2432 | ok |
| [src/dict.c](https://github.com/redis/redis/blob/d2c8a4b91e8c0e6aefd1f5bc0bf582cddbe046b7/src/dict.c) | dictRehash: 295, 392, 393, 399, 414, 415, 564, 674 | ok |
| [src/evict.c](https://github.com/redis/redis/blob/d2c8a4b91e8c0e6aefd1f5bc0bf582cddbe046b7/src/evict.c) | performEvictions: 44, 137, 461, 538 | ok |
| [src/cluster.c](https://github.com/redis/redis/blob/d2c8a4b91e8c0e6aefd1f5bc0bf582cddbe046b7/src/cluster.c) | keyHashSlot: 1352, 6231, 7297, 7522, 7563, 7580, 7612, 7677 | ok |
| [src/lazyfree.c](https://github.com/redis/redis/blob/d2c8a4b91e8c0e6aefd1f5bc0bf582cddbe046b7/src/lazyfree.c) | lazyfreeGetFreeEffort: 104, 160 | ok |
| [src/db.c](https://github.com/redis/redis/blob/d2c8a4b91e8c0e6aefd1f5bc0bf582cddbe046b7/src/db.c) | expireIfNeeded: 44, 48, 107, 340, 347, 722, 1141, 1775 | ok |
| [src/networking.c](https://github.com/redis/redis/blob/d2c8a4b91e8c0e6aefd1f5bc0bf582cddbe046b7/src/networking.c) | processInputBuffer: 2250, 2510, 2520, 2713 | ok |
| [src/aof.c](https://github.com/redis/redis/blob/d2c8a4b91e8c0e6aefd1f5bc0bf582cddbe046b7/src/aof.c) | rewriteAppendOnlyFileBackground: 777, 995, 2351, 2425, 2504 | ok |
| [src/replication.c](https://github.com/redis/redis/blob/d2c8a4b91e8c0e6aefd1f5bc0bf582cddbe046b7/src/replication.c) | masterTryPartialResynchronization: 740, 1015 | ok |

## mysql · mysql-8.0.36

commit: `49ef33f7edadef3ae04665e73d1babd40179a4f1`

| 文件 | 入口符号 | 校验 |
|---|---|---|
| [sql/sql_optimizer.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/sql/sql_optimizer.cc) | test_if_skip_sort_order: 150, 1546, 1567, 1682, 1710, 2092, 2186, 3027 | ok |
| [sql/filesort.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/sql/filesort.cc) | check_if_pq_applicable: 157, 446, 1645 | ok |
| [sql/range_optimizer/range_optimizer.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/sql/range_optimizer/range_optimizer.cc) | test_quick_select: 43, 189, 306, 435, 523 | ok |
| [storage/innobase/row/row0sel.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/storage/innobase/row/row0sel.cc) | row_search_mvcc: 4246, 4264, 4399, 4952, 6119, 6162 | ok |
| [storage/innobase/include/read0types.h](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/storage/innobase/include/read0types.h) | changes_visible: 162 | ok |
| [storage/innobase/row/row0vers.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/storage/innobase/row/row0vers.cc) | row_vers_build_for_consistent_read: 1249 | ok |
| [storage/innobase/buf/buf0lru.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/storage/innobase/buf/buf0lru.cc) | buf_LRU_make_block_young: 1732 | ok |
| [storage/innobase/lock/lock0lock.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/storage/innobase/lock/lock0lock.cc) | lock_rec: 186, 333, 334, 350, 368, 374, 431, 440 | ok |
| [storage/innobase/btr/btr0cur.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/storage/innobase/btr/btr0cur.cc) | btr_cur_search_to_nth_level: 125, 128, 618, 1714, 2392, 5060, 5096 | ok |
| [storage/innobase/read/read0read.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/storage/innobase/read/read0read.cc) | view_open: 528 | ok |
| [storage/innobase/include/buf0buf.ic](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/storage/innobase/include/buf0buf.ic) | buf_page_peek_if_too_old: 179 | ok |
| [sql/binlog.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/sql/binlog.cc) | ordered_commit: 1821, 1826, 1878, 2606, 2609, 2610, 2616, 2812 | ok |
| [storage/innobase/trx/trx0trx.cc](https://github.com/mysql/mysql-server/blob/49ef33f7edadef3ae04665e73d1babd40179a4f1/storage/innobase/trx/trx0trx.cc) | trx_commit_for_mysql: 2434, 2436, 2487 | ok |

## linux · v6.6

commit: `ffc253263a1375a65fa6c9f62a893e9767fbebfa`

| 文件 | 入口符号 | 校验 |
|---|---|---|
| [kernel/nsproxy.c](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/kernel/nsproxy.c) | copy_namespaces: 151 | ok |
| [kernel/cgroup/cgroup.c](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/kernel/cgroup/cgroup.c) | cgroup_attach_task: 1474, 1491, 2828, 2835, 5167 | ok |
| [kernel/sched/fair.c](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/kernel/sched/fair.c) | throttle_cfs_rq: 5560, 5649, 5746, 5766, 5775, 5781, 5795, 5797 | ok |
| [fs/eventpoll.c](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/fs/eventpoll.c) | ep_poll: 487, 489, 499, 512, 514, 538, 554, 599 | ok |
| [Documentation/admin-guide/cgroup-v2.rst](https://github.com/torvalds/linux/blob/ffc253263a1375a65fa6c9f62a893e9767fbebfa/Documentation/admin-guide/cgroup-v2.rst) | cpu.max: 1074, 1086 | ok |

## k8s · v1.29.0

commit: `3f7a50f38688eb332e2a1b013678c6435d539ae6`

| 文件 | 入口符号 | 校验 |
|---|---|---|
| [pkg/controller/deployment/sync.go](https://github.com/kubernetes/kubernetes/blob/3f7a50f38688eb332e2a1b013678c6435d539ae6/pkg/controller/deployment/sync.go) | syncDeploymentStatus: 44, 68, 475, 476 | ok |
| [pkg/controller/endpointslice/endpointslice_controller.go](https://github.com/kubernetes/kubernetes/blob/3f7a50f38688eb332e2a1b013678c6435d539ae6/pkg/controller/endpointslice/endpointslice_controller.go) | syncService: 64, 70, 72, 295, 320 | ok |
| [pkg/controller/podautoscaler/horizontal.go](https://github.com/kubernetes/kubernetes/blob/3f7a50f38688eb332e2a1b013678c6435d539ae6/pkg/controller/podautoscaler/horizontal.go) | reconcileAutoscaler: 64, 532, 740, 847 | ok |
| [pkg/controller/podautoscaler/replica_calculator.go](https://github.com/kubernetes/kubernetes/blob/3f7a50f38688eb332e2a1b013678c6435d539ae6/pkg/controller/podautoscaler/replica_calculator.go) | GetResourceReplicas: 63, 65 | ok |

## netty · netty-4.1.108.Final

commit: `3a3f9d13b129555802de5652667ca0af662f554e`

| 文件 | 入口符号 | 校验 |
|---|---|---|
| [transport/src/main/java/io/netty/channel/nio/NioEventLoop.java](https://github.com/netty/netty/blob/3a3f9d13b129555802de5652667ca0af662f554e/transport/src/main/java/io/netty/channel/nio/NioEventLoop.java) | processSelectedKeys: 553, 562, 648, 650, 652, 674, 714 | ok |
| [transport/src/main/java/io/netty/channel/ChannelOutboundBuffer.java](https://github.com/netty/netty/blob/3a3f9d13b129555802de5652667ca0af662f554e/transport/src/main/java/io/netty/channel/ChannelOutboundBuffer.java) | setUnwritable: 188, 632 | ok |
| [common/src/main/java/io/netty/util/concurrent/SingleThreadEventExecutor.java](https://github.com/netty/netty/blob/3a3f9d13b129555802de5652667ca0af662f554e/common/src/main/java/io/netty/util/concurrent/SingleThreadEventExecutor.java) | execute: 48, 185, 265, 298, 300, 402, 416, 418 | ok |
| [common/src/main/java/io/netty/util/concurrent/DefaultPromise.java](https://github.com/netty/netty/blob/3a3f9d13b129555802de5652667ca0af662f554e/common/src/main/java/io/netty/util/concurrent/DefaultPromise.java) | notifyListeners: 185, 205, 386, 484, 492, 503, 509, 538 | ok |

## dubbo · 3.2.12

commit: `1dd6a4aaa8816cf3f1585769dfff4f325e4ecd15`

| 文件 | 入口符号 | 校验 |
|---|---|---|
| [dubbo-cluster/src/main/java/org/apache/dubbo/rpc/cluster/support/AbstractClusterInvoker.java](https://github.com/apache/dubbo/blob/1dd6a4aaa8816cf3f1585769dfff4f325e4ecd15/dubbo-cluster/src/main/java/org/apache/dubbo/rpc/cluster/support/AbstractClusterInvoker.java) | select: 71, 94, 141, 142, 144, 145, 151, 155 | ok |
| [dubbo-cluster/src/main/java/org/apache/dubbo/rpc/cluster/support/FailoverClusterInvoker.java](https://github.com/apache/dubbo/blob/1dd6a4aaa8816cf3f1585769dfff4f325e4ecd15/dubbo-cluster/src/main/java/org/apache/dubbo/rpc/cluster/support/FailoverClusterInvoker.java) | doInvoke: 59 | ok |
| [dubbo-registry/dubbo-registry-api/src/main/java/org/apache/dubbo/registry/integration/RegistryDirectory.java](https://github.com/apache/dubbo/blob/1dd6a4aaa8816cf3f1585769dfff4f325e4ecd15/dubbo-registry/dubbo-registry-api/src/main/java/org/apache/dubbo/registry/integration/RegistryDirectory.java) | refreshInvoker: 254, 269 | ok |
| [dubbo-cluster/src/main/java/org/apache/dubbo/rpc/cluster/RouterChain.java](https://github.com/apache/dubbo/blob/1dd6a4aaa8816cf3f1585769dfff4f325e4ecd15/dubbo-cluster/src/main/java/org/apache/dubbo/rpc/cluster/RouterChain.java) | route: 26, 27, 28, 29, 64, 77, 80, 117 | ok |

## kafka · 3.7.0

commit: `2ae524ed625438c5fee89e78648bd73e64a3ada0`

| 文件 | 入口符号 | 校验 |
|---|---|---|
| [clients/src/main/java/org/apache/kafka/clients/consumer/KafkaConsumer.java](https://github.com/apache/kafka/blob/2ae524ed625438c5fee89e78648bd73e64a3ada0/clients/src/main/java/org/apache/kafka/clients/consumer/KafkaConsumer.java) | assign: 96, 99, 100, 105, 117, 121, 122, 123 | ok |
| [clients/src/main/java/org/apache/kafka/clients/consumer/internals/ConsumerCoordinator.java](https://github.com/apache/kafka/blob/2ae524ed625438c5fee89e78648bd73e64a3ada0/clients/src/main/java/org/apache/kafka/clients/consumer/internals/ConsumerCoordinator.java) | commitOffsetsSync: 1096, 1139 | ok |
| [clients/src/main/java/org/apache/kafka/clients/consumer/internals/SubscriptionState.java](https://github.com/apache/kafka/blob/2ae524ed625438c5fee89e78648bd73e64a3ada0/clients/src/main/java/org/apache/kafka/clients/consumer/internals/SubscriptionState.java) | assignFromUser: 56, 219, 270 | ok |
| [clients/src/main/java/org/apache/kafka/clients/consumer/internals/Fetcher.java](https://github.com/apache/kafka/blob/2ae524ed625438c5fee89e78648bd73e64a3ada0/clients/src/main/java/org/apache/kafka/clients/consumer/internals/Fetcher.java) | collectFetch: 144, 145 | ok |
| [clients/src/main/java/org/apache/kafka/clients/producer/internals/Sender.java](https://github.com/apache/kafka/blob/2ae524ed625438c5fee89e78648bd73e64a3ada0/clients/src/main/java/org/apache/kafka/clients/producer/internals/Sender.java) | runOnce: 252, 265, 285, 314 | ok |
| [core/src/main/scala/kafka/cluster/Partition.scala](https://github.com/apache/kafka/blob/2ae524ed625438c5fee89e78648bd73e64a3ada0/core/src/main/scala/kafka/cluster/Partition.scala) | appendRecordsToLeader: 1349 | ok |
| [core/src/main/scala/kafka/server/ReplicaFetcherThread.scala](https://github.com/apache/kafka/blob/2ae524ed625438c5fee89e78648bd73e64a3ada0/core/src/main/scala/kafka/server/ReplicaFetcherThread.scala) | processPartitionData: 103 | ok |
| [storage/src/main/java/org/apache/kafka/storage/internals/log/ProducerStateManager.java](https://github.com/apache/kafka/blob/2ae524ed625438c5fee89e78648bd73e64a3ada0/storage/src/main/java/org/apache/kafka/storage/internals/log/ProducerStateManager.java) | prepareUpdate: 415 | ok |
| [clients/src/main/java/org/apache/kafka/clients/consumer/internals/LegacyKafkaConsumer.java](https://github.com/apache/kafka/blob/2ae524ed625438c5fee89e78648bd73e64a3ada0/clients/src/main/java/org/apache/kafka/clients/consumer/internals/LegacyKafkaConsumer.java) | assign: 135, 201, 215, 277, 288, 330, 397, 400; poll: 144, 509, 584, 585, 589, 590, 596, 617 | ok |
| [core/src/main/scala/kafka/coordinator/group/GroupCoordinator.scala](https://github.com/apache/kafka/blob/2ae524ed625438c5fee89e78648bd73e64a3ada0/core/src/main/scala/kafka/coordinator/group/GroupCoordinator.scala) | handleJoinGroup: 159 | ok |
| [core/src/main/scala/kafka/coordinator/group/GroupMetadataManager.scala](https://github.com/apache/kafka/blob/2ae524ed625438c5fee89e78648bd73e64a3ada0/core/src/main/scala/kafka/coordinator/group/GroupMetadataManager.scala) | partitionFor: 195, 197, 199, 252, 268, 385, 477, 804 | ok |

## zookeeper · release-3.9.2

commit: `e454e8c7283100c7caec6dcae2bc82aaecb63023`

| 文件 | 入口符号 | 校验 |
|---|---|---|
| [zookeeper-recipes/zookeeper-recipes-lock/src/main/java/org/apache/zookeeper/recipes/lock/WriteLock.java](https://github.com/apache/zookeeper/blob/e454e8c7283100c7caec6dcae2bc82aaecb63023/zookeeper-recipes/zookeeper-recipes-lock/src/main/java/org/apache/zookeeper/recipes/lock/WriteLock.java) | LockZooKeeperOperation: 57, 72, 174 | ok |
| [zookeeper-server/src/main/java/org/apache/zookeeper/server/PrepRequestProcessor.java](https://github.com/apache/zookeeper/blob/e454e8c7283100c7caec6dcae2bc82aaecb63023/zookeeper-server/src/main/java/org/apache/zookeeper/server/PrepRequestProcessor.java) | pRequest2Txn: 315, 326, 639, 775, 779, 783, 787, 791 | ok |

## lucene · releases/lucene/9.9.2

commit: `a2939784c4ca60bc28bf488b5479c02fc2e5e22c`

| 文件 | 入口符号 | 校验 |
|---|---|---|
| [lucene/core/src/java/org/apache/lucene/index/IndexWriter.java](https://github.com/apache/lucene/blob/a2939784c4ca60bc28bf488b5479c02fc2e5e22c/lucene/core/src/java/org/apache/lucene/index/IndexWriter.java) | updateDocument: 108, 1476, 1509, 1524, 1527, 1532, 1537, 1540; prepareCommit: 272, 1318, 1352, 2436, 3573, 3574, 3581, 3583 | ok |
| [lucene/core/src/java/org/apache/lucene/index/DocumentsWriterPerThread.java](https://github.com/apache/lucene/blob/a2939784c4ca60bc28bf488b5479c02fc2e5e22c/lucene/core/src/java/org/apache/lucene/index/DocumentsWriterPerThread.java) | flush: 91, 117, 121, 214, 261, 302, 310, 313 | ok |
| [lucene/core/src/java/org/apache/lucene/index/StandardDirectoryReader.java](https://github.com/apache/lucene/blob/a2939784c4ca60bc28bf488b5479c02fc2e5e22c/lucene/core/src/java/org/apache/lucene/index/StandardDirectoryReader.java) | open: 47, 64, 67, 70, 71, 113, 178, 209 | ok |
| [lucene/core/src/java/org/apache/lucene/index/SegmentInfos.java](https://github.com/apache/lucene/blob/a2939784c4ca60bc28bf488b5479c02fc2e5e22c/lucene/core/src/java/org/apache/lucene/index/SegmentInfos.java) | finishCommit: 552, 902, 937, 979 | ok |
| [lucene/core/src/java/org/apache/lucene/codecs/lucene90/blocktree/SegmentTermsEnum.java](https://github.com/apache/lucene/blob/a2939784c4ca60bc28bf488b5479c02fc2e5e22c/lucene/core/src/java/org/apache/lucene/codecs/lucene90/blocktree/SegmentTermsEnum.java) | seekExact: 331, 346, 1033, 1140, 1142, 1171 | ok |
| [lucene/core/src/java/org/apache/lucene/codecs/lucene99/Lucene99PostingsReader.java](https://github.com/apache/lucene/blob/a2939784c4ca60bc28bf488b5479c02fc2e5e22c/lucene/core/src/java/org/apache/lucene/codecs/lucene99/Lucene99PostingsReader.java) | advance: 371, 501, 539, 691, 869, 1118, 1169, 1186 | ok |
| [lucene/core/src/java/org/apache/lucene/codecs/lucene99/ForUtil.java](https://github.com/apache/lucene/blob/a2939784c4ca60bc28bf488b5479c02fc2e5e22c/lucene/core/src/java/org/apache/lucene/codecs/lucene99/ForUtil.java) | decode: 303, 409, 412, 416, 420, 424, 428, 432 | ok |
| [lucene/core/src/java/org/apache/lucene/util/fst/FST.java](https://github.com/apache/lucene/blob/a2939784c4ca60bc28bf488b5479c02fc2e5e22c/lucene/core/src/java/org/apache/lucene/util/fst/FST.java) | findTargetArc: 1049 | ok |
| [lucene/core/src/java/org/apache/lucene/search/similarities/BM25Similarity.java](https://github.com/apache/lucene/blob/a2939784c4ca60bc28bf488b5479c02fc2e5e22c/lucene/core/src/java/org/apache/lucene/search/similarities/BM25Similarity.java) | idf: 104, 150, 161, 164, 167, 169, 170, 178 | ok |
| [lucene/core/src/java/org/apache/lucene/util/hnsw/HnswGraphSearcher.java](https://github.com/apache/lucene/blob/a2939784c4ca60bc28bf488b5479c02fc2e5e22c/lucene/core/src/java/org/apache/lucene/util/hnsw/HnswGraphSearcher.java) | searchLevel: 36, 115, 131, 137, 194 | ok |
| [lucene/core/src/java/org/apache/lucene/search/ConjunctionDISI.java](https://github.com/apache/lucene/blob/a2939784c4ca60bc28bf488b5479c02fc2e5e22c/lucene/core/src/java/org/apache/lucene/search/ConjunctionDISI.java) | doNext: 165, 205, 217, 269, 276, 279 | ok |
| [lucene/core/src/java/org/apache/lucene/search/KnnFloatVectorQuery.java](https://github.com/apache/lucene/blob/a2939784c4ca60bc28bf488b5479c02fc2e5e22c/lucene/core/src/java/org/apache/lucene/search/KnnFloatVectorQuery.java) | approximateSearch: 79 | ok |
| [lucene/core/src/java/org/apache/lucene/codecs/lucene99/PForUtil.java](https://github.com/apache/lucene/blob/a2939784c4ca60bc28bf488b5479c02fc2e5e22c/lucene/core/src/java/org/apache/lucene/codecs/lucene99/PForUtil.java) | decode: 116, 123 | ok |
| [lucene/core/src/java/org/apache/lucene/search/AbstractKnnVectorQuery.java](https://github.com/apache/lucene/blob/a2939784c4ca60bc28bf488b5479c02fc2e5e22c/lucene/core/src/java/org/apache/lucene/search/AbstractKnnVectorQuery.java) | getLeafResults: 99, 108; exactSearch: 127, 136, 165 | ok |
| [lucene/core/src/java/org/apache/lucene/analysis/Analyzer.java](https://github.com/apache/lucene/blob/a2939784c4ca60bc28bf488b5479c02fc2e5e22c/lucene/core/src/java/org/apache/lucene/analysis/Analyzer.java) | tokenStream: 40, 95, 144, 151, 153, 181, 183, 289 | ok |
| [lucene/core/src/java/org/apache/lucene/search/similarities/TFIDFSimilarity.java](https://github.com/apache/lucene/blob/a2939784c4ca60bc28bf488b5479c02fc2e5e22c/lucene/core/src/java/org/apache/lucene/search/similarities/TFIDFSimilarity.java) | tf: 229, 253, 256, 259, 260, 267, 370, 426; idf: 53, 55, 56, 60, 230, 276, 279, 280 | ok |

## eino · v0.7.0

commit: `18427c201b3315586802260f8b20a97f6b008e8b`

| 文件 | 入口符号 | 校验 |
|---|---|---|
| [adk/runner.go](https://github.com/cloudwego/eino/blob/18427c201b3315586802260f8b20a97f6b008e8b/adk/runner.go) | Runner: 30, 32, 42, 59, 60, 69, 71, 98 | ok |
| [adk/chatmodel.go](https://github.com/cloudwego/eino/blob/18427c201b3315586802260f8b20a97f6b008e8b/adk/chatmodel.go) | ChatModelAgent: 72, 116, 117, 133, 136, 143, 182, 202 | ok |
| [compose/tool_node.go](https://github.com/cloudwego/eino/blob/18427c201b3315586802260f8b20a97f6b008e8b/compose/tool_node.go) | ToolsNode: 38, 39, 41, 42, 48, 49, 55, 58 | ok |
| [compose/checkpoint.go](https://github.com/cloudwego/eino/blob/18427c201b3315586802260f8b20a97f6b008e8b/compose/checkpoint.go) | CheckPointStore: 50, 57, 166, 181 | ok |
| [flow/agent/react/react.go](https://github.com/cloudwego/eino/blob/18427c201b3315586802260f8b20a97f6b008e8b/flow/agent/react/react.go) | MaxStep: 69, 71, 235, 291 | ok |
| [adk/react.go](https://github.com/cloudwego/eino/blob/18427c201b3315586802260f8b20a97f6b008e8b/adk/react.go) | maxIterations: 79, 122, 125; newReact: 116 | ok |
| [components/embedding/interface.go](https://github.com/cloudwego/eino/blob/18427c201b3315586802260f8b20a97f6b008e8b/components/embedding/interface.go) | Embedder: 22 | ok |

## leveldb · 1.23

commit: `99b3c03b3284f5886f9ef9a4ef703d57373e61be`

| 文件 | 入口符号 | 校验 |
|---|---|---|
| [db/db_impl.cc](https://github.com/google/leveldb/blob/99b3c03b3284f5886f9ef9a4ef703d57373e61be/db/db_impl.cc) | DBImpl::Write: 43, 505, 1200; DBImpl::Get: 1115, 1181, 1387, 1449 | ok |
| [db/version_set.cc](https://github.com/google/leveldb/blob/99b3c03b3284f5886f9ef9a4ef703d57373e61be/db/version_set.cc) | Version::Get: 324, 498; PickCompaction: 1253 | ok |

## resilience · v2.2.0

commit: `e77f3536ac9b6c4764b1b8ac3dae0bca540768e4`

| 文件 | 入口符号 | 校验 |
|---|---|---|
| [resilience4j-circuitbreaker/src/main/java/io/github/resilience4j/circuitbreaker/internal/CircuitBreakerStateMachine.java](https://github.com/resilience4j/resilience4j/blob/e77f3536ac9b6c4764b1b8ac3dae0bca540768e4/resilience4j-circuitbreaker/src/main/java/io/github/resilience4j/circuitbreaker/internal/CircuitBreakerStateMachine.java) | ClosedState: 84, 323, 359, 360, 585, 590, 1173; HalfOpenState: 382, 383, 716, 734, 811, 813, 1064, 1073 | ok |
| [resilience4j-ratelimiter/src/main/java/io/github/resilience4j/ratelimiter/internal/AtomicRateLimiter.java](https://github.com/resilience4j/resilience4j/blob/e77f3536ac9b6c4764b1b8ac3dae0bca540768e4/resilience4j-ratelimiter/src/main/java/io/github/resilience4j/ratelimiter/internal/AtomicRateLimiter.java) | reservePermission: 130, 238, 291; State: 43, 47, 54, 69, 83, 84, 85, 97 | ok |

## playwright · v1.51.1

commit: `0ad26b38902449d9347536c97a34cc5dedbec729`

| 文件 | 入口符号 | 校验 |
|---|---|---|
| [packages/playwright-core/src/server/dom.ts](https://github.com/microsoft/playwright/blob/0ad26b38902449d9347536c97a34cc5dedbec729/packages/playwright-core/src/server/dom.ts) | _retryPointerAction: 364, 530, 543, 556, 569; _performPointerAction: 380, 384 | ok |

