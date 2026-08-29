import time
import os
import tempfile
import platform
import subprocess
import numpy as np
import gc
import torch
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (AudioFileClip, CompositeVideoClip, CompositeAudioClip, ImageClip, VideoFileClip)
from moviepy.audio.fx.audio_loop import audio_loop
import requests
from utility.config import get_config

def download_file(url, filename):
    with open(filename, 'wb') as f:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers)
        f.write(response.content)

def get_output_media(audio_file_path, timed_captions, background_video_data, video_server, background_music_path=None):
    config = get_config()
    OUTPUT_FILE_NAME = "rendered_video.mp4"
    
    visual_clips = []
    temp_video_files = []
    
    try:
        for (t1, t2), video_url in background_video_data:
            video_filename = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            temp_video_files.append(video_filename)
            download_file(video_url, video_filename)
            
            video_clip = VideoFileClip(video_filename).set_start(t1).set_end(t2)
            visual_clips.append(video_clip)
        
        audio_clips = []
        audio_file_clip = AudioFileClip(audio_file_path)
        audio_clips.append(audio_file_clip)

        bg_music_clip = None
        if background_music_path and os.path.exists(background_music_path):
            try:
                bg_music_clip = AudioFileClip(background_music_path).volumex(0.12)
                if bg_music_clip.duration < audio_file_clip.duration:
                    bg_music_clip = audio_loop(bg_music_clip, duration=audio_file_clip.duration)
                else:
                    bg_music_clip = bg_music_clip.set_duration(audio_file_clip.duration)
                audio_clips.append(bg_music_clip)
            except Exception as e:
                print(f"[RenderEngine] Error loading background music: {e}")

        if config.get_captions_enabled():
            font_size = config.get_caption_font_size()
            font_color = config.get_caption_font_color()
            stroke_width = config.get_caption_stroke_width()
            stroke_color = config.get_caption_stroke_color()
            caption_position = config.get_caption_position()

            pos_map = {
                'bottom_center': ["center", 1000],
                'bottom_left': ["left", 1000],
                'bottom_right': ["right", 1000],
                'top': ["center", 100],
                'center': ["center", 540]
            }
            position = pos_map.get(caption_position, ["center", 1000])

            for (t1, t2), text in timed_captions:
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
        
        return OUTPUT_FILE_NAME

    finally:
        # Explicitly close all clips to release file handles and RAM
        for clip in visual_clips:
            try:
                clip.close()
            except:
                pass
        try:
            audio_file_clip.close()
        except:
            pass
        if 'bg_music_clip' in locals() and bg_music_clip:
            try:
                bg_music_clip.close()
            except:
                pass
        try:
            video.close()
        except:
            pass

        # Cleanup temporary files
        for f in temp_video_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass

        # Force garbage collection
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()