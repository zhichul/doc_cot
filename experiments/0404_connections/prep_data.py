from dotenv import load_dotenv
load_dotenv()
import sys
import os
sys.path.append(os.environ["PROJECT_ROOT"])
import json
from corpus.pes2o import Pes2oLookup
from datasets import Dataset

def main():
    lookup = Pes2oLookup()
    with open('papers.jsonl','rt') as f:
        papers = [json.loads(line) for line in f]
    paper_infos = []
    for paper in papers:
        doc = lookup.get_doc(paper['id'])
        paper_infos.append(doc)
    prompts = []
    system ="""\
Your are an expert in machine learning and natural language processing. You need to analyze papers.
"""
    user = """\
Here's a paper {text}\n\nSuppose someone is trying to remember this paper but only remembered parts of it. What parts do you think would be salient, and what queries would the user put into the search engine? What about asking a colleague? Would they ask different queries to a human than a search engine? 

List your answer in two sections:
<search_engine></search_engine> for search engine queries
<human></human> for queries to a human colleague
"""
    for paper, meta in zip(paper_infos, papers):
        messages = [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user.format(text=paper['text'])}
        ]
        prompts.append({'prompt': messages, 'paper': paper, 'meta': meta})
    Dataset.from_list(prompts).to_parquet('prompts.parquet')
if __name__ == "__main__":
    main()