import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
# This allows your frontend website to talk to this Python backend without CORS blocks
CORS(app)

FALLBACK_INSTANCE = "https://iv.melmac.space"

def get_working_instance():
    try:
        res = requests.get("https://api.invidious.io/instances.json?sort_by=type,api,users", timeout=3)
        instances = res.json()
        for inst in instances:
            data = inst[1]
            if data.get("api") and data.get("type") == "https":
                return data.get("uri")
    except Exception:
        return FALLBACK_INSTANCE
    return FALLBACK_INSTANCE

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Missing search query"}), 400
        
    instance_url = get_working_instance()
    search_endpoint = f"{instance_url}/api/v1/search"
    
    try:
        # Python server fetches the data seamlessly
        response = requests.get(search_endpoint, params={"q": query, "type": "video"}, timeout=5)
        if response.status_code == 200:
            raw_results = response.json()
            
            # Clean up the data to send only what your web app needs
            processed_videos = []
            for video in raw_results[:5]:
                processed_videos.append({
                    "title": video.get("title"),
                    "videoId": video.get("videoId"),
                    "author": video.get("author"),
                    "description": video.get("description", "")[:150] + "..."
                })
            return jsonify(processed_videos)
        else:
            return jsonify({"error": "Community node busy"}), 502
    except Exception as e:
        return jsonify({"error": "Network timeout, try again"}), 500

if __name__ == '__main__':
    # Run on the port assigned by the cloud provider
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)