from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / 'data'
INPUT_AUDIO = DATA_DIR / 'input_audio' / 'sample.wav'
OUTPUT_DIR = DATA_DIR / 'output'
CLEAN_AUDIO = OUTPUT_DIR / 'cleaned.wav'
OUTPUT_VIDEO = OUTPUT_DIR / 'final.mp4'

EDGE_URL = os.getenv('EDGE_URL', 'http://127.0.0.1:8000/process_audio')
CLOUD_URL = os.getenv('CLOUD_URL', 'http://127.0.0.1:9000/generate_timeline')


def load_env():
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    return {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
        'GEMMA_API_KEY': os.getenv('GEMMA_API_KEY', ''),
        'EDGE_URL': EDGE_URL,
        'CLOUD_URL': CLOUD_URL,
        'GEMMA_MODEL': os.getenv('GEMMA_MODEL', 'google/gemma-2-9b-it'),
        'GEMMA_API_URL': os.getenv('GEMMA_API_URL', 'https://api-inference.huggingface.co/models'),
    }
