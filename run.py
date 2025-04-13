"""
Helper script to run the Telegram Monitor
"""

import os
import sys
import json
import subprocess
import webbrowser
import time

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import telethon
        import fastapi
        import uvicorn
        import aiohttp
        print("✅ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return False

def check_config():
    """Check if config.json exists and is valid"""
    if not os.path.exists("config.json"):
        print("❌ config.json not found")
        return False
    
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        
        if "bots" not in config or not config["bots"]:
            print("❌ No bots defined in config.json")
            return False
        
        # Check first bot config
        bot_name = next(iter(config["bots"]))
        bot_config = config["bots"][bot_name]
        
        required_fields = ["api_id", "api_hash", "phone", "groups"]
        for field in required_fields:
            if field not in bot_config:
                print(f"❌ Missing required field '{field}' in bot config")
                return False
        
        # Check placeholder values
        if bot_config["api_hash"] == "your_api_hash_here":
            print("❌ Please replace 'your_api_hash_here' with your actual API hash")
            return False
        
        if bot_config["phone"] == "+1234567890":
            print("❌ Please replace '+1234567890' with your actual phone number")
            return False
        
        if "webhook" in bot_config and "url" in bot_config["webhook"]:
            if "webhook.site/your-unique-id" in bot_config["webhook"]["url"]:
                print("❌ Please replace the webhook URL with your actual webhook URL")
                return False
        
        print("✅ Config file is valid")
        return True
    
    except json.JSONDecodeError:
        print("❌ config.json is not valid JSON")
        return False
    except Exception as e:
        print(f"❌ Error checking config: {str(e)}")
        return False

def start_webhook_server():
    """Start the webhook server in a separate process"""
    print("Starting webhook server...")
    subprocess.Popen([sys.executable, "utils/webhook_server.py"])
    time.sleep(2)  # Give it time to start
    
    # Open the webhook URL in a browser
    webbrowser.open("http://localhost:5000/webhook")
    
    print("Webhook server started at http://localhost:5000/webhook")
    print("Update your config.json to use this URL if needed")

def start_telegram_monitor():
    """Start the Telegram Monitor"""
    print("Starting Telegram Monitor...")
    
    # Get the first bot name from config
    with open("config.json", "r") as f:
        config = json.load(f)
    
    bot_name = next(iter(config["bots"]))
    
    # Start the monitor
    subprocess.run([sys.executable, "main.py", bot_name])

def main():
    """Main function"""
    print("=== Telegram Group Monitor Setup ===")
    
    # Check dependencies
    if not check_dependencies():
        print("Please restart the script after dependencies are installed")
        return
    
    # Check config
    if not check_config():
        print("Please fix the config.json file and try again")
        return
    
    # Ask if user wants to start webhook server
    start_webhook = input("Do you want to start a local webhook server? (y/n): ").lower() == 'y'
    
    if start_webhook:
        start_webhook_server()
        
        # Update config to use local webhook
        with open("config.json", "r") as f:
            config = json.load(f)
        
        bot_name = next(iter(config["bots"]))
        
        if "webhook" not in config["bots"][bot_name]:
            config["bots"][bot_name]["webhook"] = {}
        
        config["bots"][bot_name]["webhook"]["url"] = "http://localhost:5000/webhook"
        config["bots"][bot_name]["webhook"]["interval_minutes"] = 5  # Shorter interval for testing
        
        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print("Updated config.json with local webhook URL")
    
    # Start the monitor
    start_telegram_monitor()

if __name__ == "__main__":
    main()
