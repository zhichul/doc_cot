from vllm import LLM, SamplingParams
from transformers import AutoTokenizer
from datasets import load_dataset
import random


from .base import dump, get_base_arg_parser


def parse_args():
    parser = get_base_arg_parser()
    parser.add_argument('--tensor_parallel_size', type=int, default=1)
    parser.add_argument('--dtype', default='bfloat16')
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
    llm = LLM(args.model_name_or_path, tensor_parallel_size=args.tensor_parallel_size, dtype=args.dtype)
    sampling_params = SamplingParams(n=args.n, temperature=args.temp, max_tokens=args.max_tokens)
    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path)
    prompt_token_ids = [tokenizer.apply_chat_template(messages, add_generation_prompt=True) for messages in messages_list]

    outputs = llm.generate(prompt_token_ids=prompt_token_ids, sampling_params=sampling_params)
    responses_texts = [[o.text for o in output.outputs] for output in outputs]
    results = []

    for messages, responses in zip(messages_list, responses_texts):
        res = {'prompt': messages, 'responses': responses}
        results.append(res)
    dump(results, out_dir=args.out_dir, out_file=args.out_file)

if __name__ == '__main__':
    main()