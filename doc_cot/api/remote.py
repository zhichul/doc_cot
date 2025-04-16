from concurrent.futures import ThreadPoolExecutor
from datasets import load_dataset
from openai import OpenAI
import random


from .base import dump, get_base_arg_parser


def parse_args():
    parser = get_base_arg_parser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--api_key', required=False, default=None)
    parser.add_argument('--n_threads', type=int, default=16, help='how many threads to run when callin api')
    args = parser.parse_args()
    return args

def main():
    args = parse_args()

    examples = load_dataset('parquet', data_files=args.data_path)['train']
    if args.first_n is not None:
        selected =examples[:args.first_n]
    elif args.idx is not None:
        selected=examples[args.idx:args.idx+1]
    elif args.sample is not None:
        random.seed(args.seed)
        selected=examples[random.sample(list(range(len(examples))), k=args.sample)]
    else:
        selected=examples

    messages_list = selected[args.prompt_key]

    client = OpenAI(base_url=args.url, api_key=args.api_key)
    futures = []
    with ThreadPoolExecutor(max_workers=args.n_threads) as worker:
        for messages in messages_list:
            futures.append(worker.submit(client.chat.completions.create, 
                                         messages=messages, 
                                         model=args.model, 
                                         max_tokens=args.max_tokens, 
                                         n=args.n, 
                                         temperature=args.temp))
    outputs = [future.result() for future in futures]

    responses_texts = [[o.message.content for o in completion.choices] for completion in outputs]
    results = []
    for messages, responses, ex in zip(messages_list, responses_texts, selected.to_list()):
        res = {'prompt': messages, 'responses': responses, 'example': ex}
        results.append(res)
    dump(results, out_dir=args.out_dir, out_file=args.out_file)

if __name__ == '__main__':
    main()