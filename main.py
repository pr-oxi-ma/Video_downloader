import json
from flask import Flask, request, jsonify
import yt_dlp
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

@app.route('/')
def home():
    return jsonify({
        "message": "📥 Social Media Downloader API (Vercel)",
        "usage": "https://your-vercel-app.vercel.app/api?url=https://example.com/video",
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
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'forcejson': True,
            'nocheckcertificate': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

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
            "note": "Some platforms like TikTok or Drive may block or rate-limit. Try using a proxy or check if login is required.",
            "credits": {
                "telegram": "@Kaiiddo",
                "youtube": "@Kaiiddo",
                "bugs": "DiscussionxGroup"
            }
        }), 500

# This is required for Vercel to work with Flask
def vercel_handler(event, context):
    from werkzeug.wrappers import Request, Response
    from werkzeug.serving import run_simple

    def wsgi_app(environ, start_response):
        return app(environ, start_response)

    return run_simple(
        '0.0.0.0',
        5000,
        wsgi_app,
        use_reloader=False,
        use_debugger=False,
        use_evalex=False
    )