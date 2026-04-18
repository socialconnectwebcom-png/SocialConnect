from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@app.route('/')
def home():
    return "SocialConnect Server is Running!"

@app.route('/fetch-video', methods=['POST'])
def fetch_video():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400

    try:
        ydl_opts = {
            'quiet': True, 
            'no_warnings': True,
            'cookiefile': 'cookies.txt',
            'noplaylist': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                'original_url': url,
                'title': info.get('title', 'SocialConnect_Video'),
                'thumbnail': info.get('thumbnail', ''),
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['GET'])
def proxy_download():
    url = request.args.get('url')
    title = request.args.get('title', 'SocialConnect_Download')
    ext = request.args.get('ext', 'mp4') 
    quality = request.args.get('quality', 'premium')

    if not url:
        return "URL is required", 400

    safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    if not safe_title:
        safe_title = "SocialConnect_Audio_Video"

    base_path = os.path.join(DOWNLOAD_DIR, safe_title)

    try:
        ydl_opts = {
            'outtmpl': f"{base_path}.%(ext)s",
            'quiet': True,
            'no_warnings': True,
            'cookiefile': 'cookies.txt',
            'noplaylist': True
        }

        if quality == 'audio':
            # 🎧 Music Quality එක උපරිම (320kbps MP3) කරා
            ext = 'mp3' # අනිවාර්යයෙන්ම MP3 කරනවා
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320', # MP3 වල උපරිම Bitrate එක
            }]
            
        elif quality == 'normal':
            # 📱 Normal Quality එක හරියටම හැදුවා 
            # (480p නැත්නම් 360p ගන්නවා, ඒකත් නැත්නම් තියෙන අඩුම එක ගන්නවා මිසක් ලොකු ඒවා ගන්නේ නෑ)
            ydl_opts['format'] = 'bestvideo[height<=480][vcodec^=avc]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[height<=360]/worst'
            ydl_opts['merge_output_format'] = 'mp4'
            
        else:
            # 🎬 Premium Quality එක
            ydl_opts['format'] = 'bestvideo[vcodec^=avc]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            ydl_opts['merge_output_format'] = 'mp4'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        final_file = None
        for f in os.listdir(DOWNLOAD_DIR):
            if safe_title in f and not f.endswith('.part') and not f.endswith('.ytdl'):
                final_file = os.path.join(DOWNLOAD_DIR, f)
                break

        if final_file:
            return send_file(final_file, as_attachment=True)
        else:
            return "File not found after download", 500

    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
