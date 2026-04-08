from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / 'data'
INPUT_AUDIO = DATA_DIR / 'input_audio' / 'sample.wav'
OUTPUT_DIR = DATA_DIR / 'output'
CLEAN_AUDIO = OUTPUT_DIR / 'cleaned.wav'
OUTPUT_VIDEO = OUTPUT_DIR / 'final.mp4'


def load_env():
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    return {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
        'GEMMA_API_KEY': os.getenv('GEMMA_API_KEY', ''),
    }
