import os
from dotenv import load_dotenv

load_dotenv()

# fstream

_rabbit_url = os.environ.get('RABBIT_URL')
if not _rabbit_url:
    raise RuntimeError('RABBIT_URL is not configured — set it in .env or environment')
rabbit_url: str = _rabbit_url
rabbit_vhost: str = os.environ.get('RABBIT_VHOST', 'gunlinux_bot')
rabbit_exchange: str = os.environ.get('RABBIT_EXCHANGE', 'twitch_getter')

# Retwitch
RECLIENT_ID: str = os.environ.get('RECLIENT_ID', '')
RECLIENT_SECRET: str = os.environ.get('RECLIENT_SECRET', '')
REOWNER_ID: str = os.environ.get('REOWNER_ID', '')
REBOT_ID: str = os.environ.get('REBOT_ID', '')
TOKEN_FILE: str = os.environ.get('TOKEN_FILE', 'tokens.json')
CHANNEL_TOKEN_FILE: str = os.environ.get('CHANNEL_TOKEN_FILE', 'channels_tokens.json')

# paths
COMMAND_DIR: str = os.environ.get('COMMAND_DIR', './commands/')
scripts_path: str = 'local_events/scripts/'


# QUEUES
LOCAL_EVENTS = 'local_events'
TWITCH_OUT = 'twitch_out'
TWITCH_EVENTS = 'twitch_events'
