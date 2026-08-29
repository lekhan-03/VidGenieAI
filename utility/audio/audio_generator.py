import edge_tts
import os

# Using *args and **kwargs makes this bulletproof whether app.py passes 2 or 3 arguments!
async def generate_audio(text, output_filename, *args, **kwargs):
    # Try to grab the voice from kwargs, args, or fallback to the .env file
    voice = kwargs.get('voice')
    if not voice and args:
        voice = args[0]
    if not voice:
        voice = os.environ.get("EDGETTS_VOICE", "en-US-GuyNeural")
        
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_filename)
