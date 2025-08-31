import asyncio
import sys
from retwitch import settings
from requeue.rredis import RedisConnection
from requeue.sender.sender import Sender


def usage() -> None:
    print(f'{sys.argv[0]} "<message to twitch queue>"')


async def main() -> None:
    if len(sys.argv) != 1 + 1:
        usage()
        sys.exit(1)

    mssg = sys.argv[1]
    redis_url: str = settings.twitch_redis_url
    async with RedisConnection(redis_url) as redis_connection:
        sender = Sender(queue_name='twitch_out', connection=redis_connection)
        await sender.send_message(mssg)


if __name__ == '__main__':
    asyncio.run(main())
