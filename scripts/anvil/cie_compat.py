"""Compatibility layer between CIE-Scorer (July 2026) and current circuit-tracer.

Why this exists: CIE-Scorer's circuit.py calls the Graph API as it stood before circuit-tracer's
"Attribution Targets Encapsulation" commit (43933d1, 2026-02-23), but needs the CRV top-k
transcoders added on 2026-04-17 (4b1b491). No upstream commit has both, so the authors used a
private build (their README mentions "bundled circuit-tracer archives" that are not released).
Rather than edit the authors' file, translate their calls:

  Graph(logit_tokens=<tensor of vocab ids>, ...)  ->  Graph(logit_targets=[LogitTarget(...)], ...)
  Graph(scan=...)                                  ->  Graph(scan_name=...)
  model.scan                                       ->  model.scan_name
  graph.logit_tokens (read back in graph_features) ->  tensor of vocab_idx from logit_targets

The translation is lossless: LogitTarget carries (token_str, vocab_idx); circuit-tracer's own
from_pt() builds LogitTarget with token_str="" for legacy graphs, and we do the same. Nothing in
CIE-Scorer reads token_str. Import before cie_scorer.circuit is used.
"""
import logging
import torch
from circuit_tracer import graph as _G
from circuit_tracer.attribution.targets import LogitTarget
from circuit_tracer.replacement_model import replacement_model_transformerlens as _RT

if not hasattr(_RT.TransformerLensReplacementModel, "scan"):
    _RT.TransformerLensReplacementModel.scan = property(lambda self: getattr(self, "scan_name", None))

_orig_init = _G.Graph.__init__
def _init(self, *args, **kwargs):
    if "scan" in kwargs and "scan_name" not in kwargs:
        kwargs["scan_name"] = kwargs.pop("scan")
    if "logit_tokens" in kwargs and "logit_targets" not in kwargs:
        lt = kwargs.pop("logit_tokens")
        ids = lt.tolist() if isinstance(lt, torch.Tensor) else list(lt)
        kwargs["logit_targets"] = [LogitTarget(token_str="", vocab_idx=int(i)) for i in ids]
    return _orig_init(self, *args, **kwargs)
if not getattr(_G.Graph, "_cie_compat", False):
    _G.Graph.__init__ = _init
    _G.Graph._cie_compat = True

if not hasattr(_G.Graph, "logit_tokens"):
    _G.Graph.logit_tokens = property(
        lambda self: torch.tensor([t.vocab_idx for t in self.logit_targets], dtype=torch.long))

logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
for noisy in ("transformers", "huggingface_hub", "urllib3", "filelock"):
    logging.getLogger(noisy).setLevel(logging.WARNING)
