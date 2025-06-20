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
    domain = request.host_url.rstrip('/')  # Dynamically get current domain
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
        # Load cookies from environment variable (supports base64 or raw text)
        cookies_env = os.getenv('COOKIES_TXT')
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'forcejson': True,
            'nocheckcertificate': True,
        }

        if cookies_env:
            try:
                # Try decoding as base64 (common for binary files)
                cookies_decoded = base64.b64decode(cookies_env).decode('utf-8')
            except:
                cookies_decoded = cookies_env  # Fallback to raw text
            
            # Save to a temporary file
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as f:
                f.write(cookies_decoded)
                cookies_path = f.name
            ydl_opts['cookiefile'] = cookies_path

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # Clean up cookies file if it exists
        if cookies_env and 'cookies_path' in locals() and os.path.exists(cookies_path):
            os.unlink(cookies_path)

        data = {
            "id": info.get("id"),
            "title": info.get("title"),
            "uploader": info.get("uploader"),
            "uploader_id": info.get("uploader_id"),
            "channel": info.get("channel"),
            "duration": info.get("duration"),
            "view_count": info.get("view_count"),
            "webpage_url": info.get("webpage_url"),
            "formats": info.get("formats", []),
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

# Vercel serverless compatibility
def vercel_handler(event, context):
    from werkzeug.serving import run_simple
    def wsgi_app(environ, start_response):
        return app(environ, start_response)
    return run_simple('0.0.0.0', 5000, wsgi_app, use_reloader=False)