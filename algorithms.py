"""Matching algorithms: deferred acceptance (both sides, with capacities) and Boston."""
from dataclasses import dataclass, field
from heapq import heappush, heappop
from collections import defaultdict, deque


@dataclass
class Round:
    number: int
    proposals: list          # (student, school)
    rejections: list         # (student, school)
    held: dict               # school -> students held (tentative for DA, final for Boston)


@dataclass
class Result:
    assignment: list         # student -> school, -1 if unmatched
    rounds: list = field(default_factory=list)
    name: str = ""


def _rank_maps(prefs):
    return [{x: r for r, x in enumerate(p)} for p in prefs]


def deferred_acceptance(sp, hp, caps):
    """Gale-Shapley, students propose. Schools keep the best candidates *temporarily*."""
    n, m = len(sp), len(hp)
    rh = _rank_maps(hp)
    nxt = [0] * n
    held = [[] for _ in range(m)]          # max-heaps on school rank (worst on top)
    free = [i for i in range(n)]
    rounds, k = [], 0
    while free:
        k += 1
        props = defaultdict(list)
        for i in free:
            if nxt[i] < len(sp[i]):
                props[sp[i][nxt[i]]].append(i)
                nxt[i] += 1
        proposals = [(i, j) for j, L in props.items() for i in L]
        rejected = []
        for j, L in props.items():
            for i in L:
                heappush(held[j], (-rh[j][i], i))
            while len(held[j]) > caps[j]:
                _, i = heappop(held[j])
                rejected.append((i, j))
        free = [i for i, _ in rejected if nxt[i] < len(sp[i])]
        rounds.append(Round(k, sorted(proposals), sorted(rejected),
                            {j: sorted(i for _, i in held[j]) for j in range(m)}))
    assign = [-1] * n
    for j in range(m):
        for _, i in held[j]:
            assign[i] = j
    return Result(assign, rounds, "DA (students propose)")


def deferred_acceptance_schools(sp, hp, caps):
    """School-proposing version (schools make offers, students hold their best)."""
    n, m = len(sp), len(hp)
    rs = _rank_maps(sp)
    nxt = [0] * m
    cur = [-1] * n
    holding = [0] * m
    queue = deque(range(m))
    while queue:
        j = queue.popleft()
        while holding[j] < caps[j] and nxt[j] < len(hp[j]):
            i = hp[j][nxt[j]]
            nxt[j] += 1
            if j not in rs[i]:
                continue                       # unacceptable school for this student
            if cur[i] == -1:
                cur[i] = j; holding[j] += 1
            elif rs[i][j] < rs[i][cur[i]]:
                old = cur[i]
                holding[old] -= 1
                cur[i] = j; holding[j] += 1
                queue.append(old)              # old school has a free seat again
    return Result(cur, [], "DA (schools propose)")


def boston(sp, hp, caps):
    """Boston: at step k, unassigned students apply to their k-th choice and
    admissions are DEFINITIVE."""
    n, m = len(sp), len(hp)
    rh = _rank_maps(hp)
    left = list(caps)
    assign = [-1] * n
    final = [[] for _ in range(m)]
    rounds = []
    longest = max((len(p) for p in sp), default=0)
    for k in range(longest):
        props = defaultdict(list)
        for i in range(n):
            if assign[i] == -1 and k < len(sp[i]):
                props[sp[i][k]].append(i)
        rejected = []
        for j, L in props.items():
            L.sort(key=lambda i: rh[j][i])
            for i in L[: left[j]]:
                assign[i] = j; final[j].append(i)
            rejected += [(i, j) for i in L[left[j]:]]
            left[j] -= min(left[j], len(L))
        rounds.append(Round(k + 1, sorted((i, j) for j, L in props.items() for i in L),
                            sorted(rejected), {j: sorted(final[j]) for j in range(m)}))
    return Result(assign, rounds, "Boston")


ALGORITHMS = {
    "DA (students propose)": deferred_acceptance,
    "DA (schools propose)": deferred_acceptance_schools,
    "Boston": boston,
}
