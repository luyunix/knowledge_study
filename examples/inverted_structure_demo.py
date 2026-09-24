"""A deterministic illustration of term metadata, postings streams and cursors.

Array offsets are list indexes, not real Lucene file offsets. No external I/O.
"""

from collections import defaultdict
from search_index_demo import DOCS


def build_index(documents):
    grouped = defaultdict(lambda: defaultdict(list))
    for doc_id, document in enumerate(documents.values()):
        for position, term in enumerate(document["text"].split(), start=1):
            grouped[term][doc_id].append(position)

    terms, doc_ids, frequencies, positions = {}, [], [], []
    for term in sorted(grouped):
        posting = grouped[term]
        terms[term] = {
            "doc_start": len(doc_ids),
            "freq_start": len(frequencies),
            "pos_start": len(positions),
            "df": len(posting),
            "total_tf": sum(map(len, posting.values())),
        }
        for doc_id in sorted(posting):
            doc_ids.append(doc_id)
            frequencies.append(len(posting[doc_id]))
            positions.extend(posting[doc_id])
    return terms, doc_ids, frequencies, positions


def read_postings(index, term):
    terms, doc_ids, frequencies, positions = index
    if term not in terms:
        return []
    metadata = terms[term]
    position_cursor = metadata["pos_start"]
    result = []
    for i in range(metadata["df"]):
        doc_id = doc_ids[metadata["doc_start"] + i]
        frequency = frequencies[metadata["freq_start"] + i]
        result.append((doc_id, frequency, positions[position_cursor:position_cursor + frequency]))
        position_cursor += frequency
    return result


def intersect(left, right, trace=False):
    a = b = 0
    matches = []
    while a < len(left) and b < len(right):
        if trace:
            print(f"比较 {left[a]} 与 {right[b]}；此前结果 {matches}")
        if left[a] == right[b]:
            matches.append(left[a])
            a += 1
            b += 1
        elif left[a] < right[b]:
            a += 1
        else:
            b += 1
    return matches


def phrase_matches(index, first, second):
    left = {doc_id: positions for doc_id, _, positions in read_postings(index, first)}
    right = {doc_id: set(positions) for doc_id, _, positions in read_postings(index, second)}
    return [doc_id for doc_id in sorted(left.keys() & right.keys())
            if any(position + 1 in right[doc_id] for position in left[doc_id])]


def main():
    index = build_index(DOCS)
    term_metadata = index[0]
    assert len(term_metadata) == 11
    assert sum(m["total_tf"] for m in term_metadata.values()) == 19
    timeout = read_postings(index, "超时")
    assert timeout == [(0, 1, [3]), (2, 2, [3, 4])]
    assert term_metadata["超时"]["df"] == 2
    assert term_metadata["超时"]["total_tf"] == 3
    assert read_postings(index, "参数") == [(3, 3, [3, 4, 5])]
    assert read_postings(index, "不存在") == []
    print("超时的词典元信息 ->", term_metadata["超时"])
    print("超时 ->", timeout)

    deployment_ids = [d for d, _, _ in read_postings(index, "部署")]
    timeout_ids = [d for d, _, _ in timeout]
    matches = intersect(deployment_ids, timeout_ids, trace=True)
    assert matches == [0]
    assert intersect([], timeout_ids) == []
    assert intersect([1], [2]) == []
    assert intersect([0, 2], [0, 1, 2]) == [0, 2]
    names = list(DOCS)
    print("部署 AND 超时 ->", matches, "->", [names[d] for d in matches])
    assert phrase_matches(index, "部署", "超时") == [0]
    assert phrase_matches(index, "超时", "部署") == []
    assert phrase_matches(index, "超时", "超时") == [2]
    print("短语 部署 超时 ->", phrase_matches(index, "部署", "超时"))
    print("短语 超时 部署 ->", phrase_matches(index, "超时", "部署"))
    print("全部结构与查询检查通过。")


if __name__ == "__main__":
    main()
