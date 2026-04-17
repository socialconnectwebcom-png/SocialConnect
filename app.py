import os
import yt_dlp
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

TEMP_DIR = os.path.join(os.getcwd(), 'temp_downloads')
os.makedirs(TEMP_DIR, exist_ok=True)

@app.route('/api/get-video', methods=['POST'])
def get_video_info():
    data = request.json
    url = data.get('url')

    if not url: return jsonify({"error": "කරුණාකර නිවැරදි ලින්ක් එකක් ලබා දෙන්න."}), 400

    ydl_opts = { 'quiet': True, 'no_warnings': True, 'skip_download': True }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = [{"type": "video", "ext": "mp4"}, {"type": "audio", "ext": "m4a"}]

            return jsonify({
                "success": True,
                "title": info.get('title', 'SocialConnect Video'),
                "thumbnail": info.get('thumbnail', ''),
                "original_url": url, 
                "formats": formats
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/proxy-download', methods=['GET'])
def proxy_download():
    original_url = request.args.get('url')
    title = request.args.get('title', 'SocialConnect_Video')
    ext = request.args.get('ext', 'mp4')
    quality = request.args.get('quality', 'premium')

    if not original_url: return "No URL", 400

    safe_title = "".join([c for c in title if c.isalnum() or c in [' ', '-', '_']]).strip()
    if not safe_title: safe_title = "download"
    
    filepath = os.path.join(TEMP_DIR, f"{safe_title}.{ext}")

    ydl_opts = {
        'outtmpl': filepath,
        'quiet': True,
        'no_warnings': True,
        'ffmpeg_location': 'C:/ffmpeg/bin', 
    }

    if ext == 'mp4':
        ydl_opts['merge_output_format'] = 'mp4' 

        if quality == 'normal':
            # 🌟 Normal: 720p හෝ ඊට අඩු කොලිටියක් පමණක් ඉල්ලයි (File size එක අඩුවෙන්)
            ydl_opts['format'] = 'best[height<=720]/bestvideo[height<=720]+bestaudio/best'
        else:
            # 🌟 Premium: උපරිම කොලිටිය ඉල්ලයි (1080p, 2K, 4K)
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best'
    else:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['extract_audio'] = True
        ydl_opts['audio_format'] = ext

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([original_url])

        def generate_and_delete():
            with open(filepath, 'rb') as f:
                while chunk := f.read(10 * 1024 * 1024): 
                    yield chunk
            os.remove(filepath) 

        return Response(
            stream_with_context(generate_and_delete()),
            content_type='application/octet-stream', 
            headers={'Content-Disposition': f'attachment; filename="{safe_title}.{ext}"'}
        )
    except Exception as e:
        return f"Download Failed: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)