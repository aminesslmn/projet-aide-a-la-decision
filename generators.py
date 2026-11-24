"""Random instance generation (students <-> schools, many-to-one)."""
import numpy as np


def make_rng(seed=None):
    return seed if isinstance(seed, np.random.Generator) else np.random.default_rng(seed)


def make_capacities(n_students, n_schools, slack=1.2, seed=None):
    """Total seats = ceil(slack * n_students), spread as evenly as possible.
    slack < 1 -> scarcity (some students stay unmatched)."""
    rng = make_rng(seed)
    total = int(np.ceil(n_students * slack))
    caps = np.full(n_schools, total // n_schools)
    extra = rng.permutation(n_schools)[: total % n_schools]
    caps[extra] += 1
    return caps.tolist()


def generate_preferences(n_students, n_schools, correlation=0.0, list_length=None, seed=None):
    """Utilities = c * (common component) + (1-c) * (personal noise).

    correlation=0 -> independent uniform-like rankings;
    correlation=1 -> everybody agrees (popular schools / strong students).
    list_length   -> students only rank their top-k schools (truncated lists).
    Returns (student_prefs, school_prefs): lists of lists of indices, best first.
    """
    rng = make_rng(seed)
    c = correlation
    school_pop = rng.normal(size=n_schools)
    student_qual = rng.normal(size=n_students)
    u_students = c * school_pop[None, :] + (1 - c) * rng.normal(size=(n_students, n_schools))
    u_schools = c * student_qual[None, :] + (1 - c) * rng.normal(size=(n_schools, n_students))
    sp = np.argsort(-u_students, axis=1)
    hp = np.argsort(-u_schools, axis=1)
    if list_length:
        sp = sp[:, :list_length]
    return sp.tolist(), hp.tolist()


def slides_example():
    """The 3-student example of the course (i1..i3 -> 0..2, s1..s3 -> 0..2)."""
    sp = [[1, 0, 2], [0, 1, 2], [0, 1, 2]]
    hp = [[0, 2, 1], [1, 0, 2], [1, 0, 2]]
    return sp, hp, [1, 1, 1]
