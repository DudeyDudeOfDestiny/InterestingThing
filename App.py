import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# A robust list of premium, high-uptime public fallback instances
FALLBACK_INSTANCES = [
    "https://inv.tux.digital",
    "https://yewtu.be",
    "https://invidious.nerdvpn.de",
    "https://iv.melmac.space",
    "https://invidious.flokinet.to"
]

def get_working_instances():
    """Fetches public nodes from the registry, falling back to a hardcoded list on failure."""
    try:
        res = requests.get("https://api.invidious.io/instances.json?sort_by=type,api,users", timeout=4)
        if res.status_code == 200:
            instances = res.json()
            valid_urls = []
            for inst in instances:
                data = inst[1]
                if data.get("api") and data.get("type") == "https" and not data.get("monitor", {}).get("down"):
                    valid_urls.append(data.get("uri"))
            if valid_urls:
                return valid_urls
    except Exception:
        pass
    return FALLBACK_INSTANCES

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Missing search query"}), 400
        
    nodes = get_working_instances()
    
    # Cycle through nodes sequentially until one successfully returns data
    for node in nodes[:4]: 
        search_endpoint = f"{node}/api/v1/search"
        try:
            response = requests.get(search_endpoint, params={"q": query, "type": "video"}, timeout=4)
            if response.status_code == 200:
                raw_results = response.json()
                
                processed_videos = []
                for video in raw_results[:5]:
                    if video.get("type") == "video":  # Filter out channels/playlists
                        processed_videos.append({
                            "title": video.get("title"),
                            "videoId": video.get("videoId"),
                            "author": video.get("author"),
                            "description": video.get("description", "")[:150] + "..."
                        })
                return jsonify(processed_videos)
        except Exception:
            continue # If a node times out, skip to the next healthy one seamlessly
            
    return jsonify({"error": "All public community nodes are currently congested. Try again in a moment."}), 502

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
