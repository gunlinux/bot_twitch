from dataclasses import dataclass, field
import logging

from retwitch.models.commands import Command
from requeue.fstream.models import FQueueEvent


logger = logging.getLogger('retwitch.handlers')
logger.setLevel(logging.DEBUG)


@dataclass
class CommandRegistry:
    commands: dict[str, Command] = field(default_factory=dict)

    def register(self, command: Command) -> None:
        logger.debug('Successfully registered command %s', command.name)
        self.commands[command.name] = command
        if command.name[0] not in '$!':
            self.commands[f'!{command.name}'] = command

    def clear_raw_commands(self) -> None:
        self.commands = {
            command_name: command
            for command_name, command in self.commands.items()
            if command.real_runner is not None
        }

    def _get_command(self, message: str) -> Command | None:
        for command_name, command in self.commands.items():
            if message.lower().startswith(command_name.lower()):
                return command
        return None

    async def run(self, message: str, event: FQueueEvent) -> str:
        if not message:
            return ''
        command = self._get_command(message)
        if not command:
            return ''

        if command.real_runner is None and command.data:
            return command.data.get('text', '')
        return await command.real_runner(event)
