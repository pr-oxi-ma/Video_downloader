import os
import base64
import tempfile
from flask import Flask, request, jsonify
import yt_dlp
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

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

        # Extract video-only formats
        video_formats = [
            f for f in info.get("formats", [])
            if f.get("vcodec") != "none" and f.get("acodec") == "none"
        ]

        # Extract audio-only formats
        audio_formats = [
            f for f in info.get("formats", [])
            if f.get("vcodec") == "none" and f.get("acodec") != "none"
        ]

        # Pick best audio format (by bitrate)
        best_audio = sorted(audio_formats, key=lambda x: x.get("abr", 0), reverse=True)[0] if audio_formats else None

        # Combine video+best audio
        merged_formats = []
        if best_audio:
            for vf in video_formats:
                merged_formats.append({
                    "format_id": f"{vf.get('format_id')}+{best_audio.get('format_id')}",
                    "ext": vf.get("ext"),
                    "height": vf.get("height"),
                    "width": vf.get("width"),
                    "fps": vf.get("fps"),
                    "video_note": vf.get("format_note"),
                    "video_url": vf.get("url"),
                    "audio_url": best_audio.get("url"),
                    "audio_ext": best_audio.get("ext"),
                    "note": "Merged video+audio stream (playback or merge supported)"
                })

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
            "audio_only": {
                "format_id": best_audio.get("format_id"),
                "ext": best_audio.get("ext"),
                "abr": best_audio.get("abr"),
                "filesize": best_audio.get("filesize"),
                "url": best_audio.get("url")
            } if best_audio else None,
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

# For Vercel serverless
def vercel_handler(event, context):
    from werkzeug.serving import run_simple
    def wsgi_app(environ, start_response):
        return app(environ, start_response)
    return run_simple('0.0.0.0', 5000, wsgi_app, use_reloader=False)
                
