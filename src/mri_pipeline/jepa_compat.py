"""Load the pinned author's normal-attention path without requiring FlashAttention.

Only the unconditional import is replaced in memory. The upstream file stays
unchanged; model operations, parameter names and checkpoint loading are unchanged.
"""
from pathlib import Path
import hashlib
import types

AUTHOR_MODEL_SHA256 = '95101ab92ef4a67e0b51270b5eba435f40a364fd7abf08e4beed476d8b34da46'


def normal_attention_module(repo):
    path = Path(repo) / 'src/models/vision_transformer.py'
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != AUTHOR_MODEL_SHA256:
        raise ValueError('Brain-JEPA normal-attention compatibility requires the audited author file')
    source = raw.decode('utf-8')
    original = 'from flash_attn import flash_attn_qkvpacked_func'
    if source.count(original) != 1:
        raise ValueError('Unexpected FlashAttention import')
    replacement = ("def flash_attn_qkvpacked_func(*args, **kwargs):\n"
                   "    raise RuntimeError('FlashAttention disabled: select attn_mode=normal')")
    source = source.replace(original, replacement)
    module = types.ModuleType('brain_jepa_normal_attention')
    module.__file__ = str(path)
    exec(compile(source, str(path) + ':normal_attention_import_only', 'exec'), module.__dict__)
    return module
