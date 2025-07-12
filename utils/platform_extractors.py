import requests
import re
import json
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import yt_dlp
from typing import Dict, List, Optional

class PlatformExtractor:
    """Base class for platform-specific video extractors"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_video_info(self, url: str) -> Dict:
        """Extract video information from URL"""
        raise NotImplementedError
    
    def get_download_url(self, url: str, quality: str = 'best') -> str:
        """Get direct download URL for video"""
        raise NotImplementedError

class TikTokExtractor(PlatformExtractor):
    """TikTok video extractor with watermark removal support"""
    
    def extract_video_info(self, url: str) -> Dict:
        """Extract TikTok video information"""
        try:
            # Use yt-dlp for TikTok extraction
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'title': info.get('title', ''),
                    'description': info.get('description', ''),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'uploader': info.get('uploader', ''),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'formats': self._extract_formats(info)
                }
        except Exception as e:
            return {'error': str(e)}
    
    def _extract_formats(self, info: Dict) -> List[Dict]:
        """Extract available video formats"""
        formats = []
        
        if 'formats' in info:
            for fmt in info['formats']:
                if fmt.get('vcodec') != 'none':
                    formats.append({
                        'format_id': fmt.get('format_id'),
                        'ext': fmt.get('ext'),
                        'quality': fmt.get('format_note', 'Unknown'),
                        'url': fmt.get('url'),
                        'filesize': fmt.get('filesize'),
                        'has_watermark': self._check_watermark(fmt)
                    })
        
        return formats
    
    def _check_watermark(self, format_info: Dict) -> bool:
        """Check if format has watermark"""
        # TikTok usually provides watermark-free versions in certain formats
        format_id = format_info.get('format_id', '')
        
        # These format IDs typically don't have watermarks
        no_watermark_formats = ['play_addr', 'download_addr']
        
        return not any(nwf in format_id for nwf in no_watermark_formats)
    
    def get_download_url(self, url: str, quality: str = 'best') -> str:
        """Get TikTok download URL without watermark"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'best[ext=mp4]/best'
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Try to find watermark-free version
                for fmt in info.get('formats', []):
                    if not self._check_watermark(fmt) and fmt.get('url'):
                        return fmt['url']
                
                # Fallback to best available format
                return info.get('url', '')
                
        except Exception:
            return ''

class InstagramExtractor(PlatformExtractor):
    """Instagram video extractor"""
    
    def extract_video_info(self, url: str) -> Dict:
        """Extract Instagram video information"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'title': info.get('title', ''),
                    'description': info.get('description', ''),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'uploader': info.get('uploader', ''),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'formats': self._extract_formats(info)
                }
        except Exception as e:
            return {'error': str(e)}
    
    def _extract_formats(self, info: Dict) -> List[Dict]:
        """Extract available video formats"""
        formats = []
        
        if 'formats' in info:
            for fmt in info['formats']:
                if fmt.get('vcodec') != 'none':
                    formats.append({
                        'format_id': fmt.get('format_id'),
                        'ext': fmt.get('ext'),
                        'quality': fmt.get('format_note', 'Unknown'),
                        'url': fmt.get('url'),
                        'filesize': fmt.get('filesize')
                    })
        
        return formats

class YouTubeExtractor(PlatformExtractor):
    """YouTube video extractor"""
    
    def extract_video_info(self, url: str) -> Dict:
        """Extract YouTube video information"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'title': info.get('title', ''),
                    'description': info.get('description', ''),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'uploader': info.get('uploader', ''),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'upload_date': info.get('upload_date', ''),
                    'formats': self._extract_formats(info)
                }
        except Exception as e:
            return {'error': str(e)}
    
    def _extract_formats(self, info: Dict) -> List[Dict]:
        """Extract available video formats with quality options"""
        formats = []
        
        if 'formats' in info:
            # Group formats by quality
            quality_map = {}
            
            for fmt in info['formats']:
                if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                    height = fmt.get('height', 0)
                    quality_label = self._get_quality_label(height)
                    
                    if quality_label not in quality_map or fmt.get('filesize', 0) > quality_map[quality_label].get('filesize', 0):
                        quality_map[quality_label] = {
                            'format_id': fmt.get('format_id'),
                            'ext': fmt.get('ext'),
                            'quality': quality_label,
                            'resolution': f"{fmt.get('width', 0)}x{fmt.get('height', 0)}",
                            'url': fmt.get('url'),
                            'filesize': fmt.get('filesize'),
                            'fps': fmt.get('fps'),
                            'vcodec': fmt.get('vcodec'),
                            'acodec': fmt.get('acodec')
                        }
            
            formats = list(quality_map.values())
        
        return formats
    
    def _get_quality_label(self, height: int) -> str:
        """Convert height to quality label"""
        if height >= 2160:
            return '4K'
        elif height >= 1440:
            return '1440p'
        elif height >= 1080:
            return '1080p'
        elif height >= 720:
            return '720p'
        elif height >= 480:
            return '480p'
        elif height >= 360:
            return '360p'
        else:
            return '240p'

class FacebookExtractor(PlatformExtractor):
    """Facebook video extractor"""
    
    def extract_video_info(self, url: str) -> Dict:
        """Extract Facebook video information"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'title': info.get('title', ''),
                    'description': info.get('description', ''),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'uploader': info.get('uploader', ''),
                    'view_count': info.get('view_count', 0),
                    'formats': self._extract_formats(info)
                }
        except Exception as e:
            return {'error': str(e)}
    
    def _extract_formats(self, info: Dict) -> List[Dict]:
        """Extract available video formats"""
        formats = []
        
        if 'formats' in info:
            for fmt in info['formats']:
                if fmt.get('vcodec') != 'none':
                    formats.append({
                        'format_id': fmt.get('format_id'),
                        'ext': fmt.get('ext'),
                        'quality': fmt.get('format_note', 'Unknown'),
                        'url': fmt.get('url'),
                        'filesize': fmt.get('filesize')
                    })
        
        return formats

class TwitterExtractor(PlatformExtractor):
    """Twitter/X video extractor"""
    
    def extract_video_info(self, url: str) -> Dict:
        """Extract Twitter video information"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'title': info.get('title', ''),
                    'description': info.get('description', ''),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'uploader': info.get('uploader', ''),
                    'view_count': info.get('view_count', 0),
                    'formats': self._extract_formats(info)
                }
        except Exception as e:
            return {'error': str(e)}
    
    def _extract_formats(self, info: Dict) -> List[Dict]:
        """Extract available video formats"""
        formats = []
        
        if 'formats' in info:
            for fmt in info['formats']:
                if fmt.get('vcodec') != 'none':
                    formats.append({
                        'format_id': fmt.get('format_id'),
                        'ext': fmt.get('ext'),
                        'quality': fmt.get('format_note', 'Unknown'),
                        'url': fmt.get('url'),
                        'filesize': fmt.get('filesize')
                    })
        
        return formats

class ExtractorFactory:
    """Factory class to get appropriate extractor for platform"""
    
    extractors = {
        'tiktok': TikTokExtractor,
        'instagram': InstagramExtractor,
        'youtube': YouTubeExtractor,
        'facebook': FacebookExtractor,
        'twitter': TwitterExtractor
    }
    
    @classmethod
    def get_extractor(cls, platform: str) -> Optional[PlatformExtractor]:
        """Get extractor instance for platform"""
        extractor_class = cls.extractors.get(platform)
        if extractor_class:
            return extractor_class()
        return None

