from concurrent.futures import ThreadPoolExecutor
import dataclasses
import os

import tqdm
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
        indices = load_dataset('parquet', data_files=default_index_path)['train'].to_list()
        pes2o_lookup = {}
        for row in tqdm.tqdm(indices):
            file = row['file']
            for j, id in enumerate(row['corpus_ids']):
                pes2o_lookup[str(id)] = (file, j)
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

    def get_doc(self, id: int|str, as_obj=False):
        if isinstance(id, int):
            id = str(id)
        if id not in self: 
            return None
        file, idx = self.pes2o_lookup[id]
        if file not in self.dats:
            self.dats[file] = load_dataset('json', data_files=os.path.join(self.pes2o_path, file), split='train')
        paper = self.dats[file][idx]
        if as_obj:
            return Pes2oPaper(**paper)
        return paper

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
        return id in self.pes2o_lookup
    

# Each document in the dataset is a dictionary with the following fields:

# added: Date the document was added to the corpus.
# created: Best-guess date for when the document was first published. Some have resolution down to the day, only down to the year.
# id: Semantic Scholar Corpus ID of the document; it can be used with the Semantic Scholar API to retrieve metadata about the document (e.g., fields of study, authors).
# source: Collection from which the document was sourced from. At the moment, two are supported:
# s2orc: collection of full-text papers
# s2ag: collection of title and abstracts
# text: Text of the document. Paragraphs are separated by two newlines (\n\n).
# version: version of peS2o.
# metadata: extra info

@dataclasses.dataclass
class Pes2oPaper:

    added: str = None
    created: str = None
    id: str = None
    source: str = None # s2orc or s2ag
    text: str = None
    version: str = None
    metadata: dict = None