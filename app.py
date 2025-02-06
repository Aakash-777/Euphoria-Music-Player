from flask import Flask, render_template, jsonify, request, Response, stream_with_context
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import yt_dlp
import requests
import json
from datetime import datetime
import time

app = Flask(__name__)
load_dotenv()
API_KEY = os.getenv('YOUTUBE')

# Cache for storing video information
video_cache = {}

def setup_cookies():
    cookies_env = os.getenv('YOUTUBE_COOKIES')
    if cookies_env:
        try:
            with open('youtube_cookies.txt', 'w', encoding='utf-8') as f:
                f.write(cookies_env)
            print("Cookies setup successful")
        except Exception as e:
            print(f"Error setting up cookies: {e}")

setup_cookies()

def search_youtube(query, max_results=10):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    request = youtube.search().list(
        q=query,
        part='snippet',
        type='video',
        maxResults=max_results
    )
    response = request.execute()

    results = []
    for item in response['items']:
        results.append({
            'title': item['snippet']['title'],
            'videoId': item['id']['videoId'],
            'thumbnail': item['snippet']['thumbnails']['default']['url']
        })
    return results

def get_video_info(video_id):
    """Get video information using yt-dlp"""
    try:
        cookie_file = 'youtube_cookies.txt'
        
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'quiet': True,
            'noplaylist': True,
            'geo_bypass': True,
            'source_address': '0.0.0.0',
        }
        
        if os.path.exists(cookie_file):
            ydl_opts['cookiefile'] = cookie_file

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
            
            # Find the best audio format
            formats = info.get('formats', [])
            for f in formats:
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    return {
                        'url': f['url'],
                        'title': info.get('title', ''),
                        'content_type': f.get('ext', 'mp4'),
                        'error': None
                    }
            
            # Fallback to any format with audio
            for f in formats:
                if f.get('acodec') != 'none':
                    return {
                        'url': f['url'],
                        'title': info.get('title', ''),
                        'content_type': f.get('ext', 'mp4'),
                        'error': None
                    }
                    
            return {
                'url': info['url'],
                'title': info.get('title', ''),
                'content_type': 'mp4',
                'error': None
            }
            
    except Exception as e:
        print(f"Error getting video info: {str(e)}")
        return {'error': str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        results = search_youtube(query)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stream/<video_id>')
def stream_audio(video_id):
    """Stream audio data from YouTube"""
    try:
        # Check cache first
        video_info = video_cache.get(video_id)
        if not video_info or (datetime.now() - video_info['timestamp']).seconds > 3600:
            # Get fresh video info if not cached or expired
            video_info = get_video_info(video_id)
            if video_info.get('error'):
                return jsonify({'error': video_info['error']}), 400
            
            video_info['timestamp'] = datetime.now()
            video_cache[video_id] = video_info

        def generate():
            # Stream the content in chunks
            with requests.get(video_info['url'], stream=True) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk

        return Response(
            stream_with_context(generate()),
            content_type=f'audio/{video_info["content_type"]}'
        )

    except Exception as e:
        print(f"Streaming error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_audio', methods=['POST'])
def get_audio():
    """Get streaming endpoint URL for a video"""
    video_id = request.json.get('videoId')
    if not video_id:
        return jsonify({'error': 'No video ID provided'}), 400
    
    # Return the streaming endpoint URL
    return jsonify({
        'url': f'/stream/{video_id}',
        'error': None
    })

if __name__ == '__main__':
    app.run()