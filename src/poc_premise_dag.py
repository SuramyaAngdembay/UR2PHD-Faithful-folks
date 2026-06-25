"""
Proof-of-Concept: Premise DAG Construction + Faithfulness Analysis
=================================================================
Takes real FINE-CoT traces, constructs premise dependency DAGs using
heuristic premise extraction, computes graph metrics, and correlates
DAG structure with ground-truth faithfulness scores.

This is the core of our novelty: using PARC-style premise DAGs for
faithfulness detection (not just error detection).
"""

import json
import os
import re
import statistics
from collections import defaultdict
from pathlib import Path


# ─────────────────────────────────────────────────────────────────
# 1. DATA LOADING
# ─────────────────────────────────────────────────────────────────

def load_faithcot_traces(domain: str, model: str, base_path: str) -> list:
    """Load all FINE-CoT traces for a given domain/model pair."""
    dir_path = Path(base_path) / domain / model
    traces = []
    for f in sorted(dir_path.glob("response_*.json")):
        with open(f) as fh:
            data = json.load(fh)
        # Extract the sample_0 data (primary sample)
        if "sample_0" not in data:
            continue
        sample = data["sample_0"]
        
        # Get steps
        step_keys = sorted(
            [k for k in sample.keys() if k.startswith("step_")],
            key=lambda x: int(x.split("_")[1])
        )
        steps = [sample[k] for k in step_keys]
        
        # Get intermediate probabilities
        probs = sample.get("intermediate_answer_probabilities", [])
        
        traces.append({
            "file": f.name,
            "question": data.get("question", ""),
            "options": data.get("options", []),
            "label": data.get("label", ""),
            "steps": steps,
            "n_steps": len(steps),
            "soft_faithfulness": sample.get("soft_faithfulness", None),
            "hard_faithfulness": sample.get("hard_faithfulness", None),
            "final_answer": sample.get("parsed_final_answer", ""),
            "intermediate_probs": probs,
        })
    return traces


# ─────────────────────────────────────────────────────────────────
# 2. HEURISTIC PREMISE EXTRACTION
# ─────────────────────────────────────────────────────────────────

def extract_premises_heuristic(steps: list) -> dict:
    """
    Heuristic premise extraction without LLM calls.
    
    For each step, identify which earlier steps it likely depends on by:
    1. Shared entity/keyword overlap
    2. Pronoun resolution (pronouns → previous step)
    3. Logical connectors ("therefore", "so", "thus" → previous step)
    4. Step references ("from step X", "as mentioned" → referenced step)
    5. Default: each step depends on the immediately preceding step
    
    Returns: dict mapping step_index → list of premise step indices
    """
    premises = {}
    
    # Step 0 (the question) is always available as premise
    for i, step in enumerate(steps):
        step_lower = step.lower()
        step_premises = set()
        
        # Rule 1: Explicit step references
        refs = re.findall(r'step\s*(\d+)', step_lower)
        for ref in refs:
            ref_idx = int(ref) - 1  # Convert to 0-indexed
            if 0 <= ref_idx < i:
                step_premises.add(ref_idx)
        
        # Rule 2: Logical connectors → depends on previous step
        connectors = ['therefore', 'thus', 'hence', 'so,', 'consequently',
                      'as a result', 'this means', 'which means', 'it follows',
                      'we can conclude', 'the answer is', 'the correct answer']
        for conn in connectors:
            if conn in step_lower:
                if i > 0:
                    step_premises.add(i - 1)
                break
        
        # Rule 3: Backward references
        back_refs = ['as mentioned', 'from above', 'we know that', 
                     'we found', 'we calculated', 'as established',
                     'given that', 'since we', 'based on']
        for ref in back_refs:
            if ref in step_lower:
                # Reference to some earlier step — find by keyword overlap
                best_match = -1
                best_overlap = 0
                step_words = set(re.findall(r'\b\w+\b', step_lower))
                for j in range(i):
                    earlier_words = set(re.findall(r'\b\w+\b', steps[j].lower()))
                    overlap = len(step_words & earlier_words) - len(
                        {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'step',
                         'and', 'or', 'to', 'of', 'in', 'for', 'that', 'this',
                         'it', 'we', 'can', 'be', 'has', 'have', 'not', 'with'})
                    if overlap > best_overlap:
                        best_overlap = overlap
                        best_match = j
                if best_match >= 0 and best_overlap > 2:
                    step_premises.add(best_match)
        
        # Rule 4: Keyword overlap with earlier steps (shared entities)
        step_words = set(re.findall(r'\b[A-Z][a-z]+\b', step))  # Proper nouns
        step_numbers = set(re.findall(r'\b\d+\.?\d*\b', step))
        
        for j in range(i):
            earlier_words = set(re.findall(r'\b[A-Z][a-z]+\b', steps[j]))
            earlier_numbers = set(re.findall(r'\b\d+\.?\d*\b', steps[j]))
            
            # Shared proper nouns or numbers → likely dependency
            shared_entities = step_words & earlier_words
            shared_numbers = step_numbers & earlier_numbers
            
            if len(shared_entities) >= 2 or len(shared_numbers) >= 2:
                step_premises.add(j)
        
        # Rule 5: Default — if no premises found, depend on previous step
        if not step_premises and i > 0:
            step_premises.add(i - 1)
        
        # The question (step -1, conceptually step 0) is always a potential premise
        # We include it for the first substantive step
        if i == 0:
            step_premises.add(-1)  # -1 = the question itself
        
        premises[i] = sorted(step_premises)
    
    return premises


# ─────────────────────────────────────────────────────────────────
# 3. DAG CONSTRUCTION & GRAPH METRICS
# ─────────────────────────────────────────────────────────────────

def build_dag(n_steps: int, premises: dict) -> dict:
    """Build adjacency list representation of the premise DAG."""
    # Nodes: -1 (question), 0..n_steps-1 (reasoning steps)
    adj = defaultdict(list)  # parent → children
    in_edges = defaultdict(list)  # child → parents
    
    for step_idx, premise_list in premises.items():
        for premise_idx in premise_list:
            adj[premise_idx].append(step_idx)
            in_edges[step_idx].append(premise_idx)
    
    return {"adj": dict(adj), "in_edges": dict(in_edges)}


def compute_dag_metrics(n_steps: int, dag: dict) -> dict:
    """Compute structural metrics for the premise DAG."""
    adj = dag["adj"]
    in_edges = dag["in_edges"]
    
    # Out-degree: how many steps depend on each step
    out_degrees = {}
    for i in range(-1, n_steps):
        out_degrees[i] = len(adj.get(i, []))
    
    # In-degree: how many premises each step has
    in_degrees = {}
    for i in range(n_steps):
        in_degrees[i] = len(in_edges.get(i, []))
    
    # Betweenness-like centrality: count paths through each node
    # (simplified — count descendants)
    descendants = {}
    def count_descendants(node):
        if node in descendants:
            return descendants[node]
        children = adj.get(node, [])
        count = len(children)
        for child in children:
            count += count_descendants(child)
        descendants[node] = count
        return count
    
    for i in range(-1, n_steps):
        count_descendants(i)
    
    # Load-bearing score: out_degree * descendants (how "important" this node is)
    load_bearing = {}
    for i in range(-1, n_steps):
        load_bearing[i] = out_degrees.get(i, 0) * (1 + descendants.get(i, 0))
    
    # DAG depth: longest path from question to any leaf
    depth_cache = {}
    def dag_depth(node):
        if node in depth_cache:
            return depth_cache[node]
        children = adj.get(node, [])
        if not children:
            depth_cache[node] = 0
            return 0
        d = 1 + max(dag_depth(c) for c in children)
        depth_cache[node] = d
        return d
    
    max_depth = dag_depth(-1) if -1 in adj else 0
    
    # DAG width: max number of nodes at any depth level
    levels = defaultdict(list)
    level_cache = {}
    def assign_level(node, level):
        if node in level_cache:
            return
        level_cache[node] = level
        levels[level].append(node)
        for child in adj.get(node, []):
            assign_level(child, level + 1)
    assign_level(-1, 0)
    max_width = max(len(v) for v in levels.values()) if levels else 1
    
    # Linearity score: how linear vs branching is the DAG
    # 1.0 = perfectly linear (each step depends on exactly the previous one)
    # Lower = more branching
    linear_edges = sum(1 for i in range(1, n_steps)
                       if in_edges.get(i, []) == [i-1])
    linearity = linear_edges / max(n_steps - 1, 1)
    
    # Most load-bearing step (excluding question)
    step_load = {k: v for k, v in load_bearing.items() if k >= 0}
    most_load_bearing = max(step_load, key=step_load.get) if step_load else 0
    
    return {
        "n_steps": n_steps,
        "max_depth": max_depth,
        "max_width": max_width,
        "linearity": round(linearity, 3),
        "out_degrees": out_degrees,
        "in_degrees": in_degrees,
        "load_bearing": load_bearing,
        "most_load_bearing_step": most_load_bearing,
        "most_load_bearing_score": step_load.get(most_load_bearing, 0),
        "avg_in_degree": round(statistics.mean(in_degrees.values()), 2) if in_degrees else 0,
        "avg_out_degree": round(statistics.mean(
            [v for k, v in out_degrees.items() if k >= 0]), 2) if out_degrees else 0,
    }


# ─────────────────────────────────────────────────────────────────
# 4. FAITHFULNESS ANALYSIS: CORRELATE DAG WITH FAITHFULNESS
# ─────────────────────────────────────────────────────────────────

def compute_step_removal_impact(trace: dict) -> dict:
    """
    Compute how much each step's removal would change the answer distribution.
    Uses the intermediate_answer_probabilities from FINE-CoT.
    
    Returns: dict mapping step_index → KL-like divergence (impact score)
    """
    probs = trace.get("intermediate_probs", [])
    if len(probs) < 2:
        return {}
    
    impacts = {}
    for i in range(1, len(probs)):
        # Impact of step i = change in max probability from step i-1 to step i
        prev_probs = probs[i - 1]
        curr_probs = probs[i]
        
        if not prev_probs or not curr_probs:
            continue
        
        # Jensen-Shannon-like divergence (simplified)
        total_shift = 0
        for key in set(list(prev_probs.keys()) + list(curr_probs.keys())):
            p = prev_probs.get(key, 0)
            q = curr_probs.get(key, 0)
            total_shift += abs(p - q)
        
        impacts[i - 1] = round(total_shift, 6)  # step index (0-indexed)
    
    return impacts


def analyze_trace(trace: dict) -> dict:
    """Full analysis pipeline for a single trace."""
    steps = trace["steps"]
    n_steps = len(steps)
    
    # Extract premises
    premises = extract_premises_heuristic(steps)
    
    # Build DAG
    dag = build_dag(n_steps, premises)
    
    # Compute metrics
    metrics = compute_dag_metrics(n_steps, dag)
    
    # Compute step removal impact
    impacts = compute_step_removal_impact(trace)
    
    # Key insight: does the most load-bearing step have the most impact?
    if impacts and metrics["most_load_bearing_step"] in impacts:
        mlb_step = metrics["most_load_bearing_step"]
        mlb_impact = impacts.get(mlb_step, 0)
        max_impact = max(impacts.values()) if impacts else 0
        avg_impact = statistics.mean(impacts.values()) if impacts else 0
    else:
        mlb_step = metrics["most_load_bearing_step"]
        mlb_impact = 0
        max_impact = 0
        avg_impact = 0
    
    return {
        "file": trace["file"],
        "question": trace["question"][:100],
        "label": trace["label"],
        "final_answer": trace["final_answer"],
        "correct": trace["final_answer"] == trace["label"],
        "soft_faithfulness": trace["soft_faithfulness"],
        "hard_faithfulness": trace["hard_faithfulness"],
        "n_steps": n_steps,
        "premises": premises,
        "dag_linearity": metrics["linearity"],
        "dag_depth": metrics["max_depth"],
        "dag_width": metrics["max_width"],
        "most_load_bearing_step": mlb_step,
        "load_bearing_score": metrics["most_load_bearing_score"],
        "avg_in_degree": metrics["avg_in_degree"],
        "step_impacts": impacts,
        "mlb_impact": mlb_impact,
        "max_impact": max_impact,
        "avg_impact": avg_impact,
    }


# ─────────────────────────────────────────────────────────────────
# 5. MAIN: RUN ANALYSIS
# ─────────────────────────────────────────────────────────────────

def print_dag_ascii(n_steps, premises):
    """Print a simple ASCII representation of the premise DAG."""
    print("    Question (Q)")
    for i in range(n_steps):
        prem_str = ", ".join(
            f"Q" if p == -1 else f"S{p+1}" for p in premises.get(i, [])
        )
        arrow = f"  ← [{prem_str}]" if prem_str else ""
        print(f"    Step {i+1}{arrow}")


def main():
    base_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "upstream", "FaithCoT-BENCH", "faithcot_data", "faithcot"
    )
    
    print("=" * 70)
    print("Premise DAG ↔ Faithfulness Analysis")
    print("=" * 70)
    
    # Analyze both domains where unfaithfulness is highest
    results_by_domain = {}
    
    for domain in ["truthfulqa", "logiqa"]:
        for model in ["llama-3.1-8b-instruct", "Qwen2.5-7B-Instruct"]:
            model_path = os.path.join(base_path, domain, model)
            if not os.path.exists(model_path):
                continue
            
            key = f"{domain}/{model}"
            print(f"\n{'─' * 70}")
            print(f"  Domain: {domain.upper()} | Model: {model}")
            print(f"{'─' * 70}")
            
            traces = load_faithcot_traces(domain, model, base_path)
            print(f"  Loaded {len(traces)} traces")
            
            analyses = []
            for trace in traces:
                if trace["soft_faithfulness"] is not None:
                    analyses.append(analyze_trace(trace))
            
            if not analyses:
                continue
            
            # ── Aggregate Statistics ──
            faithful = [a for a in analyses if a["soft_faithfulness"] >= 0.5]
            unfaithful = [a for a in analyses if a["soft_faithfulness"] < 0.5]
            
            print(f"\n  Faithful traces: {len(faithful)}")
            print(f"  Unfaithful traces: {len(unfaithful)}")
            
            # ── KEY FINDING: DAG structure vs faithfulness ──
            if faithful and unfaithful:
                f_linearity = statistics.mean(a["dag_linearity"] for a in faithful)
                u_linearity = statistics.mean(a["dag_linearity"] for a in unfaithful)
                f_depth = statistics.mean(a["dag_depth"] for a in faithful)
                u_depth = statistics.mean(a["dag_depth"] for a in unfaithful)
                f_width = statistics.mean(a["dag_width"] for a in faithful)
                u_width = statistics.mean(a["dag_width"] for a in unfaithful)
                f_indeg = statistics.mean(a["avg_in_degree"] for a in faithful)
                u_indeg = statistics.mean(a["avg_in_degree"] for a in unfaithful)
                f_impact = statistics.mean(a["avg_impact"] for a in faithful if a["avg_impact"] > 0)  if any(a["avg_impact"] > 0 for a in faithful) else 0
                u_impact = statistics.mean(a["avg_impact"] for a in unfaithful if a["avg_impact"] > 0) if any(a["avg_impact"] > 0 for a in unfaithful) else 0
                f_lb = statistics.mean(a["load_bearing_score"] for a in faithful)
                u_lb = statistics.mean(a["load_bearing_score"] for a in unfaithful)
                
                print(f"\n  ┌─────────────────────────────┬───────────┬─────────────┐")
                print(f"  │ Metric                      │ Faithful  │ Unfaithful  │")
                print(f"  ├─────────────────────────────┼───────────┼─────────────┤")
                print(f"  │ DAG Linearity (0-1)         │ {f_linearity:>8.3f}  │ {u_linearity:>10.3f}  │")
                print(f"  │ DAG Depth                   │ {f_depth:>8.1f}  │ {u_depth:>10.1f}  │")
                print(f"  │ DAG Width                   │ {f_width:>8.1f}  │ {u_width:>10.1f}  │")
                print(f"  │ Avg In-Degree               │ {f_indeg:>8.2f}  │ {u_indeg:>10.2f}  │")
                print(f"  │ Load-Bearing Score           │ {f_lb:>8.1f}  │ {u_lb:>10.1f}  │")
                print(f"  │ Avg Step Impact              │ {f_impact:>8.4f}  │ {u_impact:>10.4f}  │")
                print(f"  └─────────────────────────────┴───────────┴─────────────┘")
            
            # ── Show example DAGs ──
            # Show one faithful and one unfaithful trace
            if faithful:
                ex = faithful[0]
                print(f"\n  📗 Example FAITHFUL trace (soft_faith={ex['soft_faithfulness']:.3f}):")
                print(f"     Q: {ex['question']}...")
                print_dag_ascii(ex["n_steps"], ex["premises"])
                
            if unfaithful:
                ex = unfaithful[0]
                print(f"\n  📕 Example UNFAITHFUL trace (soft_faith={ex['soft_faithfulness']:.3f}):")
                print(f"     Q: {ex['question']}...")
                print_dag_ascii(ex["n_steps"], ex["premises"])
            
            results_by_domain[key] = {
                "n_traces": len(analyses),
                "n_faithful": len(faithful),
                "n_unfaithful": len(unfaithful),
                "analyses": analyses,
            }
    
    # ── CORRELATION ANALYSIS ──
    print(f"\n{'=' * 70}")
    print("CORRELATION: DAG Structure ↔ Faithfulness Score")
    print(f"{'=' * 70}")
    
    all_analyses = []
    for v in results_by_domain.values():
        all_analyses.extend(v["analyses"])
    
    if all_analyses:
        # Compute Spearman-like rank correlation (simplified)
        # Between linearity and faithfulness
        pairs = [(a["dag_linearity"], a["soft_faithfulness"]) 
                 for a in all_analyses if a["soft_faithfulness"] is not None]
        
        if pairs:
            n = len(pairs)
            x_ranked = sorted(range(n), key=lambda i: pairs[i][0])
            y_ranked = sorted(range(n), key=lambda i: pairs[i][1])
            x_ranks = [0] * n
            y_ranks = [0] * n
            for rank, idx in enumerate(x_ranked):
                x_ranks[idx] = rank
            for rank, idx in enumerate(y_ranked):
                y_ranks[idx] = rank
            
            d_sq = sum((x_ranks[i] - y_ranks[i]) ** 2 for i in range(n))
            rho = 1 - (6 * d_sq) / (n * (n**2 - 1)) if n > 1 else 0
            
            print(f"\n  Spearman ρ (DAG linearity vs soft faithfulness): {rho:.4f}")
            print(f"  N = {n} traces across all domains/models")
            
            # Impact correlation
            impact_pairs = [(a["avg_impact"], a["soft_faithfulness"])
                           for a in all_analyses 
                           if a["soft_faithfulness"] is not None and a["avg_impact"] > 0]
            if impact_pairs:
                n2 = len(impact_pairs)
                x_ranked2 = sorted(range(n2), key=lambda i: impact_pairs[i][0])
                y_ranked2 = sorted(range(n2), key=lambda i: impact_pairs[i][1])
                x_ranks2 = [0] * n2
                y_ranks2 = [0] * n2
                for rank, idx in enumerate(x_ranked2):
                    x_ranks2[idx] = rank
                for rank, idx in enumerate(y_ranked2):
                    y_ranks2[idx] = rank
                d_sq2 = sum((x_ranks2[i] - y_ranks2[i]) ** 2 for i in range(n2))
                rho2 = 1 - (6 * d_sq2) / (n2 * (n2**2 - 1)) if n2 > 1 else 0
                
                print(f"  Spearman ρ (step impact vs soft faithfulness): {rho2:.4f}")
                print(f"  N = {n2} traces with impact data")
    
    # ── SAVE FULL RESULTS ──
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "src", "poc_results.json"
    )
    
    # Serialize results
    serializable = {}
    for k, v in results_by_domain.items():
        serializable[k] = {
            "n_traces": v["n_traces"],
            "n_faithful": v["n_faithful"], 
            "n_unfaithful": v["n_unfaithful"],
            "analyses": [{
                "file": a["file"],
                "soft_faithfulness": a["soft_faithfulness"],
                "hard_faithfulness": a["hard_faithfulness"],
                "correct": a["correct"],
                "n_steps": a["n_steps"],
                "dag_linearity": a["dag_linearity"],
                "dag_depth": a["dag_depth"],
                "dag_width": a["dag_width"],
                "most_load_bearing_step": a["most_load_bearing_step"],
                "load_bearing_score": a["load_bearing_score"],
                "avg_impact": a["avg_impact"],
                "mlb_impact": a["mlb_impact"],
            } for a in v["analyses"]]
        }
    
    with open(output_path, "w") as f:
        json.dump(serializable, f, indent=2)
    print(f"\n  Full results saved to: {output_path}")
    
    print(f"\n{'=' * 70}")
    print("PoC complete. Premise DAGs constructed for")
    print(f"{len(all_analyses)} traces across TruthfulQA + LogiQA.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
