"""
Simple webhook receiver for testing the Telegram Monitor
Run this script to receive webhook data locally
"""

from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# Create directory for storing summaries
os.makedirs("summaries", exist_ok=True)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive webhook data from Telegram Monitor"""
    try:
        # Get the data
        data = request.json
        
        # Print to console
        print("\n=== Received Webhook Data ===")
        print(json.dumps(data, indent=2))
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"summaries/summary_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"Saved to {filename}")
        
        return jsonify({"status": "success", "saved_to": filename})
    
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("Starting webhook receiver on http://localhost:5000/webhook")
    print("Use this URL in your config.json webhook URL")
    app.run(host='0.0.0.0', port=5000, debug=True)
