import os
import yt_dlp
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

TEMP_DIR = os.path.join(os.getcwd(), 'temp_downloads')
os.makedirs(TEMP_DIR, exist_ok=True)

# රවුට් එක /fetch-video විදිහට හැදුවා (Netlify එකේ කෝඩ් එකට ගැලපෙන්න)
@app.route('/fetch-video', methods=['POST'])
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

# රවුට් එක /download විදිහට හැදුවා
@app.route('/download', methods=['GET'])
def proxy_download():
    original_url = request.args.get('url')
    title = request.args.get('title', 'SocialConnect_Video')
    ext = request.args.get('ext', 'mp4')
    quality = request.args.get('quality', 'premium')

    if not original_url: return "No URL", 400

    safe_title = "".join([c for c in title if c.isalnum() or c in [' ', '-', '_']]).strip()
    if not safe_title: safe_title = "download"
    
    filepath = os.path.join(TEMP_DIR, f"{safe_title}.{ext}")

    # C:/ ඩ්‍රයිව් එක අයින් කරා, එතකොට Railway එකේ ඔටෝ FFmpeg හොයාගන්නවා
    ydl_opts = {
        'outtmpl': filepath,
        'quiet': True,
        'no_warnings': True,
    }

    if ext == 'mp4':
        ydl_opts['merge_output_format'] = 'mp4' 

        if quality == 'normal':
            ydl_opts['format'] = 'best[height<=720]/bestvideo[height<=720]+bestaudio/best'
        else:
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
            try:
                os.remove(filepath) 
            except:
                pass

        return Response(
            stream_with_context(generate_and_delete()),
            content_type='application/octet-stream', 
            headers={'Content-Disposition': f'attachment; filename="{safe_title}.{ext}"'}
        )
    except Exception as e:
        return f"Download Failed: {str(e)}", 500

if __name__ == '__main__':
    # Railway එකට සම්බන්ධ වෙන්න host='0.0.0.0' අනිවාර්යයි!
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
