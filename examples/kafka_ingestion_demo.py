"""Deterministic state-machine examples, not a Kafka client or durable storage.

Run with Python 3.9+. State deliberately retained across a simulated crash
stands for durable state; a Python dict itself provides no durability guarantee.
"""
from copy import deepcopy
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Event:
    event_id: str
    entity_id: str
    version: int
    price: Optional[int]
    deleted: bool = False


class VersionedIndex:
    """Models an atomic version+state update within one index generation.

    The model runs sequentially. A real implementation must implement atomic
    compare-and-write and a suitable durable acknowledgment, not copy this dict.
    """

    def __init__(self, generation):
        self.generation = generation
        self.state = {}
        self.visible = {}
        self.changes = 0

    def apply(self, event):
        incoming = (event.version, event.price, event.deleted)
        current = self.state.get(event.entity_id)
        if current is not None:
            if event.version < current[0]:
                return "stale"
            if event.version == current[0]:
                if incoming != current:
                    raise ValueError("same entity version has conflicting content")
                return "duplicate"
        self.state[event.entity_id] = incoming
        self.changes += 1
        return "applied"

    def refresh(self):
        self.visible = deepcopy(self.state)

    def search_price(self, entity_id):
        value = self.visible.get(entity_id)
        return None if value is None or value[2] else value[1]


BASE = Event("evt-P42-7", "shopA:P42", 7, 100)
CHANGE = Event("evt-P42-8", "shopA:P42", 8, 80)
NEWER = Event("evt-P42-9", "shopA:P42", 9, 75)
DELETE = Event("evt-P42-10", "shopA:P42", 10, None, True)


def initial_index(generation="G1"):
    index = VersionedIndex(generation)
    index.apply(BASE)
    index.refresh()
    index.changes = 0
    return index


def safe_next_offset(committed, delivered_offsets, completed):
    """Safe (possibly conservative) frontier for one partition's delivered list.

    Offsets are sorted actual deliveries, NOT every integer in the log. This
    teaching model omits rebalance epochs, leader epochs and delivery batches.
    No record not in `delivered_offsets` may be silently treated as completed.
    """
    assert delivered_offsets == sorted(set(delivered_offsets))
    assert all(offset >= committed for offset in delivered_offsets)
    assert completed <= set(delivered_offsets)
    next_offset = committed
    for offset in delivered_offsets:
        if offset not in completed:
            break
        next_offset = offset + 1
    return next_offset


def demo_early_commit():
    index = initial_index()
    log = {100: CHANGE}
    committed = 101  # Wrong: commit before applying offset 100.
    # CRASH: pending work disappears; committed and index.state survive in model.
    resumed = [o for o in log if o >= committed]
    assert resumed == []
    assert index.state[BASE.entity_id][1] == 100
    print("1 错误顺序：已提交 101；恢复无待处理消息；价格仍为 100（漏应用）。")


def demo_replay():
    index = initial_index()
    committed = 100
    assert index.apply(CHANGE) == "applied"
    # CRASH after sink acknowledgment, before committing 101.
    assert committed == 100
    second = index.apply(CHANGE)
    assert second == "duplicate"
    committed = 101
    assert index.state[BASE.entity_id] == (8, 80, False)
    assert index.changes == 1
    print("2 正确重放：100 投递两次；状态只改变一次；价格 80；提交 101。")


def demo_versions():
    index = initial_index()
    assert index.apply(NEWER) == "applied"
    assert index.apply(CHANGE) == "stale"
    assert index.state[BASE.entity_id] == (9, 75, False)
    assert index.apply(DELETE) == "applied"
    assert index.apply(CHANGE) == "stale"
    index.refresh()
    assert index.search_price(BASE.entity_id) is None
    assert index.state[BASE.entity_id] == (10, None, True)
    assert index.apply(DELETE) == "duplicate"
    # Conflict at the SAME version is not safe to call a duplicate.
    conflict = Event("different-event", BASE.entity_id, 10, 60)
    try:
        index.apply(conflict)
    except ValueError:
        pass
    else:
        raise AssertionError("conflicting payload was silently accepted")
    print("3 版本保护：9 挡住 8；删除版本 10 挡住旧更新；同版本异内容报错。")


def demo_frontier():
    delivered = [100, 101, 102]
    completed = {101, 102}
    assert safe_next_offset(100, delivered, completed) == 100
    completed.add(100)
    assert safe_next_offset(100, delivered, completed) == 103
    # A delivery can have offset gaps. Never wait for undelivered integer 101.
    assert safe_next_offset(100, [100, 102], {100, 102}) == 103
    assert safe_next_offset(100, [100, 102], {102}) == 100
    assert safe_next_offset(100, [], set()) == 100
    print("4 连续前缀：只完成 101/102 → 提交位置 100；再完成 100 → 103。")


def demo_delta():
    price = 100
    price -= 20
    price -= 20  # replay the same relative mutation
    assert price == 60
    print("5 非幂等指令：同一次减 20 重放后，100 → 80 → 60（错误）。")


def demo_generation():
    g1, g2 = initial_index("G1"), initial_index("G2")
    seen_globally = set()
    g1.apply(CHANGE)
    seen_globally.add(CHANGE.event_id)
    # WRONG design skips the event for a different target generation.
    if CHANGE.event_id not in seen_globally:
        g2.apply(CHANGE)
    assert g2.state[BASE.entity_id][1] == 100
    # CORRECT model scopes state/version checks to the destination generation.
    assert g2.apply(CHANGE) == "applied"
    assert g2.state[BASE.entity_id][1] == 80
    print("6 重建代次：G1 处理过不代表 G2 已处理；G2 仍需从 100 更新到 80。")


def demo_visibility():
    index = initial_index()
    index.apply(CHANGE)
    assert index.state[BASE.entity_id][1] == 80
    assert index.search_price(BASE.entity_id) == 100
    index.refresh()
    assert index.search_price(BASE.entity_id) == 80
    print("7 可见性：写入状态已是 80；refresh 前查询 100，之后查询 80。")


def main():
    for demo in (demo_early_commit, demo_replay, demo_versions, demo_frontier,
                 demo_delta, demo_generation, demo_visibility):
        demo()
    print("全部断言通过。仅为顺序状态模拟，未验证真实集群、磁盘或网络故障。")


if __name__ == "__main__":
    main()
