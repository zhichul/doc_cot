from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import dataclasses
import os

import tqdm
from .base import Lookup
from datasets import load_dataset
from dotenv import load_dotenv

load_dotenv()

default_wikipath = os.environ['WIKIPATH']
default_index_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'indices',
    'olmo-mix-1124-wiki-titles-to-file.parquet')

class WikiLookup(Lookup):

    def __init__(self, wikipath=default_wikipath, index_path=default_index_path, lazy=True):
        indices = load_dataset('parquet', data_files=default_index_path)['train'].to_list()
        wikilookup = defaultdict(list)
        for row in tqdm.tqdm(indices):
            file = row['file']
            for j, id in enumerate(row['titles']):
                wikilookup[str(id)].append((file, j))
        dats = {}
        if not lazy:
            with ThreadPoolExecutor(max_workers=32) as pool:
                for row in indices:
                    file = row['file']
                    dats[file] = pool.submit(load_dataset, 'json', data_files=os.path.join(wikipath, file), split='train')
            for file in dats:
                dats[file] = dats[file].result()
        self.dats = dats
        self.wikilookup = wikilookup
        self.wikipath = wikipath
        self.index_path = index_path

    def get_doc(self, id: str, as_obj=False):
        if id not in self: 
            return None
        file_indices = self.wikilookup[id]
        pages = []
        for file, idx in file_indices:
            if file not in self.dats:
                self.dats[file] = load_dataset('json', data_files=os.path.join(self.wikipath, file), split='train')
            page = self.dats[file][idx]
            pages.append(page)
        if as_obj:
            raise NotImplementedError
        return pages

    def get_docs(self, ids: list[int|str], as_obj=False, max_workers=4):
        futs = []
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            for id in ids:
                futs.append(pool.submit(self.get_doc, id, as_obj=as_obj))
        for fut in futs:
            yield fut.result()
        
    def __contains__(self, id):
        if isinstance(id, int):
            id = str(id)
        return id in self.wikilookup