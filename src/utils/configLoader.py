import json
import os
from dataclasses import dataclass
from typing import List
from collections import defaultdict
import re
import uuid

HOME = os.environ['HOME']

@dataclass
class TerminalConfiguration:
    name: str = "Undefined"
    directory: str = HOME
    command: List[List[str]] = (("echo", "command did not assigned"),)
    restart: bool = False
    buildable: bool = True
    
    def to_dict(self):
        """Convierte la instancia de TerminalConfiguration a un diccionario."""
        return {
            "name": self.name,
            "directory": self.directory,
            "command": self.command,
            "restart": self.restart,
            "buildable": self.buildable
        }

    @staticmethod
    def from_dict(data: dict):
        """Convierte un diccionario en una instancia de TerminalConfiguration."""
        return TerminalConfiguration(
            name=data.get("name", "Undefined"),
            directory=data.get("directory", HOME),
            command=data.get("command", [["echo", "command did not assigned"],]),
            restart=data.get("restart", False),
            buildable=data.get("buildable", True)
        )


def loadConfig(filename: str) -> defaultdict[str, TerminalConfiguration]:
    """Carga la configuración desde un archivo JSON o CSV."""
    terminalsConfig = defaultdict(TerminalConfiguration)
    if filename.endswith('.json'):
        with open(filename, 'r') as f:
            config = json.load(f)
            for terminal_data in config:
                if 'directory' in terminal_data:
                    terminal_data['directory'] = os.path.expandvars(terminal_data['directory'])
                
                if 'command' in terminal_data:
                    raw_command = os.path.expandvars(terminal_data["command"])
                    split_commands = re.split(r'&&|;', raw_command)
                    terminal_data['command'] = [cmd.strip().split() for cmd in split_commands if cmd.strip()]
                terminalsConfig[str(uuid.uuid4())] = TerminalConfiguration.from_dict(terminal_data)
    else:
        raise ValueError("Unsupported config file format")
    return terminalsConfig


def saveConfig(filename: str, terminalsConfig: defaultdict[str, TerminalConfiguration]):
    """Guarda las configuraciones en un archivo JSON."""
    data = []
    
    for terminal in terminalsConfig.values():
        terminal_dict = terminal.to_dict()
        commands_list = terminal_dict.get('command', [])
        formatted_str = ""

        for i, cmd_args in enumerate(commands_list):
            formatted_str += " ".join(cmd_args)
            if i < len(commands_list) - 1:
                formatted_str += " && "
        
        terminal_dict['command'] = formatted_str
        data.append(terminal_dict)
    if filename.endswith('.json'):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    else:
        raise ValueError("Unsupported config file format")

