import pytest
from generators import generate_preferences, make_capacities, slides_example
from algorithms import deferred_acceptance, deferred_acceptance_schools, boston
from metrics import find_blocking, profitable_lies, beneficial_swaps, student_metrics, rank_maps


def test_slides_da():
    sp, hp, caps = slides_example()
    assert deferred_acceptance(sp, hp, caps).assignment == [0, 1, 2]   # (i1,s1),(i2,s2),(i3,s3)


def test_slides_boston():
    sp, hp, caps = slides_example()
    a = boston(sp, hp, caps).assignment
    assert a == [1, 2, 0]                                              # i1->s2, i2->s3, i3->s1
    assert any(k == "envy" and i == 1 for i, _, k in find_blocking(a, sp, hp, caps))


def test_slides_swap_cost():
    sp, hp, caps = slides_example()
    assert beneficial_swaps(deferred_acceptance(sp, hp, caps).assignment, sp) == [(0, 1)]


def test_slides_manipulation():
    sp, hp, caps = slides_example()
    assert any(i == 1 for i, *_ in profitable_lies(boston, sp, hp, caps))
    assert profitable_lies(lambda a, b, c: deferred_acceptance(a, b, c), sp, hp, caps) == []


@pytest.mark.parametrize("seed", range(15))
@pytest.mark.parametrize("corr", [0, 0.5, 0.9])
@pytest.mark.parametrize("algo", [deferred_acceptance, deferred_acceptance_schools])
def test_da_stable_and_capacity(algo, corr, seed):
    n, m = 40, 6
    sp, hp = generate_preferences(n, m, corr, list_length=4 if seed % 2 else None, seed=seed)
    caps = make_capacities(n, m, slack=1.0 if seed % 3 else 0.7, seed=seed)
    a = algo(sp, hp, caps).assignment
    assert find_blocking(a, sp, hp, caps) == []
    for j in range(m):
        assert a.count(j) <= caps[j]


@pytest.mark.parametrize("seed", range(10))
def test_student_optimality(seed):
    n, m = 40, 6
    sp, hp = generate_preferences(n, m, 0.5, seed=seed)
    caps = make_capacities(n, m, 1.1, seed)
    a = deferred_acceptance(sp, hp, caps).assignment
    b = deferred_acceptance_schools(sp, hp, caps).assignment
    rs = rank_maps(sp)
    assert all(rs[i][a[i]] <= rs[i][b[i]] for i in range(n))


def test_da_no_lies_random():
    sp, hp = generate_preferences(12, 4, 0.3, seed=1)
    caps = make_capacities(12, 4, 1.0, 1)
    assert profitable_lies(deferred_acceptance, sp, hp, caps) == []
