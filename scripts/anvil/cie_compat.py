"""Version shim between CIE-Scorer (written against circuit-tracer mid-2026) and current circuit-tracer.

Upstream renamed the transcoder identifier from `scan` to `scan_name` on both ReplacementModel and
Graph (a metadata label used only for uploads; it plays no role in attribution). CIE-Scorer's
circuit.py still reads `model.scan` and passes `Graph(..., scan=...)`. Rather than edit the authors'
file, expose the old names as aliases of the new ones. Import before cie_scorer.circuit is used.
"""
import logging
from circuit_tracer import graph as _G
from circuit_tracer.replacement_model import replacement_model_transformerlens as _RT

# model.scan -> model.scan_name
if not hasattr(_RT.TransformerLensReplacementModel, "scan"):
    _RT.TransformerLensReplacementModel.scan = property(lambda self: getattr(self, "scan_name", None))

# Graph(scan=...) -> Graph(scan_name=...)
_orig_init = _G.Graph.__init__
def _init(self, *args, **kwargs):
    if "scan" in kwargs and "scan_name" not in kwargs:
        kwargs["scan_name"] = kwargs.pop("scan")
    return _orig_init(self, *args, **kwargs)
if not getattr(_G.Graph, "_cie_compat", False):
    _G.Graph.__init__ = _init
    _G.Graph._cie_compat = True

# the authors' code logs its phase timings at INFO; surface them so timing comes from their own lines
logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
for noisy in ("transformers", "huggingface_hub", "urllib3", "filelock"):
    logging.getLogger(noisy).setLevel(logging.WARNING)
