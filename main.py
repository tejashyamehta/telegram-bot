import asyncio
import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
import json
import logging

from telegram_bot.bot import TelegramMonitor
from database.storage import get_storage
from utils.summarizer import generate_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("telegram_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
    global bot_instance
    
    if not bot_instance:
        return {"status": "not_running"}
    
    try:
        stats = await bot_instance.get_stats()
        return {
            "status": "running",
            "bot_name": bot_instance.name,
            "groups_monitored": len(bot_instance.groups),
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.post("/webhook")
async def set_webhook(webhook_data: WebhookData):
    """Set or update webhook configuration"""
    global bot_instance
    
    if not bot_instance:
        raise HTTPException(status_code=404, detail="Bot not running")
    
    try:
        await bot_instance.set_webhook(webhook_data.url, webhook_data.interval_minutes)
        return {"status": "webhook updated"}
    except Exception as e:
        logger.error(f"Error setting webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/launch")
async def launch_bot(config: BotConfig, background_tasks: BackgroundTasks):
    """Launch the Telegram monitoring bot"""
    global bot_instance
    
    if bot_instance:
        return {"status": "already_running", "name": bot_instance.name}
    
    try:
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
    except Exception as e:
        logger.error(f"Error launching bot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint with basic information"""
    return {
        "app": "Telegram Group Monitor",
        "endpoints": {
            "/ping": "Health check",
            "/status": "Bot status and statistics",
            "/launch": "Launch the bot (POST)",
            "/webhook": "Set webhook (POST)"
        },
        "status": "Bot is running" if bot_instance else "Bot is not running"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)}
    )

def launch_bot_from_config():
    """Launch the bot from the config file"""
    global bot_instance
    
    try:
        # Load config from file
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        if not os.path.exists(config_path):
            logger.error(f"Config file not found: {config_path}")
            return False
            
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Get the first bot from config
        bot_name = next(iter(config.get("bots", {})))
        bot_config = config["bots"][bot_name]
        
        # Create storage
        storage = get_storage()
        
        # Create bot instance
        bot_instance = TelegramMonitor(
            name=bot_name,
            api_id=bot_config["api_id"],
            api_hash=bot_config["api_hash"],
            phone=bot_config["phone"],
            groups=bot_config["groups"],
            storage=storage
        )
        
        # Set webhook if configured
        if "webhook" in bot_config:
            asyncio.run(bot_instance.set_webhook(
                bot_config["webhook"]["url"],
                bot_config["webhook"]["interval_minutes"]
            ))
        
        # Start the bot
        asyncio.create_task(bot_instance.start())
        
        return True
    except Exception as e:
        logger.error(f"Error launching bot from config: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    # Check if a bot name was provided
    if len(sys.argv) > 1:
        bot_name = sys.argv[1]
        logger.info(f"Starting bot {bot_name} from command line")
        
        # Load config and start the bot
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(config_path, "r") as f:
            config = json.load(f)
        
        if bot_name not in config.get("bots", {}):
            logger.error(f"Bot {bot_name} not found in config")
            sys.exit(1)
        
        # Start the API server with the bot
        host = config.get("host", "127.0.0.1")
        port = config.get("port", 8000)
        
        logger.info(f"Starting API server on {host}:{port}")
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            log_level="info"
        )
    else:
        # Start API server only
        logger.info("Starting API server only")
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )
