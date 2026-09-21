"""transformers 4.57.x (required by current circuit-tracer) queries the Hub from
PreTrainedTokenizerBase._patch_mistral_regex without honouring HF_HUB_OFFLINE, so any tokenizer load
fails on an offline compute node. The helper only rewrites a regex for Mistral-family tokenizers and
is irrelevant to Llama-3.1, so it is replaced by an identity function. Import before any tokenizer load."""
import transformers.tokenization_utils_base as _TUB
if "_patch_mistral_regex" in _TUB.PreTrainedTokenizerBase.__dict__:
    def _identity(cls, tokenizer, *args, **kwargs):
        return tokenizer
    _TUB.PreTrainedTokenizerBase._patch_mistral_regex = classmethod(_identity)
