import json
import os
from dataclasses import dataclass
from typing import List
from collections import defaultdict

HOME = os.environ['HOME']

@dataclass
class TerminalConfiguration:
    name: str = "Undefined"
    directory: str = HOME
    command: str = "echo command did not assigned"
    restart: bool = False
    
    def to_dict(self):
        """Convierte la instancia de TerminalConfiguration a un diccionario."""
        return {
            "name": self.name,
            "directory": self.directory,
            "command": self.command,
            "restart": self.restart
        }

    @staticmethod
    def from_dict(data: dict):
        """Convierte un diccionario en una instancia de TerminalConfiguration."""
        return TerminalConfiguration(
            name=data.get("name", "Undefined"),
            directory=data.get("directory", HOME),
            command=data.get("command", "echo command did not assigned"),
            restart=data.get("restart", False)
        )


def loadConfig(filename: str) -> defaultdict[int, TerminalConfiguration]:
    """Carga la configuración desde un archivo JSON o CSV."""
    terminalsConfig = defaultdict(TerminalConfiguration)
    if filename.endswith('.json'):
        with open(filename, 'r') as f:
            config = json.load(f)
            for idx, terminal_data in enumerate(config):
                terminalsConfig[idx] = TerminalConfiguration.from_dict(terminal_data)
    else:
        raise ValueError("Unsupported config file format")
    return terminalsConfig


def saveConfig(filename: str, terminalsConfig: defaultdict[int, TerminalConfiguration]):
    """Guarda las configuraciones en un archivo JSON."""
    data = [terminal.to_dict() for terminal in terminalsConfig.values()]
    
    if filename.endswith('.json'):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    else:
        raise ValueError("Unsupported config file format")

