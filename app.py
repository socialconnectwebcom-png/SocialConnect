from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

# ඩවුන්ලෝඩ් වෙන ෆයිල්ස් තියාගන්න ෆෝල්ඩර් එක
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
        # Fetch කරද්දී එරර් එන්නේ නැති වෙන්න සරලම විදිහට හැදුවා
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

    # ෆයිල් නමේ තියෙන අමුතු අකුරු අයින් කරලා ලස්සනට හදාගන්නවා
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
            # Audio ඩවුන්ලෝඩ් කිරීම (Mp3)
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': ext,
                'preferredquality': '320',
            }]
            
        elif quality == 'normal':
            # 480p Normal කොලිටිය - Codec අවුල් නැතිව MP4 විදිහට ඉල්ලනවා
            ydl_opts['format'] = 'bestvideo[height<=480][vcodec^=avc]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best'
            ydl_opts['merge_output_format'] = 'mp4'
            
        else:
            # Premium කොලිටිය - හැමෝටම ප්ලේ වෙන සාමාන්‍ය MP4 (H.264) එක ඉල්ලනවා (AV1 එරර් එක ෆික්ස් කරා)
            ydl_opts['format'] = 'bestvideo[vcodec^=avc]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            ydl_opts['merge_output_format'] = 'mp4'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # ඩවුන්ලෝඩ් වුණ ෆයිල් එක හරියටම හොයාගන්නවා
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
