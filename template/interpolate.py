from __future__ import annotations
import builtins
import functools
import re
from jinja2 import Environment, StrictUndefined


@functools.cache
def indent_template(template):
    doc = []
    for line in template.splitlines():
        ws = len(line) - len(line.lstrip())
        doc.append(re.sub("{{([^{}]*)}}", lambda s: f"{{{{ str({s.group(1)}) | indent({ws})}}}}", line))
    return "\n".join(doc)

def builtins_kwargs():
    d = {}
    for name in dir(builtins):
        d[name] = getattr(builtins, name)
    return d
    
def interpolate(s, args):
    env = Environment(undefined=StrictUndefined)
    ast = env.parse(indent_template(s))
    rendered_string = env.from_string(ast).render(**(args | builtins_kwargs()))
    return rendered_string