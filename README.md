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
- SQLite (or Redis)
- aiohttp

## Installation

1. Clone the repository:
\`\`\`bash
git clone https://github.com/yourusername/telegram-monitor.git
cd telegram-monitor
\`\`\`

2. Install dependencies:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

3. Configure the application:
   - Edit `config.json` with your Telegram API credentials and group list
   - Set your webhook URL if needed

## Usage

### Starting the Bot

You can start the bot in two ways:

1. Using the command line:
\`\`\`bash
python main.py Luna
\`\`\`

2. Using the API:
\`\`\`bash
python main.py
\`\`\`

Then make a POST request to `/launch` with the bot configuration.

### API Endpoints

- `GET /ping`: Health check endpoint
- `GET /status`: Get current monitoring status and statistics
- `POST /webhook`: Set or update webhook configuration
- `POST /launch`: Launch the Telegram monitoring bot

### Programmatic Usage

```python
from main import launch_bot

# Launch the bot with a specific name (defined in config.json)
launch_bot("LunastalkerBot")
