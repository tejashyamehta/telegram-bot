import sqlite3
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Storage:
    """Abstract base class for storage implementations"""
    
    async def store_message(
        self,
        group_id: int,
        group_name: str,
        sender_id: Optional[int],
        sender_name: Optional[str],
        message_id: int,
        content: str,
        timestamp: datetime,
        has_media: bool
    ) -> None:
        """Store a message in the database"""
        raise NotImplementedError
    
    async def get_messages(
        self,
        group_id: Optional[int] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get messages from the database"""
        raise NotImplementedError
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored messages"""
        raise NotImplementedError

class SQLiteStorage(Storage):
    """SQLite implementation of the storage interface"""
    
    def __init__(self, db_path: str = "telegram_monitor.db"):
        self.db_path = db_path
        self.conn = None
        self._setup_db()
    
    def _setup_db(self):
        """Set up the SQLite database"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Create messages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            group_name TEXT NOT NULL,
            sender_id INTEGER,
            sender_name TEXT,
            message_id INTEGER NOT NULL,
            content TEXT,
            timestamp TEXT NOT NULL,
            has_media BOOLEAN NOT NULL
        )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_group_timestamp 
        ON messages (group_id, timestamp)
        ''')
        
        self.conn.commit()
    
    async def store_message(
        self,
        group_id: int,
        group_name: str,
        sender_id: Optional[int],
        sender_name: Optional[str],
        message_id: int,
        content: str,
        timestamp: datetime,
        has_media: bool
    ) -> None:
        """Store a message in the SQLite database"""
        # Run in a thread pool to avoid blocking
        await asyncio.to_thread(
            self._store_message_sync,
            group_id,
            group_name,
            sender_id,
            sender_name,
            message_id,
            content,
            timestamp,
            has_media
        )
    
    def _store_message_sync(
        self,
        group_id: int,
        group_name: str,
        sender_id: Optional[int],
        sender_name: Optional[str],
        message_id: int,
        content: str,
        timestamp: datetime,
        has_media: bool
    ) -> None:
        """Synchronous version of store_message"""
        cursor = self.conn.cursor()
        cursor.execute(
            '''
            INSERT INTO messages (
                group_id, group_name, sender_id, sender_name,
                message_id, content, timestamp, has_media
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                group_id, group_name, sender_id, sender_name,
                message_id, content, timestamp.isoformat(), has_media
            )
        )
        self.conn.commit()
    
    async def get_messages(
        self,
        group_id: Optional[int] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get messages from the SQLite database"""
        # Run in a thread pool to avoid blocking
        return await asyncio.to_thread(
            self._get_messages_sync,
            group_id,
            since,
            limit
        )
    
    def _get_messages_sync(
        self,
        group_id: Optional[int] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Synchronous version of get_messages"""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM messages"
        params = []
        
        # Add filters
        conditions = []
        if group_id is not None:
            conditions.append("group_id = ?")
            params.append(group_id)
        
        if since is not None:
            conditions.append("timestamp >= ?")
            params.append(since.isoformat())
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Add order and limit
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        
        # Convert to list of dictionaries
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored messages"""
        # Run in a thread pool to avoid blocking
        return await asyncio.to_thread(self._get_stats_sync)
    
    def _get_stats_sync(self) -> Dict[str, Any]:
        """Synchronous version of get_stats"""
        cursor = self.conn.cursor()
        
        # Get total message count
        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]
        
        # Get message count per group
        cursor.execute(
            """
            SELECT group_id, group_name, COUNT(*) as count
            FROM messages
            GROUP BY group_id
            ORDER BY count DESC
            """
        )
        groups = [
            {"group_id": row[0], "group_name": row[1], "message_count": row[2]}
            for row in cursor.fetchall()
        ]
        
        # Get most active users
        cursor.execute(
            """
            SELECT sender_id, sender_name, COUNT(*) as count
            FROM messages
            WHERE sender_id IS NOT NULL
            GROUP BY sender_id
            ORDER BY count DESC
            LIMIT 10
            """
        )
        users = [
            {"sender_id": row[0], "sender_name": row[1], "message_count": row[2]}
            for row in cursor.fetchall()
        ]
        
        # Get recent activity (last 24 hours)
        cursor.execute(
            """
            SELECT COUNT(*) FROM messages
            WHERE timestamp >= datetime('now', '-1 day')
            """
        )
        recent_activity = cursor.fetchone()[0]
        
        return {
            "total_messages": total_messages,
            "groups": groups,
            "top_users": users,
            "recent_activity": recent_activity
        }

def get_storage(storage_type: str = "sqlite", **kwargs) -> Storage:
    """Factory function to get a storage instance"""
    if storage_type.lower() == "sqlite":
        db_path = kwargs.get("db_path", "telegram_monitor.db")
        return SQLiteStorage(db_path)
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")
