import whisper

def generate_timed_captions(audio_filename, model_size="base"):
    """
    Generates word-level timestamps using standard OpenAI Whisper 
    formatted as [((start, end), word), ...] to match video query expectations.
    """
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_filename, word_timestamps=True)
    
    captions_timed = []
    for segment in result.get("segments", []):
        for word in segment.get("words", []):
            start = word["start"]
            end = word["end"]
            w_text = word["word"].strip()
            captions_timed.append(((start, end), w_text))
            
    return captions_timed