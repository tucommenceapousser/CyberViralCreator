import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip, vfx
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_audio_from_video(video_path, output_path=None):
    """Extract audio from a video file"""
    try:
        if not output_path:
            output_path = os.path.splitext(video_path)[0] + '.mp3'
        
        video = VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(output_path)
        audio.close()
        video.close()
        
        return output_path
    except Exception as e:
        logger.error(f"Error extracting audio from video: {str(e)}")
        raise

def combine_audio_with_video(video_path, audio_path, output_path=None):
    """Combine audio with video"""
    try:
        if not output_path:
            output_path = os.path.splitext(video_path)[0] + '_combined.mp4'
        
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        
        # If audio is longer than video, trim it
        if audio.duration > video.duration:
            audio = audio.subclip(0, video.duration)
        
        final_video = video.set_audio(audio)
        final_video.write_videofile(output_path)
        
        video.close()
        audio.close()
        final_video.close()
        
        return output_path
    except Exception as e:
        logger.error(f"Error combining audio with video: {str(e)}")
        raise

def add_text_overlay(video_path, text, position='bottom', output_path=None, theme='anonymous'):
    """Add text overlay to video with enhanced theme-based styling"""
    try:
        if not output_path:
            output_path = os.path.splitext(video_path)[0] + '_with_text.mp4'
            
        # Enhanced theme-based text styles
        theme_styles = {
            'anonymous': {
                'color': 'white',
                'bg_color': 'black',
                'font': 'Arial',
                'effect': 'glitch',
                'fontsize': 30
            },
            'cyber': {
                'color': '#00ff00',
                'bg_color': 'black',
                'font': 'Arial-Bold',
                'effect': 'matrix',
                'fontsize': 36
            },
            'hacking': {
                'color': '#00ff00',
                'bg_color': 'black',
                'font': 'Courier',
                'effect': 'terminal',
                'fontsize': 28
            },
            'hacktivism': {
                'color': 'red',
                'bg_color': 'black',
                'font': 'Arial-Bold',
                'effect': 'flicker',
                'fontsize': 32
            }
        }
        
        style = theme_styles.get(theme, theme_styles['anonymous'])
        video = VideoFileClip(video_path)
        
        # Create text clip with enhanced styling
        text_clip = TextClip(
            text,
            fontsize=style['fontsize'],
            color=style['color'],
            bg_color=style['bg_color'],
            font=style['font']
        )
        
        # Apply theme-based effects
        if style['effect'] == 'glitch':
            text_clip = text_clip.fx(vfx.colorx, 1.2)
        elif style['effect'] == 'matrix':
            text_clip = text_clip.fx(vfx.glow, 1.5)
        elif style['effect'] == 'terminal':
            text_clip = text_clip.fx(vfx.blackwhite)
        elif style['effect'] == 'flicker':
            # Modified flicker effect without painting
            text_clip = text_clip.fx(vfx.colorx, 1.5).fx(vfx.lum_contrast, lum=0, contrast=1.5)
        
        # Position the text with padding
        if position == 'bottom':
            text_clip = text_clip.set_position(('center', 0.85), relative=True)
        elif position == 'top':
            text_clip = text_clip.set_position(('center', 0.1), relative=True)
        
        text_clip = text_clip.set_duration(video.duration)
        
        # Add semi-transparent background for better readability
        txt_col = ColorClip(size=(video.w, text_clip.h + 20),
                          color=(0, 0, 0))
        txt_col = txt_col.set_opacity(.6)
        txt_col = txt_col.set_duration(video.duration)
        txt_col = txt_col.set_position(text_clip.pos(video))
        
        # Combine video with background and text
        final_video = CompositeVideoClip([video, txt_col, text_clip])
        final_video.write_videofile(output_path)
        
        video.close()
        text_clip.close()
        final_video.close()
        
        return output_path
    except Exception as e:
        logger.error(f"Error adding text overlay: {str(e)}")
        raise

def process_audio(audio_path, theme='anonymous', output_path=None):
    """Process audio with enhanced theme-based effects"""
    try:
        if not output_path:
            output_path = os.path.splitext(audio_path)[0] + '_processed.mp3'
            
        # Load audio file
        audio = AudioSegment.from_file(audio_path)
        
        # Normalize audio first
        audio = normalize(audio)
        
        # Apply enhanced theme-based effects
        if theme == 'anonymous':
            # Add voice modulation effect
            audio = audio.low_pass_filter(3000)
            audio = compress_dynamic_range(audio)
            audio = audio + audio.invert_phase().fade_in(50).fade_out(50)
        elif theme == 'cyber':
            # Add futuristic effect
            audio = audio.high_pass_filter(1000)
            audio = audio.low_pass_filter(4000)
            audio = audio + audio.reverse().fade_in(100).fade_out(100)
            audio = compress_dynamic_range(audio, ratio=4.0)
        elif theme == 'hacking':
            # Add glitch effect
            audio = audio + audio.invert_phase()
            audio = audio.high_pass_filter(2000)
            glitch = audio.fade_out(200).reverse()
            audio = audio.overlay(glitch, position=1000)
        elif theme == 'hacktivism':
            # Add dramatic effect
            audio = audio.low_pass_filter(2500)
            echo = audio.fade_out(500)
            audio = audio.overlay(echo, position=250)
            audio = compress_dynamic_range(audio, ratio=3.0)
            
        # Final processing
        audio = normalize(audio)  # Normalize again after effects
        
        # Export processed audio
        audio.export(output_path, format='mp3')
        return output_path
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        raise
