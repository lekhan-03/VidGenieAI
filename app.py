import edge_tts
import streamlit as st
import asyncio
import os
import base64
from base64 import b64encode

from utility.script.script_generator import generate_script
from utility.audio.audio_generator import generate_audio
from utility.captions.timed_captions_generator import generate_timed_captions
from utility.video.background_video_generator import generate_video_url
from utility.render.render_engine import get_output_media
from utility.video.video_search_query_generator import getVideoSearchQueriesTimed, merge_empty_intervals
import os
import streamlit as st
import subprocess

# --- Cloud Deployment Fix: Generate .env from Streamlit Secrets ---
if not os.path.exists('.env'):
    try:
        with open('.env', 'w') as f:
            for key, value in st.secrets.items():
                f.write(f'{key}="{value}"\n')
    except Exception as e:
        pass
# ------------------------------------------------------------------




# --- Fix ImageMagick Security Policy for MoviePy TextClips ---
try:
    policy_path = "/etc/ImageMagick-7/policy.xml" # or /etc/ImageMagick/policy.xml
    if not os.path.exists(policy_path):
        # Try alternate path for Debian Trixie/Bullseye
        for p in ["/etc/ImageMagick-6/policy.xml", "/etc/ImageMagick-7/policy.xml"]:
            if os.path.exists(p):
                policy_path = p
                break
                
    if os.path.exists(policy_path):
        with open(policy_path, "r") as f:
            content = f.read()
        # Replace the read restriction for text files
        new_content = content.replace(
            'rights="none" pattern="@*"', 
            'rights="read|write" pattern="@*"'
        )
        if new_content != content:
            subprocess.run(["sudo", "sed", "-i", 's/rights="none" pattern="@*"/rights="read|write" pattern="@*"/g', policy_path], capture_output=True)
except Exception as e:
    print(f"Could not patch ImageMagick policy: {e}")
# 1. Page Configuration
st.set_page_config(page_title="VidGenie | AI Video Creator", page_icon="✨", layout="centered")

# 2. Premium Theme-Responsive CSS
st.markdown("""
<style>
    /* Base App Styling */
    .stApp {
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    /* Center the Hero Section */
    .hero-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding-top: 2rem;
        padding-bottom: 2rem;
        text-align: center;
    }
    
    /* Logo Styling */
    .hero-logo {
        width: 110px;
        height: 110px;
        border-radius: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        margin-bottom: 1rem;
        object-fit: cover;
    }

    /* Massive Elegant Gradient Title */
    .vidgenie-title {
        background: linear-gradient(135deg, #1E3A8A 0%, #43E97B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 4.5rem !important;
        font-weight: 900 !important;
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
        line-height: 1.1 !important;
        letter-spacing: -2px;
    }
    
    /* Larger Subtitle - Adapts to Theme */
    .vidgenie-subtitle {
        color: var(--text-color);
        opacity: 0.7;
        font-size: 1.3rem !important;
        font-weight: 400 !important;
        margin-top: 0.5rem !important;
        margin-bottom: 2rem !important;
    }

    /* Bigger, sleeker Input Text Area - Adapts to Theme */
    .stTextArea textarea {
        border-radius: 16px;
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border: 1px solid transparent;
        box-shadow: 0 4px 14px rgba(0,0,0,0.05);
        font-size: 1.25rem !important;
        padding: 1.5rem !important;
        transition: all 0.3s;
    }
    .stTextArea textarea:focus {
        border-color: #43E97B !important;
        box-shadow: 0 4px 20px rgba(67, 233, 123, 0.15) !important;
    }

    /* Massive, Elevated Generate Button */
    .stButton>button {
        width: 100%;
        border-radius: 16px;
        background: linear-gradient(135deg, #2B32B2 0%, #1488CC 100%);
        color: white !important;
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
        border: none;
        padding: 1rem 2rem !important;
        box-shadow: 0 8px 25px rgba(43, 50, 178, 0.25);
        transition: all 0.3s ease;
        margin-top: 20px;
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(43, 50, 178, 0.35);
    }
    
    /* Clean Sidebar Border */
    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.1);
    }
    
    /* Larger Inspiration Pills - Adapts to Theme */
    .prompt-pill {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 20px;
        padding: 8px 18px;
        font-size: 1rem;
        font-weight: 500;
        color: var(--text-color);
        display: inline-block;
        margin: 6px 6px 20px 0px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# Helper function to load local image as base64 for HTML
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return ""

def display_video(video_path):
    try:
        with open(video_path, "rb") as video_file:
            video_bytes = video_file.read()
            video_url = f"data:video/mp4;base64,{b64encode(video_bytes).decode()}"
            st.markdown("<br>", unsafe_allow_html=True)
            st.video(video_url)
    except FileNotFoundError:
        st.error("Video file not found.")

async def generate_video_from_topic(topic, voice):
    os.environ["EDGETTS_VOICE"] = voice
    SAMPLE_FILE_NAME = "audio_tts.wav"
    VIDEO_SERVER = "pexel"

    with st.status("🎬 Directing your video...", expanded=True) as status:
        st.write("📝 Drafting script...")
        response = generate_script(topic)
        if not response:
            status.update(label="Script generation failed.", state="error")
            return

        st.write("🎙️ Recording voiceover...")
        await generate_audio(response, SAMPLE_FILE_NAME, voice=voice)

        st.write("⏱️ Synchronizing subtitles...")
        timed_captions = generate_timed_captions(SAMPLE_FILE_NAME)
        
        st.write("🎥 Sourcing cinematic b-roll...")
        search_terms = getVideoSearchQueriesTimed(response, timed_captions)
        
        if search_terms:
            background_video_urls = generate_video_url(search_terms, VIDEO_SERVER)
            background_video_urls = merge_empty_intervals(background_video_urls)
        else:
            status.update(label="Footage search failed.", state="error")
            return

        st.write("🎞️ Rendering final composition...")
        if background_video_urls:
            output_video = get_output_media(SAMPLE_FILE_NAME, timed_captions, background_video_urls, VIDEO_SERVER)
            status.update(label="Video Complete!", state="complete", expanded=False)
            
            with st.expander("📄 Review Script"):
                st.write(response)
            display_video(output_video)
            st.balloons()
        else:
            status.update(label="Rendering failed.", state="error")

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🎙️ Narrator Settings")
    st.write("Tune the voice of your video.")
    accent = st.selectbox("Accent", ("American", "British", "Indian", "Australian"))
    gender = st.radio("Gender", ("Male", "Female"), horizontal=True)
    
    st.divider()
    st.markdown("### ⚙️ Engine")
    st.write("• **LLM:** Llama-3.3-70b\n• **Voice:** Edge-TTS\n• **Visuals:** Pexels HD\n• **Stitching:** MoviePy")

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

# --- MAIN LAYOUT (HERO SECTION) ---

# Replace 'kiran1.jpg' with your actual logo file name
logo_base64 = get_base64_image("kiran1.jpg")
if logo_base64:
    img_src = f"data:image/jpeg;base64,{logo_base64}"
else:
    img_src = "https://cdn-icons-png.flaticon.com/512/3175/3175218.png"

st.markdown(f"""
<div class="hero-container">
    <img src="{img_src}" class="hero-logo" alt="VidGenie Logo">
    <h1 class="vidgenie-title">VidGenie</h1>
    <p class="vidgenie-subtitle">Transform your ideas into captivating short-form videos.</p>
</div>
""", unsafe_allow_html=True)

with st.container():
    topic = st.text_area("Topic Input", height=140, label_visibility="collapsed", placeholder="Describe your video idea in detail...\nE.g., 'The history of the Samurai' or 'Top 3 hidden travel spots in Japan'")
    
    # Inspiration Pills
    st.markdown("""
    <div>
        <span class="prompt-pill">💡 The rise of AI agents</span>
        <span class="prompt-pill">💡 Stoic habits for daily life</span>
        <span class="prompt-pill">💡 Exploring deep ocean trenches</span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("✨ Generate Video"):
        if topic.strip():
            asyncio.run(generate_video_from_topic(topic, voice))
        else:
            st.warning("⚠️ Please provide a topic to generate a video.")