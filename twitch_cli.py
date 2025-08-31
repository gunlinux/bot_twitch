import asyncio
import os
import sys
import logging
from retwitch.token import TokenManager
import dotenv
from retwitch import settings

logger = logging.getLogger('twitchbot')


async def main():
    dotenv.load_dotenv()
    client_id = os.getenv('RECLIENT_ID', '')
    client_secret = os.getenv('RECLIENT_SECRET', '')
    token_manager: TokenManager = TokenManager(
        client_id=client_id,
        client_secret=client_secret,
        token_file=settings.TOKEN_FILE,
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
        await token_manager.get_token_from_code(code=code)
        token_manager.token_file = file
        token_manager.save_real_token()
        return


if __name__ == '__main__':
    asyncio.run(main())
