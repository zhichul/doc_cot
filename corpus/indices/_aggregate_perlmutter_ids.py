import os
import tqdm
from datasets import Dataset
from pathlib import Path

input_dir = Path("/pscratch/sd/z/zlu39/olmo-mix-1124/data/pes2o/")
output_file = "olmo-mix-1124-pes2o-ids-to-file.parquet"

index = []
for file_path in tqdm.tqdm(input_dir.glob('pes2o-*.ids')):
    data_name = file_path.stem + '.json.gz'
    with open(file_path, "r") as f:
        cids = []
        for line in f:
            cid = int(line)
            cids.append(cid)
    index.append({"file": data_name, "corpus_ids": line.rstrip("\n")})
Dataset.from_list(index).to_parquet(output_file)