import whisper

def generate_timed_captions(audio_filename):
    """
    Generates word-level timestamps using standard OpenAI Whisper 
    to prevent hook compatibility errors on cloud environments.
    """
    model = whisper.load_model("base")
    result = model.transcribe(audio_filename, word_timestamps=True)
    
    segments = []
    for segment in result.get("segments", []):
        for word in segment.get("words", []):
            segments.append({
                "word": word["word"].strip(),
                "start": word["start"],
                "end": word["end"]
            })
            
    return segments