from flask import Blueprint, request, jsonify, send_file
from flask_cors import cross_origin
import yt_dlp
import os
import tempfile
import validators
import re
import requests
from urllib.parse import urlparse
import json
import time

downloader_bp = Blueprint('downloader', __name__)

# Supported platforms configuration
SUPPORTED_PLATFORMS = {
    'youtube': {
        'domains': ['youtube.com', 'youtu.be', 'm.youtube.com'],
        'name': 'YouTube',
        'icon': 'youtube'
    },
    'tiktok': {
        'domains': ['tiktok.com', 'vm.tiktok.com', 'm.tiktok.com'],
        'name': 'TikTok',
        'icon': 'tiktok'
    },
    'instagram': {
        'domains': ['instagram.com', 'instagr.am'],
        'name': 'Instagram',
        'icon': 'instagram'
    },
    'facebook': {
        'domains': ['facebook.com', 'fb.watch', 'm.facebook.com'],
        'name': 'Facebook',
        'icon': 'facebook'
    },
    'twitter': {
        'domains': ['twitter.com', 'x.com', 't.co'],
        'name': 'Twitter/X',
        'icon': 'twitter'
    },
    'vimeo': {
        'domains': ['vimeo.com'],
        'name': 'Vimeo',
        'icon': 'vimeo'
    },
    'dailymotion': {
        'domains': ['dailymotion.com', 'dai.ly'],
        'name': 'Dailymotion',
        'icon': 'dailymotion'
    }
}

def detect_platform(url):
    """Detect which platform the URL belongs to"""
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        for platform, config in SUPPORTED_PLATFORMS.items():
            if any(domain.endswith(supported_domain) for supported_domain in config['domains']):
                return platform
                
        return None
    except Exception:
        return None

def get_video_info(url):
    """Extract video information without downloading"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Extract relevant information
            video_info = {
                'title': info.get('title', 'Unknown Title'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'uploader': info.get('uploader', 'Unknown'),
                'view_count': info.get('view_count', 0),
                'upload_date': info.get('upload_date', ''),
                'description': info.get('description', '')[:200] + '...' if info.get('description') else '',
                'formats': []
            }
            
            # Extract available formats
            if 'formats' in info:
                for fmt in info['formats']:
                    if fmt.get('vcodec') != 'none':  # Only video formats
                        format_info = {
                            'format_id': fmt.get('format_id'),
                            'ext': fmt.get('ext'),
                            'quality': fmt.get('format_note', 'Unknown'),
                            'resolution': fmt.get('resolution', 'Unknown'),
                            'filesize': fmt.get('filesize'),
                            'fps': fmt.get('fps'),
                            'vcodec': fmt.get('vcodec'),
                            'acodec': fmt.get('acodec')
                        }
                        video_info['formats'].append(format_info)
            
            return video_info
            
    except Exception as e:
        raise Exception(f"Failed to extract video info: {str(e)}")

def download_video(url, quality='best', format_type='mp4'):
    """Download video with specified quality and format"""
    try:
        # Create temporary directory for downloads
        temp_dir = tempfile.mkdtemp()
        
        # Configure yt-dlp options
        ydl_opts = {
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'format': f'{quality}[ext={format_type}]/best[ext={format_type}]/best',
            'quiet': True,
            'no_warnings': True,
        }
        
        # Special handling for TikTok to remove watermark
        platform = detect_platform(url)
        if platform == 'tiktok':
            ydl_opts['format'] = 'best[ext=mp4]/best'
            # Try to get the version without watermark
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            
            # Download the video
            ydl.download([url])
            
            # Find the downloaded file
            for file in os.listdir(temp_dir):
                if file.endswith(('.mp4', '.webm', '.mkv', '.avi')):
                    file_path = os.path.join(temp_dir, file)
                    file_size = os.path.getsize(file_path)
                    
                    return {
                        'file_path': file_path,
                        'filename': file,
                        'title': title,
                        'size': file_size,
                        'temp_dir': temp_dir
                    }
                    
        raise Exception("No video file found after download")
        
    except Exception as e:
        raise Exception(f"Download failed: {str(e)}")

@downloader_bp.route('/api/platforms', methods=['GET'])
@cross_origin()
def get_supported_platforms():
    """Get list of supported platforms"""
    return jsonify({
        'success': True,
        'platforms': SUPPORTED_PLATFORMS
    })

@downloader_bp.route('/api/detect', methods=['POST'])
@cross_origin()
def detect_video_platform():
    """Detect platform from URL"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            }), 400
            
        if not validators.url(url):
            return jsonify({
                'success': False,
                'error': 'Invalid URL format'
            }), 400
            
        platform = detect_platform(url)
        
        if not platform:
            return jsonify({
                'success': False,
                'error': 'Unsupported platform'
            }), 400
            
        return jsonify({
            'success': True,
            'platform': platform,
            'platform_info': SUPPORTED_PLATFORMS[platform]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@downloader_bp.route('/api/info', methods=['POST'])
@cross_origin()
def get_video_information():
    """Get video information and available formats"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            }), 400
            
        if not validators.url(url):
            return jsonify({
                'success': False,
                'error': 'Invalid URL format'
            }), 400
            
        platform = detect_platform(url)
        if not platform:
            return jsonify({
                'success': False,
                'error': 'Unsupported platform'
            }), 400
            
        video_info = get_video_info(url)
        video_info['platform'] = platform
        video_info['platform_info'] = SUPPORTED_PLATFORMS[platform]
        
        return jsonify({
            'success': True,
            'video_info': video_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@downloader_bp.route('/api/download', methods=['POST'])
@cross_origin()
def download_video_endpoint():
    """Download video with specified options"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        quality = data.get('quality', 'best')
        format_type = data.get('format', 'mp4')
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            }), 400
            
        if not validators.url(url):
            return jsonify({
                'success': False,
                'error': 'Invalid URL format'
            }), 400
            
        platform = detect_platform(url)
        if not platform:
            return jsonify({
                'success': False,
                'error': 'Unsupported platform'
            }), 400
            
        # Download the video
        download_result = download_video(url, quality, format_type)
        
        # Return file for download
        return send_file(
            download_result['file_path'],
            as_attachment=True,
            download_name=f"{download_result['title']}.{format_type}",
            mimetype='video/mp4'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@downloader_bp.route('/api/health', methods=['GET'])
@cross_origin()
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': int(time.time()),
        'supported_platforms': len(SUPPORTED_PLATFORMS)
    })

@downloader_bp.route('/api/stats', methods=['GET'])
@cross_origin()
def get_stats():
    """Get API statistics"""
    return jsonify({
        'success': True,
        'stats': {
            'supported_platforms': len(SUPPORTED_PLATFORMS),
            'total_downloads': 0,  # This would be tracked in a real database
            'uptime': '24/7',
            'version': '1.0.0'
        }
    })

