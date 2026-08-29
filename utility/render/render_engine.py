import time
import os
import tempfile
import zipfile
import platform
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (AudioFileClip, CompositeVideoClip, CompositeAudioClip, ImageClip,
                            VideoFileClip)
from moviepy.audio.fx.audio_loop import audio_loop
from moviepy.audio.fx.audio_normalize import audio_normalize
import requests
from utility.config import get_config

def download_file(url, filename):
    with open(filename, 'wb') as f:
        headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        f.write(response.content)

def search_program(program_name):
    try: 
        search_cmd = "where" if platform.system() == "Windows" else "which"
        return subprocess.check_output([search_cmd, program_name]).decode().strip()
    except subprocess.CalledProcessError:
        return None

def get_program_path(program_name):
    program_path = search_program(program_name)
    return program_path

def get_output_media(audio_file_path, timed_captions, background_video_data, video_server, background_music_path=None):
    config = get_config()
    
    # Check if rendering with Remotion is configured
    render_engine = os.getenv('RENDER_ENGINE', 'moviepy').lower()
    if render_engine == 'remotion':
        print("[RenderEngine] Routing compilation to React/Remotion renderer...")
        from utility.render.remotion_renderer import render_with_remotion
        return render_with_remotion(
            audio_file_path=audio_file_path,
            timed_captions=timed_captions,
            background_video_data=background_video_data,
            background_music_path=background_music_path
        )

    OUTPUT_FILE_NAME = "rendered_video.mp4"
    
    visual_clips = []
    for (t1, t2), video_url in background_video_data:
        # Download video file
        video_filename = tempfile.NamedTemporaryFile(delete=False).name
        download_file(video_url, video_filename)
        
        # Create VideoFileClip from downloaded file
        video_clip = VideoFileClip(video_filename)
        video_clip = video_clip.set_start(t1)
        video_clip = video_clip.set_end(t2)
        visual_clips.append(video_clip)
    
    audio_clips = []
    audio_file_clip = AudioFileClip(audio_file_path)
    audio_clips.append(audio_file_clip)

    if background_music_path and os.path.exists(background_music_path):
        try:
            bg_music_clip = AudioFileClip(background_music_path)
            # Set volume of background music to 12% so voiceover remains clear
            bg_music_clip = bg_music_clip.volumex(0.12)
            # Loop bg music if it's shorter than voiceover
            if bg_music_clip.duration < audio_file_clip.duration:
                bg_music_clip = audio_loop(bg_music_clip, duration=audio_file_clip.duration)
            else:
                bg_music_clip = bg_music_clip.set_duration(audio_file_clip.duration)
            audio_clips.append(bg_music_clip)
            print("[RenderEngine] Successfully loaded and mixed background music.")
        except Exception as e:
            print(f"[RenderEngine] Error loading/mixing background music: {e}")

    
    # Only add captions if enabled in config (using pure Python Pillow to bypass ImageMagick policy restrictions)
    if config.get_captions_enabled():
        for (t1, t2), text in timed_captions:
            font_size = config.get_caption_font_size()
            font_color = config.get_caption_font_color()
            stroke_width = config.get_caption_stroke_width()
            stroke_color = config.get_caption_stroke_color()
            caption_position = config.get_caption_position()

            if caption_position == 'bottom_center':
                position = ["center", 1000]
            elif caption_position == 'bottom_left':
                position = ["left", 1000]
            elif caption_position == 'bottom_right':
                position = ["right", 1000]
            elif caption_position == 'top':
                position = ["center", 100]
            elif caption_position == 'center':
                position = ["center", 540]
            else:
                position = ["center", 1000]

            # Generate caption overlay using Pillow
            img_width, img_height = 1080, 200
            img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()
                
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (img_width - text_width) / 2
            y = (img_height - text_height) / 2
            
            if stroke_width > 0:
                for adj_x in range(-stroke_width, stroke_width + 1):
                    for adj_y in range(-stroke_width, stroke_width + 1):
                        draw.text((x + adj_x, y + adj_y), text, font=font, fill=stroke_color)
                        
            draw.text((x, y), text, font=font, fill=font_color)
            
            text_clip = ImageClip(np.array(img)).set_start(t1).set_end(t2).set_position(position)
            visual_clips.append(text_clip)
    
    video = CompositeVideoClip(visual_clips)
    
    if audio_clips:
        audio = CompositeAudioClip(audio_clips)
        video.duration = audio.duration
        video.audio = audio

    video.write_videofile(OUTPUT_FILE_NAME, codec='libx264', audio_codec='aac', fps=25, preset='veryfast')
    
    # Clean up downloaded files
    for (t1, t2), video_url in background_video_data:
        video_filename = tempfile.NamedTemporaryFile(delete=False).name
        if os.path.exists(video_filename):
            os.remove(video_filename)

    return OUTPUT_FILE_NAME