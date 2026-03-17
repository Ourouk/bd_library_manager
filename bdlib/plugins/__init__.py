import pkg_resources
from typing import List
from bdlib.cli import CliPlugin


def discover_plugins() -> List[CliPlugin]:
    plugins = []
    for entry_point in pkg_resources.iter_entry_points("bdlib.plugins"):
        try:
            plugin_class = entry_point.load()
            plugins.append(plugin_class())
        except Exception as e:
            print(f"Failed to load plugin {entry_point.name}: {e}")
    return plugins
