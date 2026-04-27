import asyncio
import os
import sys
import logging
from retwitch.token.token_manager import TokenManager
from retwitch.token.token_store import TokenStore
from retwitch.token.token_oauth import TwitchAuth
import dotenv
from retwitch import settings

logger = logging.getLogger('twitchbot')


async def main():
    dotenv.load_dotenv()
    client_id = os.getenv('RECLIENT_ID', '')
    client_secret = os.getenv('RECLIENT_SECRET', '')
    token_store = TokenStore(token_file=settings.TOKEN_FILE)
    twitch_auth = TwitchAuth(
        client_id=client_id,
        client_secret=client_secret,
    )
    token_manager: TokenManager = TokenManager(
        twitch_auth=twitch_auth,
        token_store=token_store,
    )

    if len(sys.argv) == 1:
        url = token_manager.generate_code_url()
        print(url)
        sys.exit()

    if len(sys.argv) == 1 + 1:
        # only code -> save to default file
        code = sys.argv[1]
        await token_manager.get_token_from_code(code=code)
        token_manager.save_real_token()
        return

    if len(sys.argv) == 1 + 1 + 1:
        # code + file name -> + channel_token
        code = sys.argv[1]
        file = sys.argv[2]
        token_store = TokenStore(token_file=file)
        token_manager: TokenManager = TokenManager(
            twitch_auth=twitch_auth,
            token_store=token_store,
        )
        await token_manager.get_token_from_code(code=code)
        token_manager.save_real_token()
        return


if __name__ == '__main__':
    asyncio.run(main())
