from pathlib import Path
import os
from functools import lru_cache

# Force HF cache paths early
_base_dir = Path(__file__).resolve().parents[1]
_cache_dir = _base_dir / '.hf_cache'
_cache_dir.mkdir(parents=True, exist_ok=True)
os.environ['HF_HOME'] = str(_cache_dir)
os.environ['HF_HUB_CACHE'] = str(_cache_dir)
os.environ['TRANSFORMERS_CACHE'] = str(_cache_dir)

from transformers import pipeline

MODEL_ID = 'j-hartmann/emotion-english-distilroberta-base'
LABEL_MAP = {
    'joy': 'motivational',
    'sadness': 'sad',
    'anger': 'energetic',
    'neutral': 'calm',
}


@lru_cache(maxsize=1)
def _get_classifier():
    return pipeline('text-classification', model=MODEL_ID, top_k=1)


def classify_emotion(text):
    if not text:
        return 'calm'
    clf = _get_classifier()
    result = clf(text)
    # result may be list of dicts or list[list[dict]] depending on pipeline
    if isinstance(result, list) and result and isinstance(result[0], list):
        result = result[0]
    label = result[0]['label'].lower()
    return LABEL_MAP.get(label, 'calm')
