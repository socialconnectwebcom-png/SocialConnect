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
            'noplaylist': True,
            # YouTube Bot check එක bypass කරන Android trick එක
            'extractor_args': {'youtube': ['player_client=android']}
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

    safe_title = "".join([c for c in title if c.isalnum() or c==' ']).strip()
    if not safe_title:
        safe_title = "SocialConnect_Media"

    base_path = os.path.join(DOWNLOAD_DIR, safe_title)

    try:
        ydl_opts = {
            'outtmpl': f"{base_path}.%(ext)s",
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'extractor_args': {'youtube': ['player_client=android']}
        }

        if quality == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            ext = 'mp3'
            mimetype = 'audio/mpeg'
        
        elif quality == 'normal':
            # අඩු කොලිටිය (480p හෝ ඊට අඩු)
            ydl_opts['format'] = 'bestvideo[height<=480]+bestaudio/best[height<=480]/best[height<=480]/best'
            ydl_opts['merge_output_format'] = 'mp4'
            mimetype = 'video/mp4'
            ext = 'mp4'

        else:
            # උපරිම කොලිටිය (Premium)
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
            ydl_opts['merge_output_format'] = 'mp4'
            mimetype = 'video/mp4'
            ext = 'mp4'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        final_filepath = f"{base_path}.{ext}"
        
        # File එකක් හොයාගන්න බැරි වුණොත් Backup එකක් විදිහට පරීක්ෂා කිරීම
        if not os.path.exists(final_filepath):
            for f in os.listdir(DOWNLOAD_DIR):
                if safe_title in f:
                    final_filepath = os.path.join(DOWNLOAD_DIR, f)
                    break

        return send_file(final_filepath, as_attachment=True, download_name=f"{safe_title}.{ext}", mimetype=mimetype)

    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
