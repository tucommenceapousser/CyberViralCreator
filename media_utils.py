import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip, vfx
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
import logging
import time
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_disk_space(file_size):
    """Check if there's enough disk space for processing"""
    try:
        st = os.statvfs('/')
        free_space = st.f_bavail * st.f_frsize
        # Require 3x the file size for processing
        return free_space > (file_size * 3)
    except:
        # Default to True on systems where statvfs is not available
        return True

def cleanup_temp_files():
    """Clean up temporary files created during processing"""
    temp_pattern = "*TEMP_MPY*"
    try:
        import glob
        for temp_file in glob.glob(temp_pattern):
            try:
                os.remove(temp_file)
            except OSError:
                pass
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {str(e)}")

def optimize_video_settings(clip, target_size_mb=20):
    """Optimize video settings to reduce file size"""
    target_bitrate = f"{target_size_mb}M"
    return {
        'codec': 'libx264',
        'bitrate': target_bitrate,
        'audio_codec': 'aac',
        'audio_bitrate': '128k',
        'preset': 'faster',
        'threads': 2
    }

def extract_audio_from_video(video_path, output_path=None):
    """Extract audio from a video file with optimization"""
    try:
        if not output_path:
            output_path = os.path.splitext(video_path)[0] + '.mp3'
        
        if not check_disk_space(os.path.getsize(video_path)):
            raise Exception("Insufficient disk space for processing")
            
        video = VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(output_path, 
                            bitrate="128k",
                            fps=44100,
                            nbytes=2,
                            codec='libmp3lame')
        
        audio.close()
        video.close()
        cleanup_temp_files()
        
        return output_path
    except Exception as e:
        cleanup_temp_files()
        logger.error(f"Error extracting audio from video: {str(e)}")
        raise

def combine_audio_with_video(video_path, audio_path, output_path=None):
    """Combine audio with video with optimization"""
    try:
        if not output_path:
            output_path = os.path.splitext(video_path)[0] + '_combined.mp4'
            
        total_size = os.path.getsize(video_path) + os.path.getsize(audio_path)
        if not check_disk_space(total_size):
            raise Exception("Insufficient disk space for processing")
            
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        
        if audio.duration > video.duration:
            audio = audio.subclip(0, video.duration)
        
        final_video = video.set_audio(audio)
        final_video.write_videofile(output_path, **optimize_video_settings(final_video))
        
        video.close()
        audio.close()
        final_video.close()
        cleanup_temp_files()
        
        return output_path
    except Exception as e:
        cleanup_temp_files()
        logger.error(f"Error combining audio with video: {str(e)}")
        raise

def add_text_overlay(video_path, text, position='bottom', output_path=None, theme='anonymous'):
    """Add text overlay to video with optimization"""
    try:
        if not output_path:
            output_path = os.path.splitext(video_path)[0] + '_with_text.mp4'
            
        if not check_disk_space(os.path.getsize(video_path)):
            raise Exception("Insufficient disk space for processing")
            
        # Theme-based text styles (rest of the styles remain the same)
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
        
        # Create text clip with styling
        text_clip = TextClip(text, fontsize=style['fontsize'],
                           color=style['color'],
                           bg_color=style['bg_color'],
                           font=style['font'])
        
        # Apply effects and position the text
        if position == 'bottom':
            text_clip = text_clip.set_position(('center', 0.85), relative=True)
        else:
            text_clip = text_clip.set_position(('center', 0.1), relative=True)
        
        text_clip = text_clip.set_duration(video.duration)
        
        # Combine video with text
        final_video = CompositeVideoClip([video, text_clip])
        final_video.write_videofile(output_path, **optimize_video_settings(final_video))
        
        video.close()
        text_clip.close()
        final_video.close()
        cleanup_temp_files()
        
        return output_path
    except Exception as e:
        cleanup_temp_files()
        logger.error(f"Error adding text overlay: {str(e)}")
        raise

def process_audio(audio_path, theme='anonymous', output_path=None):
    """Process audio with optimization"""
    try:
        if not output_path:
            output_path = os.path.splitext(audio_path)[0] + '_processed.mp3'
            
        if not check_disk_space(os.path.getsize(audio_path)):
            raise Exception("Insufficient disk space for processing")
            
        # Load and normalize audio
        audio = AudioSegment.from_file(audio_path)
        audio = normalize(audio)
        
        # Apply theme-based effects with optimized settings
        if theme == 'anonymous':
            audio = audio.low_pass_filter(3000)
            audio = compress_dynamic_range(audio, ratio=2.0)
        elif theme == 'cyber':
            audio = audio.high_pass_filter(1000)
            audio = audio.low_pass_filter(4000)
            audio = compress_dynamic_range(audio, ratio=2.5)
        elif theme == 'hacking':
            audio = audio.high_pass_filter(2000)
            audio = compress_dynamic_range(audio, ratio=2.0)
        elif theme == 'hacktivism':
            audio = audio.low_pass_filter(2500)
            audio = compress_dynamic_range(audio, ratio=2.0)
            
        # Export with optimized settings
        audio.export(output_path, 
                    format='mp3',
                    bitrate='128k',
                    parameters=["-q:a", "4"])
        
        cleanup_temp_files()
        return output_path
    except Exception as e:
        cleanup_temp_files()
        logger.error(f"Error processing audio: {str(e)}")
        raise
