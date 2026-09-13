"""Strict cached-data IO and question-clustered statistics for the repair analyses."""
from __future__ import annotations
import hashlib
import json
import platform
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import scipy
from scipy.stats import rankdata


def read_json(path):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError(f'Duplicate JSON key: {key} in {path}')
            out[key] = value
        return out
    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def indexed(rows, key):
    out = {}
    for row in rows:
        if row[key] in out:
            raise ValueError(f'Duplicate {key}: {row[key]}')
        out[row[key]] = row
    return out


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write('\n')


def number(value):
    return float(value) if np.isfinite(value) else None


def interval(value, draws, name):
    valid = np.asarray(draws, dtype=float)
    valid = valid[np.isfinite(valid)]
    bounds = np.percentile(valid, [2.5, 97.5]).tolist() if len(valid) >= 2 else None
    complete = len(valid) == len(draws)
    return {name: number(value), 'ci95': bounds if complete else None,
            'bootstrap_valid': len(valid), 'bootstrap_attempted': len(draws),
            'interval_status': 'all resamples defined' if complete else 'CI withheld: undefined resamples',
            'conditional_valid_resample_percentiles': None if complete else bounds}


def aucs(y, scores):
    """Columns of scores all point towards y=1; ties get half credit."""
    y = np.asarray(y)
    scores = np.asarray(scores, dtype=float)
    if scores.ndim == 1:
        scores = scores[:, None]
    if len(y) != len(scores) or not np.isin(y, [0, 1]).all() or not np.isfinite(scores).all():
        raise ValueError('AUROC requires aligned binary labels and finite scores')
    n1, n0 = int(y.sum()), int(len(y) - y.sum())
    if not n1 or not n0:
        return np.full(scores.shape[1], np.nan)
    ranks = rankdata(scores, axis=0)
    return (ranks[y == 1].sum(axis=0) - n1 * (n1 + 1) / 2) / (n1 * n0)


def rhos(y, scores):
    scores = np.asarray(scores, dtype=float)
    if scores.ndim == 1:
        scores = scores[:, None]
    if len(y) < 3:
        return np.full(scores.shape[1], np.nan)
    xr, yr = rankdata(scores, axis=0), rankdata(y)
    xr -= xr.mean(axis=0)
    yr -= yr.mean()
    denom = np.sqrt((xr * xr).sum(axis=0) * (yr * yr).sum())
    with np.errstate(divide='ignore', invalid='ignore'):
        return (xr * yr[:, None]).sum(axis=0) / denom


def cluster_draws(keys, repeats, seed):
    """Fixed attempts; undefined resamples are reported, never silently retried."""
    if repeats < 2:
        raise ValueError('At least two bootstrap draws are required')
    groups = defaultdict(list)
    for i, key in enumerate(keys):
        groups[key].append(i)
    groups = [np.asarray(groups[k], dtype=int) for k in sorted(groups)]
    if not groups:
        raise ValueError('Empty population')
    rng = np.random.default_rng(seed)
    for _ in range(repeats):
        yield np.concatenate([groups[i] for i in rng.integers(len(groups), size=len(groups))])


def manifest(inputs, scripts, protocol, seed, repeats):
    sources = {str(k): sha256(v) for k, v in inputs.items()}
    code = {Path(p).name: sha256(p) for p in scripts}
    identity = dict(inputs=sources, code=code, protocol=protocol, seed=seed, bootstrap=repeats)
    run_hash = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return dict(identity, run_sha256=run_hash,
                created_utc=datetime.now(timezone.utc).isoformat(),
                versions={'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__},
                status='complete cached-data reanalysis; no new model inference')
