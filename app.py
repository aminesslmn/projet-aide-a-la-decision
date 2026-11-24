"""Streamlit demo:  streamlit run app.py"""
import numpy as np, pandas as pd, streamlit as st
from collections import Counter
from generators import generate_preferences, make_capacities, slides_example
from algorithms import ALGORITHMS
from metrics import (student_metrics, school_metrics, find_blocking, beneficial_swaps,
                     profitable_lies, rank_maps)

st.set_page_config(page_title="Stable matching lab", layout="wide")
st.title("Stable matching lab")
S, H = (lambda i: f"i{i+1}"), (lambda j: f"s{j+1}")

# ---------------- sidebar ----------------
with st.sidebar:
    st.header("Instance")
    if st.checkbox("Course example (3 students)", value=True):
        sp, hp, caps = slides_example()
    else:
        n = st.slider("Students", 5, 300, 40)
        m = st.slider("Schools", 2, 30, 6)
        slack = st.slider("Seats / students", 0.5, 2.0, 1.1, 0.05)
        corr = st.slider("Preference correlation", 0.0, 1.0, 0.3, 0.05,
                         help="0 = independent tastes, 1 = everybody agrees")
        k = st.slider("List length (0 = full)", 0, m, 0)
        seed = st.number_input("Seed", 0, 10_000, 42)
        sp, hp = generate_preferences(n, m, corr, k or None, seed)
        caps = make_capacities(n, m, slack, seed)
    n, m = len(sp), len(hp)
    st.caption(f"{n} students, {m} schools, {sum(caps)} seats")

with st.expander("Preferences"):
    c1, c2 = st.columns(2)
    c1.dataframe(pd.DataFrame({S(i): [", ".join(H(j) for j in p)] for i, p in enumerate(sp)}).T
                 .rename(columns={0: "student ranking"}))
    c2.dataframe(pd.DataFrame({H(j): [", ".join(S(i) for i in p[:15]) + (" ..." if len(p) > 15 else ""), caps[j]]
                               for j, p in enumerate(hp)}, index=["priority order", "capacity"]).T)

t1, t2, t3, t4 = st.tabs(["Step by step", "Compare algorithms", "Correlation sweep", "Manipulation test"])

# ---------------- step by step ----------------
with t1:
    name = st.radio("Algorithm", ["DA (students propose)", "Boston"], horizontal=True)
    res = ALGORITHMS[name](sp, hp, caps)
    r = st.slider("Round", 1, len(res.rounds), 1) if len(res.rounds) > 1 else 1
    rd = res.rounds[r - 1]
    a, b, c = st.columns(3)
    a.subheader("Proposals"); a.write("\n".join(f"- {S(i)} → {H(j)}" for i, j in rd.proposals) or "-")
    b.subheader("Rejections"); b.write("\n".join(f"- {S(i)} ✗ {H(j)}" for i, j in rd.rejections) or "none")
    label = "Tentatively held" if name.startswith("DA") else "Definitively admitted"
    c.subheader(label)
    c.write("\n".join(f"- {H(j)}: {', '.join(S(i) for i in L) or '-'}" for j, L in rd.held.items()))
    if r == len(res.rounds):
        st.success("Final matching: " + ", ".join(f"({S(i)},{H(j)})" if j >= 0 else f"({S(i)},∅)"
                                                  for i, j in enumerate(res.assignment)) if n <= 12
                   else f"Final matching reached after {len(res.rounds)} rounds.")

# ---------------- compare ----------------
with t2:
    rows, hists = {}, {}
    rs = rank_maps(sp)
    for nm, fn in ALGORITHMS.items():
        a_ = fn(sp, hp, caps).assignment
        bl = find_blocking(a_, sp, hp, caps)
        sm, hm = student_metrics(a_, sp), school_metrics(a_, hp, caps)
        rows[nm] = {"justified envy pairs": sum(k == "envy" for *_, k in bl),
                    "empty-seat blocking pairs": sum(k == "empty_seat" for *_, k in bl),
                    "beneficial swaps": len(beneficial_swaps(a_, sp)) if n <= 400 else None,
                    "students: avg rank": sm["avg_rank"], "students: % 1st choice": sm["pct_first_choice"],
                    "students: worst rank": sm["worst_rank"], "students: Gini of ranks": sm["gini_ranks"],
                    "students: unmatched %": sm["unmatched_pct"], "students: Borda satisfaction": sm["borda_satisfaction"],
                    "schools: avg priority rank": hm["avg_priority_rank"],
                    "schools: Borda satisfaction": hm["borda_satisfaction"], "schools: fill rate %": hm["fill_rate_pct"]}
        hists[nm] = Counter(rs[i][j] + 1 for i, j in enumerate(a_) if j >= 0)
    st.dataframe(pd.DataFrame(rows).style.format(precision=2, na_rep="-"), width="stretch")
    st.subheader("Distribution of obtained ranks (students)")
    st.bar_chart(pd.DataFrame(hists).fillna(0).sort_index())
    st.caption("Stable = 0 blocking pairs. DA has none; Boston typically does. "
               "A beneficial swap is the efficiency price of respecting priorities.")

# ---------------- sweep ----------------
with t3:
    st.write("Averages over random instances using the size settings of the sidebar "
             "(or 40 students / 6 schools with the course example).")
    reps = st.slider("Repetitions per point", 3, 30, 10)
    if st.button("Run sweep"):
        nn, mm = (n, m) if n > 3 else (40, 6)
        rows, bar = [], st.progress(0.0)
        cs = np.linspace(0, 1, 6)
        for ci, cval in enumerate(cs):
            for rep in range(reps):
                sp_, hp_ = generate_preferences(nn, mm, cval, seed=1000 + rep)
                cp_ = make_capacities(nn, mm, 1.1, seed=rep)
                for nm in ["DA (students propose)", "DA (schools propose)", "Boston"]:
                    a_ = ALGORITHMS[nm](sp_, hp_, cp_).assignment
                    sm = student_metrics(a_, sp_)
                    rows.append({"correlation": cval, "algorithm": nm, "avg rank": sm["avg_rank"],
                                 "% 1st choice": sm["pct_first_choice"],
                                 "justified envy": sum(k == "envy" for *_, k in find_blocking(a_, sp_, hp_, cp_))})
            bar.progress((ci + 1) / len(cs))
        df = pd.DataFrame(rows).groupby(["correlation", "algorithm"]).mean().reset_index()
        for col in ["avg rank", "% 1st choice", "justified envy"]:
            st.subheader(col)
            st.line_chart(df.pivot(index="correlation", columns="algorithm", values=col))

# ---------------- manipulation ----------------
with t4:
    st.write("Searches simple lies (put one school first, swap two neighbours) that make a student "
             "end up with a school she truly prefers.")
    lim = st.slider("Students tested", 1, min(n, 25), min(n, 10))
    if st.button("Search for profitable lies"):
        for nm in ["DA (students propose)", "Boston"]:
            f = profitable_lies(ALGORITHMS[nm], sp, hp, caps, students=range(lim))
            st.markdown(f"**{nm}**: {len(f)} / {lim} students can gain by lying")
            if f:
                st.dataframe(pd.DataFrame([{"student": S(i), "lie": " > ".join(H(j) for j in lie),
                                            "true rank (honest)": "∅" if h == float("inf") else int(h) + 1,
                                            "true rank (lying)": "∅" if w == float("inf") else int(w) + 1}
                                           for i, lie, h, w in f]))
