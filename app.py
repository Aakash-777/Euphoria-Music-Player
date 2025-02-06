from flask import Flask, render_template, jsonify, request
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import yt_dlp
import json

app = Flask(__name__)
load_dotenv()
API_KEY = os.getenv('YOUTUBE')

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
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'quiet': True,
            'noplaylist': True,
            'geo_bypass': True,
            'source_address': '0.0.0.0',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
            return info['url']
    except Exception as e:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    results = search_youtube(query)
    return jsonify(results)

@app.route('/get_audio', methods=['POST'])
def get_audio():
    video_id = request.json.get('videoId')
    if not video_id:
        return jsonify({'error': 'No video ID provided'}), 400
    
    audio_url = get_audio_url(video_id)
    if not audio_url:
        return jsonify({'error': 'Could not get audio URL'}), 400
    
    return jsonify({'url': audio_url})

if __name__ == '__main__':
    app.run(debug=True)