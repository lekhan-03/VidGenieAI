import edge_tts
import streamlit as st
import asyncio
import os
from base64 import b64encode
from utility.script.script_generator import generate_script
from utility.audio.audio_generator import generate_audio
from utility.captions.timed_captions_generator import generate_timed_captions
from utility.video.background_video_generator import generate_video_url
from utility.render.render_engine import get_output_media
from utility.video.video_search_query_generator import getVideoSearchQueriesTimed, merge_empty_intervals
from PIL import Image

def display_video(video_path):
    try:
        with open(video_path, "rb") as video_file:
            video_bytes = video_file.read()
            video_url = f"data:video/mp4;base64,{b64encode(video_bytes).decode()}"
            st.video(video_url)
    except FileNotFoundError:
        st.error("Video file not found. Please try again.")

async def generate_video_from_topic(topic, voice):
    # Force the environment variable to match your selection so backend config managers catch it
    os.environ["EDGETTS_VOICE"] = voice
    
    SAMPLE_FILE_NAME = "audio_tts.wav"
    VIDEO_SERVER = "pexel"

    response = generate_script(topic)
    if not response:
        st.error("Failed to generate script. Please try again.")
        return
    st.success("Script generated successfully!")
    st.write(f"**Generated Script:** {response}")

    st.info(f"Generating audio using voice: {voice}")
    # Pass voice to our updated fail-safe generator
    await generate_audio(response, SAMPLE_FILE_NAME, voice=voice)

    timed_captions = generate_timed_captions(SAMPLE_FILE_NAME)
    search_terms = getVideoSearchQueriesTimed(response, timed_captions)
    
    if search_terms:
        background_video_urls = generate_video_url(search_terms, VIDEO_SERVER)
        background_video_urls = merge_empty_intervals(background_video_urls)
    else:
        st.error("Failed to generate background video. Please try again.")
        return

    if background_video_urls:
        output_video = get_output_media(SAMPLE_FILE_NAME, timed_captions, background_video_urls, VIDEO_SERVER)
        st.success("Video rendered successfully!")
        st.write("**Final Video:**")
        display_video(output_video)
    else:
        st.error("Failed to render video. Please try again.")

with st.sidebar:
    st.header("About")
    st.write("**Script2Scene**: AI generates a script, converts it to speech, adds timed captions, fetches background footage, and renders the final video.")

col1, col2 = st.columns([1, 4])  
with col1:
    try:
        logo = Image.open("kiran1.jpg")
        st.image(logo, use_container_width=True) 
    except FileNotFoundError:
        pass
with col2:
    st.markdown("<h1 style='color: #4CAF50; margin: 0;'>Script2Scene</h1>", unsafe_allow_html=True)

topic = st.text_input("Enter a topic:", placeholder="e.g., Space Mysteries, Ancient Rome, AI Future")

st.write("### 🎙️ Select Voice Settings:")
col_v1, col_v2 = st.columns(2)
with col_v1:
    accent = st.selectbox("Select Accent / Region:", ("American", "British", "Indian", "Australian"))
with col_v2:
    gender = st.radio("Select Gender:", ("Male", "Female"), horizontal=True)

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
st.caption(f"**Selected Voice Model:** `{voice}`")

if st.button("Generate Video"):
    if topic.strip():
        st.info("Processing your request. Please wait...")
        asyncio.run(generate_video_from_topic(topic, voice))
    else:
        st.error("Please enter a valid topic!")
