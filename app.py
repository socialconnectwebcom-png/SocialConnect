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
        ydl_opts = {
            'quiet': True, 
            'no_warnings': True,
            'cookiefile': 'cookies.txt',
            'format': 'b'  # <-- FIX: Fetch කරන වෙලාවට Format Error එන එක නැවැත්තුවා
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

    # අමුතු අකුරු අයින් කරලා ෆයිල් එකේ නම හදාගන්නවා
    safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    if not safe_title:
        safe_title = "SocialConnect_Audio_Video"

    base_path = os.path.join(DOWNLOAD_DIR, safe_title)

    try:
        ydl_opts = {
            'outtmpl': f"{base_path}.%(ext)s",
            'quiet': True,
            'no_warnings': True,
            'cookiefile': 'cookies.txt'
        }

        if quality == 'audio':
            # Music වලට අදාළ කොටස
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': ext, 
                'preferredquality': '320', 
            }]
            mimetype = f'audio/{ext}'
            final_filepath = f"{base_path}.{ext}"
            download_filename = f"{safe_title}.{ext}"

        elif quality == 'normal':
            # Normal කොලිටිය 480p වලට සීමා කළා (Fallback 'b' එක්ක)
            ydl_opts['format'] = 'bestvideo[height<=480]+bestaudio/best[height<=480]/b'
            ydl_opts['merge_output_format'] = 'mp4'
            mimetype = 'video/mp4'
            final_filepath = f"{base_path}.mp4"
            download_filename = f"{safe_title}.mp4"

        else:
            # Premium - Format එක Fix කරා ඕනෑම එකක් Mp4 වලට Merge වෙන්න (Fallback 'b' එක්ක)
            ydl_opts['format'] = 'bestvideo+bestaudio/best/b'
            ydl_opts['merge_output_format'] = 'mp4'
            mimetype = 'video/mp4'
            final_filepath = f"{base_path}.mp4"
            download_filename = f"{safe_title}.mp4"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return send_file(
            final_filepath,
            as_attachment=True,
            download_name=download_filename,
            mimetype=mimetype
        )

    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
