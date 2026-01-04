import json
from dataclasses import dataclass
from typing import Dict, Any

def _coerce_number(x: Any) -> float:
    """
    Accepts:
      - int/float
      - dict wrappers like {"value": 0.1}, {"const": 0.1}, {"s": 0.1}
      - nested wrappers like {"value": {"value": 0.1}} or {"type": "...", "value": 0.1}
    Raises with a helpful message if it cannot coerce.
    """
    if isinstance(x, (int, float)):
        return float(x)

    if isinstance(x, dict):
        # Common wrapper keys (try in order)
        for k in ("value", "const", "s", "signal"):
            if k in x:
                return _coerce_number(x[k])

        # Sometimes the numeric value is the only dict value
        if len(x) == 1:
            return _coerce_number(next(iter(x.values())))

        raise TypeError(f"Cannot coerce channel descriptor to float. Keys={list(x.keys())}")

    raise TypeError(f"Cannot coerce channel value to float. Type={type(x).__name__}")

@dataclass
class World:
    channels: Dict[str, float]

    def get_channel_value(self, name: str) -> float:
        return float(self.channels[name])

def load_world(path: str) -> World:
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)

    raw_channels = obj.get("channels", {})
    if not isinstance(raw_channels, dict):
        raise TypeError("world JSON must contain an object 'channels' mapping names to values/descriptors")

    channels: Dict[str, float] = {}
    for name, raw in raw_channels.items():
        channels[name] = _coerce_number(raw)

    return World(channels=channels)
