"""Four-document teaching demo; no dependencies, network calls or file writes.

Textbook BM25 and exact cosine only. This is not a Lucene/ANN implementation.
Run default checks with --check; omit that flag when modifying the exercise data.
"""

import argparse
from collections import Counter, defaultdict
from math import isclose, log, sqrt


DOCS = {
    "D1": {"text": "Python 部署 超时 排查", "tenant": "A", "sdk": "v2"},
    "D2": {"text": "Java 部署 配置 指南", "tenant": "A", "sdk": "v1"},
    "D3": {"text": "Python 请求 超时 超时 处理", "tenant": "B", "sdk": "v2"},
    "D4": {"text": "Python 部署 参数 参数 参数 检查", "tenant": "A", "sdk": "v2"},
}
VECTORS = {"D1": (0.95, 0.05), "D2": (0, 1), "D3": (1, 0), "D4": (0.8, 0.2)}
QUERY = "部署 超时"
QUERY_VECTOR = (1, 0)
K = 2
FUSION_WINDOW = 3


def cosine(left, right):
    if len(left) != len(right):
        raise ValueError("Vector dimensions must match")
    denominator = sqrt(sum(x * x for x in left) * sum(y * y for y in right))
    if denominator == 0:
        raise ValueError("Cosine is undefined for zero vectors")
    return sum(x * y for x, y in zip(left, right)) / denominator


def rank(scores):
    # Stable document-ID tie breaking is only a teaching convention.
    return sorted(scores, key=lambda doc_id: (-scores[doc_id], doc_id))


def rrf(rankings, constant=60):
    if constant < 0:
        raise ValueError("RRF constant must be nonnegative")
    scores = defaultdict(float)
    for ranking in rankings:
        if len(ranking) != len(set(ranking)):
            raise ValueError("Each ranking must contain unique document IDs")
        for position, doc_id in enumerate(ranking, start=1):
            scores[doc_id] += 1 / (constant + position)
    return dict(scores)


def run(check=False):
    tokens = {doc_id: doc["text"].split() for doc_id, doc in DOCS.items()}
    frequencies = {doc_id: Counter(words) for doc_id, words in tokens.items()}
    postings = defaultdict(list)
    for doc_id, counts in frequencies.items():
        for term in counts:
            postings[term].append(doc_id)

    # Dedupe query terms for this deliberately simple scoring model.
    query_terms = list(dict.fromkeys(QUERY.split()))
    match_sets = [set(postings.get(term, [])) for term in query_terms]
    any_match = set().union(*match_sets)
    all_match = set.intersection(*match_sets) if match_sets else set()
    print("查询：", QUERY)
    print("倒排：", {term: postings.get(term, []) for term in query_terms})
    print("OR：", sorted(any_match), "AND：", sorted(all_match))

    doc_order = list(DOCS)
    tenant_mask = sum(1 << i for i, d in enumerate(doc_order) if DOCS[d]["tenant"] == "A")
    sdk_mask = sum(1 << i for i, d in enumerate(doc_order) if DOCS[d]["sdk"] == "v2")
    allowed_mask = tenant_mask & sdk_mask
    allowed = {d for i, d in enumerate(doc_order) if allowed_mask & (1 << i)}
    display_bits = lambda mask: " ".join(str((mask >> i) & 1) for i in range(len(doc_order)))
    print("位图顺序：", doc_order)
    print("租户 A：", display_bits(tenant_mask))
    print("SDK v2：", display_bits(sdk_mask))
    print("AND：   ", display_bits(allowed_mask), sorted(allowed))

    n = len(DOCS)
    average_length = sum(map(len, tokens.values())) / n
    k1, b = 1.2, 0.75
    scores = {}
    for doc_id in sorted(any_match):
        score = 0.0
        for term in query_terms:
            tf = frequencies[doc_id][term]
            df = len(postings.get(term, []))
            idf = log(1 + (n - df + 0.5) / (df + 0.5))
            denominator = tf + k1 * (1 - b + b * len(tokens[doc_id]) / average_length)
            score += idf * tf * (k1 + 1) / denominator
        scores[doc_id] = score
    lexical = rank(scores)
    print("BM25：", [(d, round(scores[d], 6)) for d in lexical])

    vector_scores = {d: cosine(QUERY_VECTOR, vector) for d, vector in VECTORS.items()}
    vector_order = rank(vector_scores)
    print("精确余弦：", [(d, round(vector_scores[d], 6)) for d in vector_order])
    postfiltered = [d for d in vector_order[:K] if d in allowed]
    prefiltered = rank({d: score for d, score in vector_scores.items() if d in allowed})[:K]
    print(f"全库 Top-{K} 后过滤：", postfiltered)
    print(f"允许集合内精确 Top-{K}：", prefiltered)

    unfiltered_rrf = rrf([lexical[:FUSION_WINDOW], vector_order[:FUSION_WINDOW]])
    print("无过滤 RRF（仅演示公式）：", [(d, round(unfiltered_rrf[d], 6)) for d in rank(unfiltered_rrf)])
    filtered_lexical = [d for d in lexical if d in allowed]
    filtered_vector = [d for d in vector_order if d in allowed]
    safe_rrf = rrf([filtered_lexical[:FUSION_WINDOW], filtered_vector[:FUSION_WINDOW]])
    print("两路均遵守过滤后的 RRF：", [(d, round(safe_rrf[d], 6)) for d in rank(safe_rrf)])

    if check:
        assert lexical == ["D1", "D3", "D2", "D4"]
        expected = {"D1": 1.1223162353975633, "D2": 0.3813046715252945,
                    "D3": 0.9391751101266034, "D4": 0.3220089126703891}
        assert all(isclose(scores[d], score, rel_tol=1e-12) for d, score in expected.items())
        assert any_match == set(DOCS) and all_match == {"D1"}
        assert display_bits(allowed_mask) == "1 0 0 1"
        assert vector_order == ["D3", "D1", "D4", "D2"]
        assert postfiltered == ["D1"] and prefiltered == ["D1", "D4"]
        assert isclose(unfiltered_rrf["D1"], 1 / 61 + 1 / 62)
        assert isclose(unfiltered_rrf["D1"], unfiltered_rrf["D3"])
        assert isclose(unfiltered_rrf["D2"], 1 / 63)
        assert set(safe_rrf) == {"D1", "D4"}
        assert isclose(cosine((1, 0), (2, 0)), 1.0)
        assert rrf([[], []]) == {}
        print("默认示例的数值与集合检查全部通过。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check the unchanged default example")
    run(parser.parse_args().check)
