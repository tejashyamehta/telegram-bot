import asyncio
import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from telegram_bot.bot import TelegramMonitor
from database.storage import get_storage
from utils.summarizer import generate_summary

app = FastAPI(title="Telegram Group Monitor")

# Global bot instance
bot_instance = None

class WebhookData(BaseModel):
    url: str
    interval_minutes: int = 60

class BotConfig(BaseModel):
    name: str
    api_id: int
    api_hash: str
    phone: str
    groups: List[str]
    webhook: Optional[WebhookData] = None

@app.get("/ping")
async def ping():
    """Health check endpoint"""
    return {"status": "ok", "service": "telegram-monitor"}

@app.get("/status")
async def status():
    """Get current monitoring status"""
    if not bot_instance:
        raise HTTPException(status_code=404, detail="Bot not running")
    
    stats = await bot_instance.get_stats()
    return {
        "status": "running",
        "bot_name": bot_instance.name,
        "groups_monitored": len(bot_instance.groups),
        "stats": stats
    }

@app.post("/webhook")
async def set_webhook(webhook_data: WebhookData):
    """Set or update webhook configuration"""
    if not bot_instance:
        raise HTTPException(status_code=404, detail="Bot not running")
    
    await bot_instance.set_webhook(webhook_data.url, webhook_data.interval_minutes)
    return {"status": "webhook updated"}

@app.post("/launch")
async def launch_bot(config: BotConfig, background_tasks: BackgroundTasks):
    """Launch the Telegram monitoring bot"""
    global bot_instance
    
    if bot_instance:
        return {"status": "already_running", "name": bot_instance.name}
    
    # Initialize storage
    storage = get_storage()
    
    # Initialize and start the bot
    bot_instance = TelegramMonitor(
        name=config.name,
        api_id=config.api_id,
        api_hash=config.api_hash,
        phone=config.phone,
        groups=config.groups,
        storage=storage
    )
    
    # Set webhook if provided
    if config.webhook:
        await bot_instance.set_webhook(
            config.webhook.url, 
            config.webhook.interval_minutes
        )
    
    # Start the bot in the background
    background_tasks.add_task(bot_instance.start)
    
    return {
        "status": "starting",
        "name": config.name,
        "groups": len(config.groups)
    }

def launch_bot(name: str):
    """Function to launch the bot programmatically"""
    import json
    import os
    
    # Load config from file
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Start the API server
    uvicorn.run(
        "main:app",
        host=config.get("host", "0.0.0.0"),
        port=config.get("port", 8000),
        reload=False
    )

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Launch with name from command line
        launch_bot(sys.argv[1])
    else:
        # Start API server only
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )
