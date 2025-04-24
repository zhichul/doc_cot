from __future__ import annotations
import dataclasses
import os
import addict

class DictNoDefault(addict.Dict):
    def __missing__(self, key):
        raise KeyError(key)


def parse_name(s):
    parts = s.rsplit('_', 2)  # split from the right, max 2 splits
    if len(parts) != 3:
        raise ValueError("String must be in format 'name_major_minor'")
    
    name, minor_str, major_str = parts
    try:
        major = int(major_str)
        minor = int(minor_str)
    except ValueError:
        raise ValueError("Major and minor must be integers")
    
    return name, major, minor

def split_path(full_path: str, root_dir: str):
    rel_path = os.path.relpath(full_path, root_dir)
    parts = rel_path.replace(os.sep, '/').split('/')
    name, ext = os.path.splitext(parts[-1])
    return parts[:-1] + [name, ext.lstrip('.')]

def read_file(full_path: str):
    with open(full_path, 'rt') as f:
        return f.read()

def namespace_at_path(root, path: list[str]):
    d = root
    for s in path:
        d = d[s]
    return d

@dataclasses.dataclass
class Prompt:
    name: str
    major: int
    minor: int
    content: str

def update_defaults(module: dict[str, Prompt], prompt):
    base_name = prompt.name
    if (base_name not in module) or \
       (prompt.major > module[base_name].major) or \
       (prompt.major == module[base_name].major and prompt.minor > module[base_name].latest.minor):
        module[base_name] = prompt
    major_name = f'{prompt.name}_{prompt.major}'
    if (major_name not in module) or \
       (prompt.minor > module[major_name].latest.minor):
        module[major_name] = prompt
    full_name = f'{prompt.name}_{prompt.major}_{prompt.minor}'
    assert full_name not in module
    module[full_name] = prompt

def load_prompts(prompt_dir = os.path.join(os.path.dirname(__file__), 'prompts')):
    prompts = addict.Dict()
    for dirpath, _, filenames in os.walk(prompt_dir):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            
            path = split_path(full_path, prompt_dir)
            extension = path[-1]
            if extension == 'yaml':
                # parse prompt
                name, major, minor = parse_name(path[-2])
                content = read_file(full_path)
                prompt = Prompt(name, major, minor, content)
                
                # put it in right path, with some versioning default
                dir = path[:-2]
                module = namespace_at_path(prompts, dir)
                update_defaults(module, prompt)
    return DictNoDefault(prompts)

prompts = load_prompts()

def print_nested_keys(d, indent=0):
    for key, value in d.items():
        print('  ' * indent + str(key))
        if isinstance(value, dict):
            print_nested_keys(value, indent + 1)
            
if __name__ == '__main__':
    print_nested_keys(prompts)
                
                
                


            