import sys
from enum import Enum
import asyncio
import psutil

class AlpacaInterface:
    class State(Enum):
        ACTIVE = 0
        TERMINATED = 1

    def __init__(self, model_path):
        self.model_path = model_path
        self.state = self.State.TERMINATED

    async def restart(self):
        await self.terminate()
        await self.start()

    async def start(self):
        if self.state == self.State.ACTIVE:
            return False

        self.cli_process = await asyncio.create_subprocess_shell(
                ' '.join([self.model_path]),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=sys.stderr
            )
        
        self.state = self.State.ACTIVE

        await self._initial_flush_readline()
        return True
    
    # Flush the initial prints before first user prompt
    async def _initial_flush_readline(self):
        if self.state != self.State.ACTIVE:
            return

        # Flush 1 empty line
        await self.cli_process.stdout.readline()

        # Flush "> "
        await self.cli_process.stdout.read(2)
        return True

    async def read(self):
        if self.state != self.State.ACTIVE:
            return False

        output = ''

        # Used to detect user input prompt
        prev_new_line = True

        while True:
            # Read output of alpaca.cpp char by char till we see "\n> "
            byte_array = bytearray()
            while True:
                try:
                    byte_array += await self.cli_process.stdout.read(1)
                    new_char = byte_array.decode('utf-8')
                    break
                except UnicodeDecodeError:
                    pass

            # User input prompt detection
            if prev_new_line and new_char == ">":
                # Check if the next char is " "
                next_char = await self.cli_process.stdout.read(1)
                next_char = next_char.decode('utf-8')
                if next_char == " ":
                    break

                output += new_char + next_char
            else:
                output += new_char

            if new_char == '\n':
                prev_new_line = True
            else:
                prev_new_line = False

        return output
    
    async def write(self, prompt):
        if self.state != self.State.ACTIVE:
            return False

        prompt = prompt.strip()
        # print(f"Wrote \"{prompt}\" to chat")
        self.cli_process.stdin.write((prompt+"\n").encode('utf-8'))
        await self.cli_process.stdin.drain()

        return True

    async def terminate(self):
        if self.state != self.State.ACTIVE:
            return False

        self.state = self.State.TERMINATED

        self.cli_process.stdin.close()
        self.cli_process.stdout._transport.close()
        parent = psutil.Process(self.cli_process.pid)
        for child in parent.children(recursive=True):
            child.terminate()
        self.cli_process.terminate()

        return True

    async def __aenter__(self):
        return self

    async def __aexit__(self):
        await self.terminate()