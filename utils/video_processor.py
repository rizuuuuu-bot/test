import os
import subprocess
import tempfile
from typing import Dict, List, Optional, Tuple
import json

class VideoProcessor:
    """Advanced video processing utilities for quality enhancement and watermark removal"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def get_video_metadata(self, video_path: str) -> Dict:
        """Extract detailed video metadata using ffprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {}
        except Exception:
            return {}
    
    def enhance_video_quality(self, input_path: str, output_path: str, 
                            target_resolution: str = "1920x1080") -> bool:
        """Enhance video quality using ffmpeg"""
        try:
            cmd = [
                'ffmpeg', '-i', input_path,
                '-vf', f'scale={target_resolution}:flags=lanczos',
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
                '-c:a', 'aac', '-b:a', '192k',
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def remove_watermark_by_cropping(self, input_path: str, output_path: str,
                                   crop_params: str = "iw-200:ih-100:100:50") -> bool:
        """Remove watermark by cropping the video"""
        try:
            cmd = [
                'ffmpeg', '-i', input_path,
                '-vf', f'crop={crop_params}',
                '-c:a', 'copy',
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def remove_watermark_by_blurring(self, input_path: str, output_path: str,
                                   blur_region: str = "100:50:200:100") -> bool:
        """Remove watermark by blurring a specific region"""
        try:
            x, y, w, h = blur_region.split(':')
            cmd = [
                'ffmpeg', '-i', input_path,
                '-vf', f'boxblur=enable=\'between(t,0,999)\':x={x}:y={y}:w={w}:h={h}:blur_radius=10',
                '-c:a', 'copy',
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def convert_format(self, input_path: str, output_path: str, 
                      target_format: str = "mp4") -> bool:
        """Convert video to different format"""
        try:
            cmd = [
                'ffmpeg', '-i', input_path,
                '-c:v', 'libx264', '-c:a', 'aac',
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def compress_video(self, input_path: str, output_path: str,
                      target_size_mb: int = 50) -> bool:
        """Compress video to target file size"""
        try:
            # Get video duration first
            metadata = self.get_video_metadata(input_path)
            duration = float(metadata.get('format', {}).get('duration', 0))
            
            if duration == 0:
                return False
            
            # Calculate target bitrate
            target_bitrate = int((target_size_mb * 8 * 1024) / duration)
            
            cmd = [
                'ffmpeg', '-i', input_path,
                '-b:v', f'{target_bitrate}k',
                '-maxrate', f'{target_bitrate * 1.2}k',
                '-bufsize', f'{target_bitrate * 2}k',
                '-c:v', 'libx264', '-preset', 'medium',
                '-c:a', 'aac', '-b:a', '128k',
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def extract_audio(self, input_path: str, output_path: str) -> bool:
        """Extract audio from video"""
        try:
            cmd = [
                'ffmpeg', '-i', input_path,
                '-vn', '-acodec', 'mp3', '-ab', '192k',
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def create_thumbnail(self, input_path: str, output_path: str,
                        timestamp: str = "00:00:01") -> bool:
        """Create thumbnail from video"""
        try:
            cmd = [
                'ffmpeg', '-i', input_path,
                '-ss', timestamp, '-vframes', '1',
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass

class PlatformSpecificProcessor:
    """Platform-specific video processing logic"""
    
    @staticmethod
    def process_tiktok_video(input_path: str, output_path: str) -> bool:
        """Process TikTok video to remove watermark"""
        processor = VideoProcessor()
        
        # TikTok watermarks are usually in the bottom-right corner
        # Crop the video to remove the watermark area
        crop_params = "iw-150:ih-80:0:0"  # Remove 150px from right, 80px from bottom
        
        return processor.remove_watermark_by_cropping(input_path, output_path, crop_params)
    
    @staticmethod
    def process_instagram_video(input_path: str, output_path: str) -> bool:
        """Process Instagram video for optimal quality"""
        processor = VideoProcessor()
        
        # Instagram videos are usually good quality, just ensure proper format
        return processor.convert_format(input_path, output_path, "mp4")
    
    @staticmethod
    def process_youtube_video(input_path: str, output_path: str) -> bool:
        """Process YouTube video for optimal quality"""
        processor = VideoProcessor()
        
        # YouTube videos are usually high quality, just convert if needed
        return processor.convert_format(input_path, output_path, "mp4")
    
    @staticmethod
    def process_facebook_video(input_path: str, output_path: str) -> bool:
        """Process Facebook video"""
        processor = VideoProcessor()
        
        # Facebook videos might need quality enhancement
        return processor.enhance_video_quality(input_path, output_path)
    
    @staticmethod
    def process_twitter_video(input_path: str, output_path: str) -> bool:
        """Process Twitter/X video"""
        processor = VideoProcessor()
        
        # Twitter videos are often compressed, enhance quality
        return processor.enhance_video_quality(input_path, output_path)

