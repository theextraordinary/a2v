from functools import lru_cache
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
