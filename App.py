import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# A list of completely different public servers. If one fails, your app tries the next!
FALLBACK_NODES = [
    "https://inv.tux.digital",
    "https://yewtu.be",
    "https://invidious.nerdvpn.de",
    "https://invidious.flokinet.to",
    "https://iv.melmac.space"
]

def get_working_nodes():
    try:
        # Ask the global registry for active servers
        res = requests.get("https://api.invidious.io/instances.json?sort_by=type,api,users", timeout=3)
        if res.status_code == 200:
            instances = res.json()
            valid_urls = []
            for inst in instances:
                data = inst[1]
                # Check if the server's API is on and it isn't marked as 'down'
                if data.get("api") and data.get("type") == "https" and not data.get("monitor", {}).get("down"):
                    valid_urls.append(data.get("uri"))
            if valid_urls:
                return valid_urls
    except Exception:
        pass
    return FALLBACK_NODES

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Missing search query"}), 400
        
    nodes = get_working_nodes()
    
    # Try up to 4 different community servers until one responds successfully
    for node in nodes[:4]: 
        search_endpoint = f"{node}/api/v1/search"
        try:
            print(f"Trying community node: {node}")
            response = requests.get(search_endpoint, params={"q": query, "type": "video"}, timeout=4)
            if response.status_code == 200:
                raw_results = response.json()
                
                processed_videos = []
                for video in raw_results[:5]:
                    if video.get("type") == "video":
                        processed_videos.append({
                            "title": video.get("title"),
                            "videoId": video.get("videoId"),
                            "author": video.get("author"),
                            "description": video.get("description", "")[:150] + "..."
                        })
                return jsonify(processed_videos)
        except Exception:
            print(f"Node {node} failed/timed out. Moving to next...")
            continue 
            
    return jsonify({"error": "All public nodes are busy right now."}), 502

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
