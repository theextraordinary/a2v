import whisper


def transcribe_audio(audio_path, model_size='base'):
    model = whisper.load_model(model_size)
    result = model.transcribe(str(audio_path), fp16=False)
    segments = []
    for seg in result.get('segments', []):
        segments.append({
            'start': float(seg['start']),
            'end': float(seg['end']),
            'text': seg['text'].strip(),
        })
    return segments
