from pathlib import Path
import sys
import time
from requests import Session
from dotenv import load_dotenv
import os
import addict
import tqdm

print(Path(__file__).resolve().parent.parent.parent / '.env', file=sys.stderr)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / '.env')

S2_API_KEY = os.environ['S2_API_KEY']
REQUEST_WAIT=1.5
default_fields = ['paperId', 'title', 'corpusId']
default_reference_fields = default_fields + ['contexts']
def wait_after(seconds):
    def wrapper(func):
        def inner(*args, **kwargs):
            result = func(*args, **kwargs)
            time.sleep(seconds)
            return result
        return inner
    return wrapper

def split(items: list[any], batch_size: int):
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

@wait_after(REQUEST_WAIT)
def _get_papers_by_ids_with_session(session: Session, ids: list[str], fields: list[str] = default_fields, id_type='corpus', **kwargs):
    params = {'fields': ','.join(fields), **kwargs}
    headers = {'X-API-KEY': S2_API_KEY}
    full_ids = []
    for id in ids:
        if id_type == 'corpus':
            full_ids.append(f'CorpusId:{id}')
        elif id_type == 'paper':
            full_ids.append(id)
        else:
            raise NotImplementedError
    body = {'ids': full_ids}
    with session.post('https://api.semanticscholar.org/graph/v1/paper/batch',
                       params=params,
                       headers=headers,
                       json=body) as response:
        response.raise_for_status()
        return response.json()

def get_papers_by_ids(ids: list[str], fields: list[str]=default_fields, session: Session=None, id_type='corpus', **kwargs) -> list[dict]:
    if session is None:
        with Session() as session:
            return _get_papers_by_ids_with_session(session, ids, fields=fields, id_type=id_type, **kwargs)
    else:
        return _get_papers_by_ids_with_session(session, ids, fields=fields, id_type=id_type, **kwargs)

def _get_papers_by_ids_batched(ids: list[str], batch_size: int = 100, **kwargs):
    # use a session to reuse the same TCP connection
    with Session() as session:
        # take advantage of S2 batch paper endpoint
        for ids_batch in split(ids, batch_size):
            yield from _get_papers_by_ids_with_session(session, ids_batch, **kwargs)

def get_papers_by_ids_batched(ids, fields: list[str]=default_fields, batch_size: int = 100, id_type='corpus', **kwargs):
    results = []
    for result in tqdm.tqdm(_get_papers_by_ids_batched(ids, fields=fields, batch_size=batch_size, **kwargs), total=len(ids)):
        results.append(result)
    return results

@wait_after(REQUEST_WAIT)
def _get_paper_by_title_with_session(session: Session, title: str, fields: list[str]=default_fields, **kwargs):
    headers = {'X-API-KEY': S2_API_KEY}
    params = {'query': title, 'fields': ','.join(fields), **kwargs}
    with session.get('https://api.semanticscholar.org/graph/v1/paper/search/match', params=params, headers=headers) as response:
                if response.status_code == 404:
                    return None
                else:
                    response.raise_for_status()
                    return response.json()['data'][0]

def get_papers_by_title(title: str, fields: list[str]=default_fields, session: Session=None, **kwargs) -> list[dict]:
    if session is None:
        with Session() as session:
            _get_paper_by_title_with_session(session, title, fields=fields, **kwargs)
    else:
        _get_paper_by_title_with_session(session, title, fields=fields, **kwargs)

def get_papers_by_title(titles: list[str], fields: list[str]=default_fields, **kwargs) -> list[dict]:
    results = []
    with Session() as session:
        for title in tqdm.tqdm(titles):
            result = _get_paper_by_title_with_session(session, title, fields=fields, **kwargs)
            results.append(result)
    return results

@wait_after(REQUEST_WAIT)
def _get_links_by_id_with_session(session: Session, id: str, get_keyword: str, offset: int=0, limit: int=100, fields: list[str] = default_fields,  **kwargs):
    params = {'fields': ','.join(fields), **kwargs, 'offset': offset, 'limit': limit}
    headers = {'X-API-KEY': S2_API_KEY}
    print(headers)
    with session.get(f'https://api.semanticscholar.org/graph/v1/paper/CorpusId:{id}/{get_keyword}',
                       params=params,
                       headers=headers
                       ) as response:
        response.raise_for_status()
        return response.json()

def _get_links_by_id_batched(id, get_keyword: str, batch_size: int = 100, **kwargs):
    # use a session to reuse the same TCP connection
    with Session() as session:
        # take advantage of S2 batch paper endpoint
        offset = 0
        while offset is not None:
            result = _get_links_by_id_with_session(session, id, get_keyword, offset, batch_size, **kwargs)
            offset = result.get('next', None)
            yield from result['data']

class DictNoDefault(addict.Dict):
    def __missing__(self, key):
        raise KeyError(key)

def get_bibs_by_id_batched(id:str, fields: list[str]=default_reference_fields, batch_size: int = 100, as_addict=False, **kwargs):
    results = []
    for result in tqdm.tqdm(_get_links_by_id_batched(id, get_keyword='references', fields=fields, batch_size=batch_size, **kwargs)):
        results.append(result)
    if as_addict:
        return [DictNoDefault(res) for res in results]
    return results

def get_cites_by_id_batched(id:str, fields: list[str]=default_reference_fields, batch_size: int = 100, as_addict=False, **kwargs):
    results = []
    for result in tqdm.tqdm(_get_links_by_id_batched(id, get_keyword='citations', fields=fields, batch_size=batch_size, **kwargs)):
        results.append(result)
    if as_addict:
        return [DictNoDefault(res) for res in results]
    return results

if __name__ == '__main__':
    print(get_papers_by_ids_batched([229348988, 10421567]))
    print(get_papers_by_title(['A distributional approach to controllable text generation', 'Illinois-LH: A Denotational and Distributional Approach to Semantics']))
    bibs = get_bibs_by_id_batched(229348988)
    print(len(bibs))
    breakpoint()