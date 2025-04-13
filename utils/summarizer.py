import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

from database.storage import Storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def generate_summary(storage: Storage) -> Dict[str, Any]:
    """Generate a summary of recent activity"""
    # Get data from the last hour
    since = datetime.now() - timedelta(hours=1)
    
    # Get overall stats
    stats = await storage.get_stats()
    
    # Get recent messages
    recent_messages = await storage.get_messages(since=since, limit=1000)
    
    # Group messages by group
    groups_data = {}
    for message in recent_messages:
        group_id = message["group_id"]
        if group_id not in groups_data:
            groups_data[group_id] = {
                "group_name": message["group_name"],
                "message_count": 0,
                "users": set(),
                "has_media_count": 0
            }
        
        groups_data[group_id]["message_count"] += 1
        if message["sender_id"]:
            groups_data[group_id]["users"].add(message["sender_id"])
        if message["has_media"]:
            groups_data[group_id]["has_media_count"] += 1
    
    # Convert to list and format
    groups_summary = []
    for group_id, data in groups_data.items():
        groups_summary.append({
            "group_id": group_id,
            "group_name": data["group_name"],
            "message_count": data["message_count"],
            "unique_users": len(data["users"]),
            "media_count": data["has_media_count"]
        })
    
    # Sort by message count
    groups_summary.sort(key=lambda x: x["message_count"], reverse=True)
    
    # Create summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "period_hours": 1,
        "total_messages": len(recent_messages),
        "groups": groups_summary,
        "overall_stats": {
            "total_messages_all_time": stats["total_messages"],
            "recent_activity_24h": stats["recent_activity"],
            "top_users": stats["top_users"][:5]  # Limit to top 5
        }
    }
    
    return summary
