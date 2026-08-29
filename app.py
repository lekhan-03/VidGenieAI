import edge_tts
import streamlit as st
import asyncio
import os
from base64 import b64encode
from PIL import Image

from utility.script.script_generator import generate_script
from utility.audio.audio_generator import generate_audio
from utility.captions.timed_captions_generator import generate_timed_captions
from utility.video.background_video_generator import generate_video_url
from utility.render.render_engine import get_output_media
from utility.video.video_search_query_generator import getVideoSearchQueriesTimed, merge_empty_intervals

# 1. Page Configuration (Must be the first Streamlit command)
st.set_page_config(page_title="VidGenie | AI Video Creator", page_icon="🧞‍♂️", layout="centered")

# 2. Custom CSS for Modern UI
st.markdown("""
<style>
    /* Gradient Title */
    .vidgenie-title {
        background: -webkit-linear-gradient(45deg, #FF6B6B, #4CAF50, #2196F3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5em;
        font-weight: 900;
        margin-bottom: 0px;
        padding-bottom: 0px;
    }
    .vidgenie-subtitle {
        color: #888888;
        font-size: 1.2em;
        font-weight: 400;
        margin-top: -10px;
        margin-bottom: 30px;
    }
    /* Modern Button Styling */
    .stButton>button {
        width: 100%;
        border-radius: 30px;
        background: linear-gradient(90deg, #4CAF50 0%, #2E7D32 100%);
        color: white;
        font-weight: 700;
        font-size: 1.1em;
        border: none;
        padding: 12px 24px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0px 8px 15px rgba(76, 175, 80, 0.3);
    }
    /* Clean up input boxes */
    .stTextInput>div>div>input {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Function to display video
def display_video(video_path):
    try:
        with open(video_path, "rb") as video_file:
            video_bytes = video_file.read()
            video_url = f"data:video/mp4;base64,{b64encode(video_bytes).decode()}"
            st.video(video_url)
    except FileNotFoundError:
        st.error("🚨 Video file not found. Please try again.")

# Main Video Generation Function
async def generate_video_from_topic(topic, voice):
    os.environ["EDGETTS_VOICE"] = voice
    SAMPLE_FILE_NAME = "audio_tts.wav"
    VIDEO_SERVER = "pexel"

    with st.status("🧞‍♂️ VidGenie is working its magic...", expanded=True) as status:
        st.write("📝 Writing an engaging script...")
        response = generate_script(topic)
        if not response:
            status.update(label="Script generation failed.", state="error")
            st.error("Failed to generate script. Please try again.")
            return

        st.write(f"🎙️ Generating voiceover ({voice})...")
        await generate_audio(response, SAMPLE_FILE_NAME, voice=voice)

        st.write("⏱️ Syncing automated captions...")
        timed_captions = generate_timed_captions(SAMPLE_FILE_NAME)
        
        st.write("🎥 Hunting for perfect background footage...")
        search_terms = getVideoSearchQueriesTimed(response, timed_captions)
        
        if search_terms:
            background_video_urls = generate_video_url(search_terms, VIDEO_SERVER)
            background_video_urls = merge_empty_intervals(background_video_urls)
        else:
            status.update(label="Footage search failed.", state="error")
            st.error("Failed to generate background video. Please try again.")
            return

        st.write("🎬 Rendering final masterpiece...")
        if background_video_urls:
            output_video = get_output_media(SAMPLE_FILE_NAME, timed_captions, background_video_urls, VIDEO_SERVER)
            status.update(label="Video Complete!", state="complete", expanded=False)
            
            st.success("✨ Your video is ready!")
            with st.expander("📄 View Generated Script"):
                st.write(response)
            display_video(output_video)
        else:
            status.update(label="Rendering failed.", state="error")
            st.error("Failed to render video. Please try again.")

# --- UI LAYOUT ---

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3175/3175218.png", width=80) # Generic magic lamp icon
    st.title("About VidGenie")
    st.write("Transform simple text prompts into fully produced, captioned short-form videos in minutes.")
    st.divider()
    st.markdown("### ⚙️ How it works:")
    st.markdown("1. **AI Scripting** (Groq)\n2. **Voiceover** (Edge-TTS)\n3. **Captions** (Whisper)\n4. **B-Roll** (Pexels)\n5. **Stitching** (MoviePy)")

# Main Header
col1, col2 = st.columns([1, 5])
with col1:
    try:
        logo = Image.open("kiran1.jpg")
        st.image(logo, use_container_width=True)
    except FileNotFoundError:
        st.write("🧞‍♂️") # Fallback emoji if logo is missing
with col2:
    st.markdown('<p class="vidgenie-title">VidGenie</p>', unsafe_allow_html=True)
    st.markdown('<p class="vidgenie-subtitle">Summon engaging videos from thin air.</p>', unsafe_allow_html=True)

# Input Section
st.markdown("### 🪄 What should the video be about?")
topic = st.text_input("Topic", label_visibility="collapsed", placeholder="e.g., The Mysteries of the Deep Ocean, Stoic Philosophy, Top 3 Supercars...")

st.divider()

# Voice Selection
st.markdown("### 🗣️ Choose Your Narrator")
col_v1, col_v2 = st.columns(2)
with col_v1:
    accent = st.selectbox("Region / Accent:", ("American", "British", "Indian", "Australian"))
with col_v2:
    gender = st.radio("Gender:", ("Male", "Female"), horizontal=True)

voice_mapping = {
    ("Male", "American"): "en-US-GuyNeural",
    ("Female", "American"): "en-US-JennyNeural",
    ("Male", "British"): "en-GB-RyanNeural",
    ("Female", "British"): "en-GB-SoniaNeural",
    ("Male", "Indian"): "en-IN-PrabhatNeural",
    ("Female", "Indian"): "en-IN-NeerjaNeural",
    ("Male", "Australian"): "en-AU-WilliamNeural",
    ("Female", "Australian"): "en-AU-NatashaNeural",
}
voice = voice_mapping.get((gender, accent), "en-US-GuyNeural")

st.write("") # Spacer

# Generate Button
if st.button("✨ Generate Video ✨"):
    if topic.strip():
        asyncio.run(generate_video_from_topic(topic, voice))
    else:
        st.warning("⚠️ Please enter a topic first to summon your video!")