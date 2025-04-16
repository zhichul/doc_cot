import dataclasses
import json
import os
from openai import OpenAI
from template import yaml_utils
from corpus.pes2o import Pes2oLookup, Pes2oPaper
from corpus.s2orc import get_bibs_by_id_batched
from .base import prompts

@dataclasses.dataclass
class Score:
    value: int = None
    rationale: str = None

@dataclasses.dataclass
class Citation:
    literal: str = None # (xyz et al., 2024)
    type: str = None # name_year or index
    paper: Pes2oPaper = None

@dataclasses.dataclass
class QAPair:
    question: str = None
    answer: str = None
    rationale: str = None
    score: Score = None

@dataclasses.dataclass
class Citance:
    citation: Citation = None
    context: str = None
    score: Score = None
    qa_pairs: list[QAPair] = dataclasses.field(default_factory=list)

@dataclasses.dataclass
class AnnotatedPaper(Pes2oPaper):
    bibliography: list[Pes2oPaper] = None
    citances: list[Citance] = None 

def find_matching_bib_entry(paper: AnnotatedPaper, citance: Citance, client: OpenAI, **kwargs):
    config = yaml_utils.load_single(s=prompts.question_generation.find_id.content, interpolation_args={'paper': paper, 'citance': citance})
    print(config['messages']['user'])
    with open(f'citance_match_prompt_{citance.citation.literal}.json', 'wt') as f:
        print(json.dumps(config, indent=4), file=f)
    if 'response_format' not in kwargs:
        kwargs['response_format'] = config.get('response_format', None)
    output = client.chat.completions.create(
        messages = [{'role': 'system', 'content': config['messages']['system'],
                     'role': 'user', 'content': config['messages']['user']}],
        **kwargs
    )
    match = json.loads(output.choices[0].message.content)
    print(json.dumps({'match': match, 'citance': dataclasses.asdict(citance)} , indent=4))
    print("##################################")
    with open(f'citance_match_result_{citance.citation.literal}.json', 'wt') as f:
        print(json.dumps({'match': match, 'citance': dataclasses.asdict(citance)} , indent=4), file=f)
    return match

def extract_citances(paper: AnnotatedPaper, client: OpenAI, **kwargs):
    config = yaml_utils.load_single(s=prompts.question_generation.citance.content, interpolation_args={'paper': paper})
    with open('citance_extraction_prompt.json', 'wt') as f:
        print(json.dumps(config, indent=4), file=f)
    if 'response_format' not in kwargs:
        kwargs['response_format'] = config.get('response_format', None)
    output = client.chat.completions.create(
        messages = [{'role': 'system', 'content': config['messages']['system'],
                     'role': 'user', 'content': config['messages']['user']}],
        **kwargs
    )
    cits = json.loads(output.choices[0].message.content)
    with open('citance_extraction_result.json', 'wt') as f:
        print(json.dumps(cits, indent=4), file=f)
    return [Citance(context=cit['context'], 
                    citation=Citation(literal=cit['citation']['literal'],
                                      type=cit['citation']['type']))for cit in cits['citances']]

def generate_question(paper: AnnotatedPaper, citance: Citance, client, **kwargs):
    debug_name = citance.citation.paper.id
    config = yaml_utils.load_single(s=prompts.question_generation.question.content, 
                interpolation_args={'paper': paper, 'citance': citance})
    with open(f'cit_ex_quest_prompt_{debug_name}.json', 'wt') as f:
        print(json.dumps(config, indent=4), file=f) 
    if 'response_format' not in kwargs:
        kwargs['response_format'] = config.get('response_format', None)
    cit_ques_output = client.chat.completions.create(
        messages = [{'role': 'system', 'content': config['messages']['system'],
                    'role': 'user', 'content': config['messages']['user']}],
        **kwargs
    )
    quest = json.loads(cit_ques_output.choices[0].message.content)
    with open(f'cit_ex_quest_response_{debug_name}.json', 'wt') as f:
        print(json.dumps(quest, indent=4), file=f)
    return quest

def generate_relation(paper: AnnotatedPaper, citance: Citance, client, **kwargs):
    debug_name = citance.citation.paper.id
    config = yaml_utils.load_single(s=prompts.question_generation.relation.content, 
                interpolation_args={'paper': paper, 'citance': citance})
    with open(f'cit_ex_rel_prompt_{debug_name}.json', 'wt') as f:
        print(json.dumps(config, indent=4), file=f) 
    if 'response_format' not in kwargs:
        kwargs['response_format'] = config.get('response_format', None)
    cit_rel_output = client.chat.completions.create(
        messages = [{'role': 'system', 'content': config['messages']['system'],
                    'role': 'user', 'content': config['messages']['user']}],
        **kwargs
    )
    quest = json.loads(cit_rel_output.choices[0].message.content)
    with open(f'cit_ex_rel_response_{debug_name}.json', 'wt') as f:
        print(json.dumps(quest, indent=4), file=f)
    return quest


def citance_based_question_generation(paper: Pes2oPaper, client: OpenAI, lookup: Pes2oLookup, **kwargs):
    paper = AnnotatedPaper(**dataclasses.asdict(paper))

    # fetch bib (useful fields are bib.contexts, bib.citedPaper.field, where field is one of below)
    bibs = get_bibs_by_id_batched(paper.id, fields=['corpusId', 'authors', 'title', 'year', 'contexts'], as_addict=True)
    paper.bibliography = bibs
    print(bibs[0].contexts)
    # extract citance
    citances = extract_citances(paper, client, **kwargs)
    paper.citances = citances
    
    # for each citance, generate a list of questions
    for citance in citances:
        bib = find_matching_bib_entry(paper, citance, client, **kwargs)
        id = bib['corpusId']
        if id in lookup:
            print(f'{id} in pes2o')
            cited_paper = lookup.get_doc(id, as_obj=True)
            citance.citation.paper = cited_paper
        else:
            print(f'{id} not in pes2o')
            continue

        generate_question(paper, citance, client, **kwargs)

def citance_based_relation_generation(paper: Pes2oPaper, client: OpenAI, lookup: Pes2oLookup, **kwargs):
    paper = AnnotatedPaper(**dataclasses.asdict(paper))

    # fetch bib (useful fields are bib.contexts, bib.citedPaper.field, where field is one of below)
    bibs = get_bibs_by_id_batched(paper.id, fields=['corpusId', 'authors', 'title', 'year', 'contexts'], as_addict=True)
    paper.bibliography = bibs
    print(bibs[0].contexts)
    # extract citance
    citances = extract_citances(paper, client, **kwargs)
    paper.citances = citances
    exit(0)
    # for each citance, generate a list of questions
    for citance in citances:
        bib = find_matching_bib_entry(paper, citance, client, **kwargs)
        id = bib['corpusId']
        if id in lookup:
            print(f'{id} in pes2o')
            cited_paper = lookup.get_doc(id, as_obj=True)
            citance.citation.paper = cited_paper
        else:
            print(f'{id} not in pes2o')
            continue

        generate_relation(paper, citance, client, **kwargs)




if __name__ == '__main__':
    # lookup = Pes2oLookup()
    # paper = lookup.get_doc(229348988)
    # content = paper['text']
    lookup = Pes2oLookup()
    content = Pes2oPaper(**json.load(open('resources/distributional.json')))
    client = OpenAI(base_url='http://nid008500:8001/v1', api_key='EMPTY')
    model = 'meta-llama/Llama-3.3-70B-Instruct'
    print(json.dumps(citance_based_relation_generation(content, client, lookup, model=model), indent=4))