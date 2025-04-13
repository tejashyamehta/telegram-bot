# Telegram Group Monitor

A backend system for passively monitoring public Telegram groups and logging their activity.

## Features

- Autonomously joins public Telegram groups
- Passively observes message flow without replying
- Logs messages and metadata (group name, sender ID, timestamp, content)
- Periodically generates and sends summaries to a webhook
- FastAPI backend with health check and status endpoints

## Requirements

- Python 3.10+
- Telethon
- FastAPI
- SQLite
- aiohttp

## Quick Start

The easiest way to get started is to use the helper script:

\`\`\`bash
python run.py
\`\`\`

This script will:
1. Check if all dependencies are installed
2. Validate your configuration
3. Optionally start a local webhook server for testing
4. Start the Telegram Monitor

## Manual Setup

### 1. Install Dependencies

\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 2. Configure the Application

Edit `config.json` with your Telegram API credentials:

\`\`\`json
{
  "host": "127.0.0.1",
  "port": 8000,
  "bots": {
    "YourBotName": {
      "api_id": YOUR_API_ID,
      "api_hash": "YOUR_API_HASH",
      "phone": "+1234567890",
      "groups": ["@group1", "@group2"],
      "webhook": {
        "url": "https://your-webhook-url.com/endpoint",
        "interval_minutes": 60
      }
    }
  }
}
\`\`\`

### 3. Get Telegram API Credentials

1. Go to https://my.telegram.org/apps
2. Create a new application
3. Note your `api_id` and `api_hash`
4. Add these to your config.json file

### 4. Running the Application

Start the application with your bot name:

\`\`\`bash
python main.py YourBotName
\`\`\`

The first time you run it, you'll need to enter the verification code sent to your Telegram account.

## Testing with a Local Webhook

For testing, you can use the included webhook server:

\`\`\`bash
python utils/webhook_server.py
\`\`\`

This starts a simple Flask server at http://localhost:5000/webhook that receives and logs webhook data.

Update your config.json to use this URL:

\`\`\`json
"webhook": {
  "url": "http://localhost:5000/webhook",
  "interval_minutes": 5
}
\`\`\`

## API Endpoints

- `GET /`: Basic information about the API
- `GET /ping`: Health check endpoint
- `GET /status`: Get current monitoring status and statistics
- `POST /webhook`: Set or update webhook configuration
- `POST /launch`: Launch the Telegram monitoring bot

## Accessing the API

The API runs on http://127.0.0.1:8000 by default. You can access it in your browser or using tools like curl:

\`\`\`bash
# Check status
curl http://127.0.0.1:8000/status

# Launch the bot
curl -X POST http://127.0.0.1:8000/launch -H "Content-Type: application/json" -d '{
  "name": "YourBotName",
  "api_id": 12345,
  "api_hash": "your_api_hash",
  "phone": "+1234567890",
  "groups": ["@group1", "@group2"]
}'
\`\`\`

## Logs and Data

- Logs are stored in `telegram_monitor.log`
- Message data is stored in `telegram_monitor.db` (SQLite database)
- If using the local webhook server, summaries are stored in the `summaries` directory

## Troubleshooting

### Common Issues

1. **Authentication Error**:
   - Make sure your API ID and hash are correct
   - Ensure your phone number is in the correct format (with country code)

2. **Group Joining Issues**:
   - Ensure the group usernames are correct (with @ symbol)
   - Make sure the groups are public

3. **Webhook Errors**:
   - Verify your webhook URL is accessible
   - Check the logs for any webhook-related errors

4. **Can't Access API**:
   - Make sure you're using http://127.0.0.1:8000 (not 0.0.0.0)
   - Check if the server is running with `ps aux | grep main.py`

### Getting Help

If you encounter issues:
1. Check the log file: `cat telegram_monitor.log`
2. Make sure all dependencies are installed: `pip install -r requirements.txt`
3. Verify your config.json is correctly formatted

## License

MIT
