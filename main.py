import os
import base64
import tempfile
from flask import Flask, request, jsonify
import yt_dlp
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

def merge_video_audio(info):
    """Ensure all formats have both video and audio"""
    merged_formats = []
    video_formats = [f for f in info.get('formats', []) if f.get('vcodec') != 'none']
    audio_formats = [f for f in info.get('formats', []) if f.get('acodec') != 'none']
    
    for v_format in video_formats:
        # Skip if already has audio
        if v_format.get('acodec') != 'none':
            merged_formats.append(v_format)
            continue
            
        # Find compatible audio format
        best_audio = None
        for a_format in audio_formats:
            # Match by extension/container when possible
            if (a_format.get('ext') == v_format.get('ext') or 
                (a_format.get('container') == v_format.get('container'))):
                best_audio = a_format
                break
                
        if not best_audio:
            # Fallback to any audio format
            best_audio = audio_formats[0] if audio_formats else None
            
        if best_audio:
            # Create merged format entry
            merged = {
                **v_format,
                'acodec': best_audio['acodec'],
                'audio_ext': best_audio.get('audio_ext', best_audio.get('ext')),
                'url': f"{v_format['url']}+{best_audio['url']}",
                'format_note': f"{v_format.get('format_note', '')}+audio",
                'format': f"{v_format.get('format', '')}+{best_audio.get('format', '')}",
                'filesize_approx': (v_format.get('filesize_approx', 0) + 
                                   best_audio.get('filesize_approx', 0)),
                'requested_formats': [v_format, best_audio]
            }
            merged_formats.append(merged)
            
    return merged_formats

@app.route('/')
def home():
    domain = request.host_url.rstrip('/')
    return jsonify({
        "message": "📥 Social Media Downloader API (Vercel)",
        "usage": f"{domain}/api?url=https://example.com/video",
        "powered_by": "yt-dlp",
        "credits": {
            "telegram": "@Kaiiddo",
            "youtube": "@Kaiiddo",
            "bugs": "DiscussionxGroup"
        }
    })

@app.route('/api')
def download():
    url = request.args.get('url')
    if not url:
        return jsonify({
            "status": "error",
            "message": "Missing 'url' parameter. Use /api?url=VIDEO_URL",
            "credits": {
                "telegram": "@Kaiiddo",
                "youtube": "@Kaiiddo",
                "bugs": "DiscussionxGroup"
            }
        }), 400

    try:
        cookies_env = os.getenv('COOKIES_TXT')
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'forcejson': True,
            'nocheckcertificate': True,
            'extract_flat': False,
        }

        if cookies_env:
            try:
                cookies_decoded = base64.b64decode(cookies_env).decode('utf-8')
            except:
                cookies_decoded = cookies_env
            
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as f:
                f.write(cookies_decoded)
                cookies_path = f.name
            ydl_opts['cookiefile'] = cookies_path

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if cookies_env and 'cookies_path' in locals() and os.path.exists(cookies_path):
            os.unlink(cookies_path)

        # Process formats to ensure all have audio
        merged_formats = merge_video_audio(info)

        data = {
            "id": info.get("id"),
            "title": info.get("title"),
            "uploader": info.get("uploader"),
            "uploader_id": info.get("uploader_id"),
            "channel": info.get("channel"),
            "duration": info.get("duration"),
            "view_count": info.get("view_count"),
            "webpage_url": info.get("webpage_url"),
            "formats": merged_formats,
            "thumbnails": info.get("thumbnails", []),
            "credits": {
                "telegram": "@Kaiiddo",
                "youtube": "@Kaiiddo",
                "bugs": "DiscussionxGroup"
            }
        }

        return jsonify(data)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "note": "Some platforms may block requests. Ensure cookies are valid if used.",
            "credits": {
                "telegram": "@Kaiiddo",
                "youtube": "@Kaiiddo",
                "bugs": "DiscussionxGroup"
            }
        }), 500

def vercel_handler(event, context):
    from werkzeug.serving import run_simple
    def wsgi_app(environ, start_response):
        return app(environ, start_response)
    return run_simple('0.0.0.0', 5000, wsgi_app, use_reloader=False)
