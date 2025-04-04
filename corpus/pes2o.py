from concurrent.futures import ThreadPoolExecutor
import os
from .base import Lookup
from datasets import load_dataset
from dotenv import load_dotenv

load_dotenv()

default_pes2o_path = os.environ['PES2O_PATH']
default_index_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'indices',
    'olmo-mix-1124-pes2o-ids-to-file.parquet')

class Pes2oLookup(Lookup):

    def __init__(self, pes2o_path=default_pes2o_path, index_path=default_index_path, lazy=True):
        indices = load_dataset('parquet', data_files=default_index_path).to_list()
        pes2o_lookup = {}
        for row in indices:
            file = row['file']
            for j, id in enumerate(row['corpus_ids']):
                pes2o_lookup[id] = (file, j)
        dats = {}
        if not lazy:
            with ThreadPoolExecutor(max_workers=32) as pool:
                for row in indices:
                    file = row['file']
                    dats[file] = pool.submit(load_dataset, 'json', data_files=os.path.join(pes2o_path, file), split='train')
            for file in dats:
                dats[file] = dats[file].result()
        self.dats = dats
        self.pes2o_lookup = pes2o_lookup
        self.pes2o_path = pes2o_path
        self.index_path = index_path

    def get_paper(self, id):
        file, idx = self.pes2o_lookup[id]
        if file not in self.dats:
            self.dats[file] = load_dataset('json', data_files=os.path.join(self.pes2o_path, file), split='train')
        paper = self.dats[file][idx]
        return paper