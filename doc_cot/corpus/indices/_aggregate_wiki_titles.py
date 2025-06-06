from datasets import load_dataset, Dataset

w1 = load_dataset('json', data_files='/pscratch/sd/z/zlu39/olmo-mix-1124/data/wiki/wiki-0001.json.gz')['train']
w0 = load_dataset('json', data_files='/pscratch/sd/z/zlu39/olmo-mix-1124/data/wiki/wiki-0000.json.gz')['train']
w0_with_name = w0.map(lambda xs: {'title': [x.split("\n\n")[0] for x in xs['text']]}, batched=True)
w1_with_name = w1.map(lambda xs: {'title': [x.split("\n\n")[0] for x in xs['text']]}, batched=True)
wiki_index = [{'file': 'wiki-0000.json.gz', 'titles': w0_with_name['title']}, {'file': 'wiki-0001.json.gz', 'titles': w1_with_name['title']}]
Dataset.from_list(wiki_index).to_parquet("olmo-mix-1124-wiki-titles-to-file.parquet")