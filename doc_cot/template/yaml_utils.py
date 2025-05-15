from __future__ import annotations

from ruamel.yaml import YAML
from .interpolate import interpolate
import yaml

def load_single(s: str=None, file: str=None, interpolation_args=None):
    if s is None:
        with open(file, 'rt') as f:
            s = f.read()
    if interpolation_args is not None:
        s = interpolate(s, interpolation_args)
    return yaml.safe_load(s)