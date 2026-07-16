"""Exact ft x parsed-correctness crosstabs (overall + per domain) + ft x y + census -> JSON artifact.
CPU-only; run on Aquaman. Feeds paper Appendix A (reviewer-verifiable label-semantics table)."""
import collections, glob, json, os
BASE = os.path.expanduser("~/ur2phd/upstream/FaithCoT-BENCH/faithcot_data/faithcot")
DOMAINS = ["truthfulqa", "logiqa", "aqua", "HLE_BIO"]
MDIRS = ["llama-3.1-8b-instruct", "Qwen2.5-7B-Instruct", "gpt-4o-mini", "gemini-2.5-flash"]
rows = []
for dom in DOMAINS:
    for md in MDIRS:
        for f in glob.glob(os.path.join(BASE, dom, md, "response_*.json")):
            d = json.load(open(f)); s = d.get("sample_0", {})
            rows.append(dict(dom=dom, md=md, ft=d.get("faithful_type"), y=d.get("unfaithfulness"),
                             label=str(d.get("label")), parsed=s.get("parsed_final_answer")))
def cstat(rr):
    out = {}
    for ft in (1, 2, 3, 4):
        c = w = u = 0
        for r in rr:
            if r["ft"] != ft: continue
            if r["parsed"] is None or str(r["parsed"]).strip() in ("", "None"): u += 1
            elif str(r["parsed"]).upper()[:1] == r["label"].upper()[:1]: c += 1
            else: w += 1
        out[f"ft{ft}"] = dict(parsed_correct=c, parsed_incorrect=w, unparsed=u)
    return out
res = dict(
    census=dict(total=len(rows),
                y_present=sum(r["y"] is not None for r in rows),
                ft_1to4=sum(r["ft"] in (1, 2, 3, 4) for r in rows),
                ft_other=dict(collections.Counter(str(r["ft"]) for r in rows if r["ft"] not in (1, 2, 3, 4)))),
    overall=cstat(rows),
    by_domain={dom: cstat([r for r in rows if r["dom"] == dom]) for dom in DOMAINS},
    ft_x_y=dict((f"ft{ft},y{y}", n) for (ft, y), n in sorted(
        collections.Counter((r["ft"], r["y"]) for r in rows if r["ft"] in (1, 2, 3, 4) and r["y"] is not None).items())),
)
out = os.path.expanduser("~/synth/results/label_crosstabs.json")
json.dump(res, open(out, "w"), indent=1)
print(json.dumps(res["overall"], indent=1))
print("census:", res["census"]); print("->", out)
