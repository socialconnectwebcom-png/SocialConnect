import os
import yt_dlp
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
# CORS එක මෙන්න මෙහෙම හරියටම දෙන්න
CORS(app, resources={r"/*": {"origins": "*"}}) 

TEMP_DIR = os.path.join(os.getcwd(), 'temp_downloads')
os.makedirs(TEMP_DIR, exist_ok=True)

@app.route('/fetch-video', methods=['POST', 'OPTIONS']) # OPTIONS එකත් එකතු කළා
def get_video_info():
    if request.method == 'OPTIONS':
        return Response(status=200)
        
    data = request.json
    url = data.get('url')

    if not url: return jsonify({"error": "No URL provided"}), 400

    ydl_opts = { 'quiet': True, 'no_warnings': True, 'skip_download': True }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "success": True,
                "title": info.get('title', 'Video'),
                "thumbnail": info.get('thumbnail', ''),
                "original_url": url
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download', methods=['GET'])
def proxy_download():
    original_url = request.args.get('url')
    title = request.args.get('title', 'video')
    ext = request.args.get('ext', 'mp4')
    quality = request.args.get('quality', 'premium')

    if not original_url: return "No URL", 400

    safe_title = "".join([c for c in title if c.isalnum() or c in [' ', '-', '_']]).strip()
    filepath = os.path.join(TEMP_DIR, f"{safe_title}.{ext}")

    ydl_opts = { 'outtmpl': filepath, 'quiet': True, 'no_warnings': True }

    if ext == 'mp4':
        ydl_opts['merge_output_format'] = 'mp4' 
        if quality == 'normal':
            ydl_opts['format'] = 'best[height<=720]/best'
        else:
            ydl_opts['format'] = 'bestvideo+bestaudio/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([original_url])

        def generate():
            with open(filepath, 'rb') as f:
                while chunk := f.read(1024 * 1024): yield chunk
            os.remove(filepath)

        return Response(stream_with_context(generate()), content_type='application/octet-stream')
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
