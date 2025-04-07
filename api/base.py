import argparse
import json
import os


def dump(results: list[dict], out_dir=None, out_file=None):
    if out_file is not None:
        with open(out_file, 'wt') as f:
            for result in results:
                print(json.dumps(result), file=f)
    elif out_dir is not None:
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        for i, res in enumerate(results):
            with open(f'{out_dir}/{i}.json', 'wt') as f:
                print(json.dumps(res, indent=4), file=f)
    else:
        raise ValueError("No out_file/out_dir provided")

def get_base_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--data_path', required=True)
    parser.add_argument('--out_file', required=False)
    parser.add_argument('--out_dir', required=False)
    parser.add_argument('--max_tokens', type=int, default=None)
    parser.add_argument('--first_n', type=int, default=None)
    parser.add_argument('--sample', type=int, default=None)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--idx', type=int, default=None)
    parser.add_argument('--n', type=int, default=1)
    parser.add_argument('--temp', type=float, default=1.0)
    parser.add_argument('--prompt_key', type=str, default='prompt')
    parser.add_argument('--responses_key', type=str, default='responses')
    return parser