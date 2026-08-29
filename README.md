# 🎬 VidGenie — Where Your Ideas Become Videos ✨

Turn a single topic into a fully-produced short video — script, voiceover, captions, and stock footage — all generated automatically and stitched together in one click.

Built on top of [Text-To-Video-AI](https://github.com/SamurAIGPT/Text-To-Video-AI), wrapped in an interactive Streamlit UI.

---

## 🚀 What It Does

Give it a topic like *"The Ocean"* or *"AI in 2026"*, and VidGenie will:

1. **Write a script** for the topic using an LLM (Groq)
2. **Generate a voiceover** from the script using Edge TTS
3. **Create timed captions** synced to the audio
4. **Fetch matching background footage** from Pexels based on the script's content
5. **Render the final video** — audio, captions, and clips combined into one output — right in your browser

No editing software. No manual voice recording. Just a topic and a click.

## 🖥️ Demo

| Step | What Happens |
|------|-------------|
| ✍️ Script Generation | AI writes a short-form video script from your topic |
| 🗣️ Voiceover | Edge TTS converts the script to natural speech (choose gender + accent) |
| 💬 Captions | Auto-generated, timed to the audio |
| 🎥 Footage | Relevant stock clips are pulled and sequenced automatically |
| 🎞️ Render | Everything is combined into a final downloadable video |

## 🧰 Tech Stack

| Component | Tool |
|---|---|
| UI | [Streamlit](https://streamlit.io/) |
| Script Generation | [Groq](https://groq.com/) (LLM API) |
| Text-to-Speech | [Edge TTS](https://github.com/rany2/edge-tts) |
| Speech-to-Text / Captions | Whisper |
| Background Footage | [Pexels API](https://www.pexels.com/api/) |
| Video Rendering | MoviePy |
| Tunneling (for Colab demos) | [pyngrok](https://pyngrok.readthedocs.io/) |

## ⚙️ Setup

### 1. Clone the repo

```bash
git clone https://github.com/SamurAIGPT/Text-To-Video-AI
cd Text-To-Video-AI
```

### 2. Install system & Python dependencies

```bash
apt update -y
apt install imagemagick -y
sed -i '/<policy domain="path" rights="none" pattern="@\*"/d' /etc/ImageMagick-6/policy.xml

pip install -r requirements.txt
pip install streamlit edge-tts pyngrok
```

> ImageMagick's default security policy blocks the kind of text/path rendering MoviePy needs for captions — the `sed` command above removes that restriction.

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
# --- AI Provider ---
LLM_PROVIDER=groq
GROQ_MODEL=openai/gpt-oss-120b
GROQ_API_KEY=your_groq_api_key_here

# --- Visuals ---
PEXELS_API_KEY=your_pexels_api_key_here
VIDEO_ORIENTATION=portrait

# --- Audio & Captions ---
STT_PROVIDER=whisper
TTS_PROVIDER=edgetts
EDGETTS_VOICE=en-US-GuyNeural

# --- Caption Styling ---
CAPTIONS_ENABLED=true
CAPTION_FONT_SIZE=100
CAPTION_FONT_COLOR=white
CAPTION_FONT_FACE=Arial-Bold
CAPTION_STROKE_WIDTH=3
CAPTION_STROKE_COLOR=black
CAPTION_POSITION=bottom_center

# --- Rendering Engine ---
RENDER_ENGINE=moviepy
```

Get your free API keys here:
- **Groq**: [console.groq.com](https://console.groq.com/)
- **Pexels**: [pexels.com/api](https://www.pexels.com/api/)

A template is included at `.env.example` — copy it and fill in your own keys instead of writing `.env` from scratch:

```bash
cp .env.example .env
```

> ⚠️ Never commit your `.env` file or push real API keys to GitHub — it should already be listed in `.gitignore`.

### Windows setup

If you're on Windows, see [`INSTALL_WINDOWS.md`](./INSTALL_WINDOWS.md) for OS-specific install steps (ImageMagick and some dependencies behave differently outside Linux/Colab).

### 4. Run the app

```bash
streamlit run app.py
```

**Running in Google Colab?** Since Colab doesn't expose local ports, tunnel it with ngrok:

```python
from pyngrok import ngrok

ngrok.set_auth_token("your_ngrok_authtoken")
!nohup streamlit run app.py &
public_url = ngrok.connect(8501)
print(f"Your Streamlit app is live at: {public_url}")
```

## 🎛️ Usage

1. Launch the app and enter a topic (e.g. *"Fruits"*, *"AI"*, *"Nature"*)
2. Pick a voice — gender (Male/Female) and accent (British/American)
3. Click **Generate Video**
4. Watch the pipeline run: script → audio → captions → footage → render
5. Preview and download your finished video

## 📁 Project Structure

```
Text-To-Video-AI/
├── app.py                          # Streamlit UI & orchestration
├── utility/
│   ├── script/script_generator.py         # LLM script generation
│   ├── audio/audio_generator.py           # Edge TTS voiceover
│   ├── captions/timed_captions_generator.py # Whisper-based caption timing
│   ├── video/background_video_generator.py  # Pexels footage search
│   ├── video/video_search_query_generator.py # Search term generation
│   └── render/render_engine.py            # Final video composition
├── Text_to_Video_example.ipynb      # Example notebook walkthrough
├── requirements.txt
├── .env.example                     # Template — copy to .env and fill in your keys
├── .env
└── INSTALL_WINDOWS.md                # Windows-specific setup instructions
```

## 🛠️ Troubleshooting

| Issue | Fix |
|---|---|
| `model_decommissioned` error from Groq | Your `GROQ_MODEL` is outdated — check [console.groq.com/docs/deprecations](https://console.groq.com/docs/deprecations) for the current recommended model |
| ImageMagick permission errors on captions | Re-run the `sed` policy fix in step 2 |
| Video file not found after render | Check that `PEXELS_API_KEY` is valid and hasn't hit its rate limit |

## 🙌 Credits

Built on top of the excellent [Text-To-Video-AI](https://github.com/SamurAIGPT/Text-To-Video-AI) by SamurAIGPT.

## 📄 License

This project is intended for educational and personal use. Check the upstream repo's license before commercial use.
