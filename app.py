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
        ydl_opts = {'quiet': True, 'no_warnings': True, 'noplaylist': True}
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
    quality = request.args.get('quality', 'premium')

    if not url:
        return "URL is required", 400

    safe_title = "".join([c for c in title if c.isalnum() or c==' ']).strip()
    if not safe_title:
        safe_title = "SocialConnect_Media"

    try:
        ydl_opts = {
            'outtmpl': f"{DOWNLOAD_DIR}/{safe_title}.%(ext)s",
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True
        }

        if quality == 'audio':
            # 🎵 Music: High Quality 320kbps MP3
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }]
            ext = 'mp3'
            mimetype = 'audio/mpeg'
        
        elif quality == 'normal':
            # 📉 Normal Quality: 
            # මුලින්ම 480p හෝ ඊට අඩු එකක් හොයනවා. ඒක නැත්නම් තියෙන සවුත්තුම (worst) එක හොයනවා.
            # ඒ කිසිම දෙයක් නැතුව Pinterest වගේ සයිට් එකක තියෙන්නේ එකම එක ෆයිල් එකක් නම්, 
            # Error එකක් දෙන්නේ නැතුව ඒ තියෙන එකම ෆයිල් එක දෙනවා (/best).
            ydl_opts['format'] = 'best[height<=480]/worstvideo+worstaudio/worst/best'
            ydl_opts['merge_output_format'] = 'mp4'
            ext = 'mp4'
            mimetype = 'video/mp4'

        else:
            # 📈 Premium Quality: අනිවාර්යයෙන්ම උපරිම කොලිටිය
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
            ydl_opts['merge_output_format'] = 'mp4'
            ext = 'mp4'
            mimetype = 'video/mp4'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        final_path = f"{DOWNLOAD_DIR}/{safe_title}.{ext}"
        
        if os.path.exists(final_path):
            return send_file(final_path, as_attachment=True, download_name=f"{safe_title}.{ext}", mimetype=mimetype)
        else:
            for f in os.listdir(DOWNLOAD_DIR):
                if safe_title in f:
                    return send_file(os.path.join(DOWNLOAD_DIR, f), as_attachment=True)
            return "File not found", 404

    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
