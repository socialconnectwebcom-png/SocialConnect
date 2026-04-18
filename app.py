from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

# Temporary folder to store downloaded files
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
        ydl_opts = {'quiet': True, 'no_warnings': True}
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

    # අමුතු අකුරු අයින් කරලා ෆයිල් එකේ නම හදාගන්නවා (Crash වීම නවත්වන්න)
    safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    if not safe_title:
        safe_title = "SocialConnect_Video"
        
    filename = f"{safe_title}.{ext}"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    try:
        ydl_opts = {
            'outtmpl': filepath,
            'quiet': True,
            'no_warnings': True,
        }

        # Quality එක අනුව යන්න ඕනේ විදිහ තීරණය කිරීම (අලුත්ම ලොජික් එක)
        if quality == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': ext,
                'preferredquality': '192',
            }]
            mimetype = f'audio/{ext}'
            
        elif quality == 'normal':
            # Normal වලදී: තියෙන එකක් අරන් අනිවාර්යයෙන්ම MP4 කරනවා (Error එන්නේ නෑ)
            ydl_opts['format'] = 'best[ext=mp4]/best[ext=webm]/best/bv+ba/b' 
            ydl_opts['merge_output_format'] = 'mp4'
            mimetype = 'video/mp4'
            
        else: 
            # Premium වලදී: උපරිම කොලිටිය (4K/1080p) තියෙන වීඩියෝව සහ හොඳම ඕඩියෝව එකතු කරනවා
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best/bv*+ba*' 
            ydl_opts['merge_output_format'] = 'mp4'
            mimetype = 'video/mp4'

        # වීඩියෝ එක සර්වර් එකට ඩවුන්ලෝඩ් කිරීම
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # ඩවුන්ලෝඩ් වුණ ෆයිල් එක පීසී එකට යැවීම
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )

    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
