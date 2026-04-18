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

        # Quality එක අනුව යන්න ඕනේ විදිහ තීරණය කිරීම
        if quality == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': ext,
                'preferredquality': '192',
            }]
            mimetype = f'audio/{ext}'
            
        elif quality == 'normal':
            # ffmpeg නැතුව ගන්න පුළුවන් හොඳම තනි ෆයිල් එක
            ydl_opts['format'] = 'b' 
            mimetype = 'video/mp4'
            
        else: 
            # Premium - වීඩියෝ එකයි ඕඩියෝ එකයි ffmpeg වලින් එකතු කරනවා
            ydl_opts['format'] = 'bv*+ba/b' 
            mimetype = 'video/mp4'

        # වීඩියෝ එක සර්වර් එකට ඩවුන්ලෝඩ් කිරීම
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # ඩවුන්ලෝඩ් වුණ ෆයිල් එක පීසී එකට යැවීම (නම සහ Format එකත් එක්ක)
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
