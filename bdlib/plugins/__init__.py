from importlib.metadata import entry_points
from typing import List
from bdlib.cli import CliPlugin


def discover_plugins() -> List[CliPlugin]:
    plugins = []
    eps = entry_points(group="bdlib.plugins")
    for entry_point in eps:
        try:
            plugin_class = entry_point.load()
            plugins.append(plugin_class())
        except Exception as e:
            print(f"Failed to load plugin {entry_point.name}: {e}")
    return plugins
