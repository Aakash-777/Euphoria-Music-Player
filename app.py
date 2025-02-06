from flask import Flask, render_template, jsonify, request
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import yt_dlp
import json

app = Flask(__name__)
load_dotenv()
API_KEY = os.getenv('YOUTUBE')

# Add this after your imports
def setup_cookies():
    cookies_env = os.getenv('YOUTUBE_COOKIES')
    if cookies_env:
        try:
            # Write cookies from environment variable to file
            with open('youtube_cookies.json', 'w') as f:
                f.write(cookies_env)
            print("Cookies setup successful")
        except Exception as e:
            print(f"Error setting up cookies: {e}")

# Add this right after creating the Flask app
setup_cookies()

# Load cookies from file
def load_cookies():
    try:
        with open('youtube_cookies.json', 'r') as f:
            return json.load(f)
    except:
        return None

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

def get_audio_url(video_id):
    try:
        cookies = load_cookies()
        
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'quiet': True,
            'noplaylist': True,
            'geo_bypass': True,
            'source_address': '0.0.0.0',
        }
        
        # Add cookies if available
        if cookies:
            ydl_opts['cookiefile'] = 'youtube_cookies.json'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
            formats = info.get('formats', [])
            
            # Find the best audio format
            for f in formats:
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    return {'url': f['url'], 'error': None}
            
            # Fallback to any format with audio
            for f in formats:
                if f.get('acodec') != 'none':
                    return {'url': f['url'], 'error': None}
                    
            return {'url': info['url'], 'error': None}
            
    except Exception as e:
        print(f"Error in get_audio_url: {str(e)}")
        return {'url': None, 'error': str(e)}

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

@app.route('/get_audio', methods=['POST'])
def get_audio():
    video_id = request.json.get('videoId')
    if not video_id:
        return jsonify({'error': 'No video ID provided'}), 400
    
    result = get_audio_url(video_id)
    if result['error']:
        return jsonify({'error': result['error']}), 400
    if result['url']:
        return jsonify({'url': result['url']})
    
    return jsonify({'error': 'Could not get audio URL'}), 400

if __name__ == '__main__':
    app.run(debug=True)