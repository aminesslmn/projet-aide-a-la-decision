"""Satisfaction, stability, efficiency and manipulation analysis."""
import numpy as np

INF = float("inf")


def rank_maps(prefs):
    return [{x: r for r, x in enumerate(p)} for p in prefs]


def gini(values):
    v = np.sort(np.asarray(values, dtype=float))
    if len(v) == 0 or v.sum() == 0:
        return 0.0
    n = len(v)
    return float((2 * np.arange(1, n + 1) - n - 1).dot(v) / (n * v.sum()))


def student_metrics(assign, sp):
    rs = rank_maps(sp)
    n = len(sp)
    ranks = [rs[i][j] + 1 for i, j in enumerate(assign) if j >= 0]       # 1 = first choice
    borda = [1 - (rs[i][j]) / max(len(sp[i]) - 1, 1) if j >= 0 else 0.0
             for i, j in enumerate(assign)]                               # 1 best, 0 worst/unmatched
    return {
        "avg_rank": float(np.mean(ranks)) if ranks else float("nan"),
        "pct_first_choice": 100 * sum(r == 1 for r in ranks) / n,
        "pct_top3": 100 * sum(r <= 3 for r in ranks) / n,
        "worst_rank": max(ranks) if ranks else None,
        "unmatched_pct": 100 * (n - len(ranks)) / n,
        "gini_ranks": gini(ranks),
        "borda_satisfaction": float(np.mean(borda)),
    }


def school_metrics(assign, hp, caps):
    rh = rank_maps(hp)
    n, m = len(assign), len(hp)
    admitted = [[] for _ in range(m)]
    for i, j in enumerate(assign):
        if j >= 0:
            admitted[j].append(i)
    ranks = [rh[j][i] for j in range(m) for i in admitted[j]]            # 0 = best candidate
    return {
        "avg_priority_rank": float(np.mean(ranks)) + 1 if ranks else float("nan"),
        "borda_satisfaction": float(np.mean([1 - r / max(n - 1, 1) for r in ranks])) if ranks else 0.0,
        "fill_rate_pct": 100 * len(ranks) / sum(caps),
        "empty_seats": sum(caps) - len(ranks),
    }


def find_blocking(assign, sp, hp, caps):
    """List of (student, school, kind). kind='envy' (justified envy: refused although higher
    priority than an admitted student) or 'empty_seat'. Matching is stable iff list is empty."""
    n, m = len(sp), len(hp)
    rs, rh = rank_maps(sp), rank_maps(hp)
    admitted = [[] for _ in range(m)]
    for i, j in enumerate(assign):
        if j >= 0:
            admitted[j].append(i)
    worst = [max((rh[j][i] for i in admitted[j]), default=None) for j in range(m)]
    out = []
    for i in range(n):
        cur = rs[i][assign[i]] if assign[i] >= 0 else INF
        for j in sp[i]:
            if rs[i][j] >= cur:
                break
            if len(admitted[j]) < caps[j]:
                out.append((i, j, "empty_seat"))
            elif rh[j][i] < worst[j]:
                out.append((i, j, "envy"))
    return out


def beneficial_swaps(assign, sp):
    """Pairs of students who would BOTH strictly gain by exchanging seats
    (the efficiency cost of respecting priorities, last slide of the course)."""
    rs = rank_maps(sp)
    out = []
    for i in range(len(sp)):
        a = assign[i]
        if a < 0:
            continue
        for k in range(i + 1, len(sp)):
            b = assign[k]
            if b < 0 or a == b or b not in rs[i] or a not in rs[k]:
                continue
            if rs[i][b] < rs[i][a] and rs[k][a] < rs[k][b]:
                out.append((i, k))
    return out


def profitable_lies(algo, sp, hp, caps, students=None):
    """Search simple misreports (put one school first / swap two adjacent schools).
    Returns [(student, lie, true_rank_when_honest, true_rank_when_lying)] for students who gain.
    Rank is 0-based; inf = unmatched. Empty list for a strategy-proof algorithm."""
    base = algo(sp, hp, caps).assignment
    rs = rank_maps(sp)
    found = []
    for i in (range(len(sp)) if students is None else students):
        honest = rs[i][base[i]] if base[i] >= 0 else INF
        lies = [[j] + [x for x in sp[i] if x != j] for j in sp[i]]
        for p in range(len(sp[i]) - 1):
            l = list(sp[i]); l[p], l[p + 1] = l[p + 1], l[p]; lies.append(l)
        for lie in lies:
            if lie == sp[i]:
                continue
            res = algo(sp[:i] + [lie] + sp[i + 1:], hp, caps).assignment[i]
            new = rs[i][res] if res >= 0 else INF
            if new < honest:
                found.append((i, lie, honest, new))
                break
    return found
