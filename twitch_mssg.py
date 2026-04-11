import asyncio
import sys

from faststream.rabbit import RabbitBroker

from retwitch import settings
from requeue.sender.sender import Sender


def usage() -> None:
    print(f'{sys.argv[0]} "<message to twitch queue>"')


async def main() -> None:
    if len(sys.argv) != 1 + 1:
        usage()
        sys.exit(1)

    mssg = sys.argv[1]
    broker = RabbitBroker(settings.rabbit_url, virtualhost=settings.rabbit_vhost)

    sender = Sender(exchange_name=settings.TWITCH_OUT, broker=broker)
    await sender.send_message(mssg)


if __name__ == '__main__':
    asyncio.run(main())
