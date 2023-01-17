from itertools import combinations
import re

import numpy as np
import pandas as pd

import cafeconmiel.utils.paths as paths_utils

 
def get_freq_df(docs_text, clust_mask, variants, yticks_labels):
    regexes = [
        r'\b(' + v.replace(', ', '|').replace(',', '|') + r')\b'
        for v in variants.values()
    ]
    res = np.array([
        [docs_text.loc[clust_mask].str.count(r).sum() for r in regexes],
        [docs_text.loc[~clust_mask].str.count(r).sum() for r in regexes],
    ])
    freq_df = pd.DataFrame(
        res,
        columns=pd.Index(list(variants.keys()), name='forms'),
        index=pd.Index(yticks_labels, name='origin')
    )
    return freq_df

def freq_to_polar_df(freq_df):
    polar_df = freq_df.copy()
    for c in combinations(freq_df.columns, 2):
        polar_df[f"polar_{c[0]} - {c[1]}"] = (
            (polar_df[f'{c[0]}'] - polar_df[f'{c[1]}'])
            / (polar_df[f'{c[0]}'] + polar_df[f'{c[1]}'])
        )
    polar_df = polar_df.loc[:, polar_df.columns.str.startswith('polar')].rename_axis('variants', axis=1)
    polar_df.columns = polar_df.columns.str.removeprefix('polar_')
    return polar_df


def get_context_df(docs_text, docs_df, variants, save=True, corpus_name='all'):
    all_matches_df = pd.DataFrame()
    for f, v in variants.items():
        capt_r = r'(\b' + f"({v.replace(', ', '|').replace(',', '|')})".replace('(', '(?:') + r'\b)'
        matches_dict = {'meta_id': [], 'match': [], 'context': []}
        for doc_id, t in docs_text.iteritems():
            matches = re.finditer(capt_r, t)
            for m in matches:
                matches_dict['meta_id'].append(doc_id)
                matches_dict['match'].append(m.group())
                matches_dict['context'].append('...' + t[m.start() - 10: m.end() + 10]+ '...')
        matches_df = pd.DataFrame(matches_dict).set_index('meta_id').join(
            docs_df[['corpus', 'doc_type', 'is_bal']]
        )
        print(f, matches_df['match'].unique())
        all_matches_df = pd.concat([all_matches_df, matches_df])
        if save:
            save_dir_path = paths_utils.format_path(
                paths_utils.ProjectPaths().charact_words_freqs, corpus_name=corpus_name
            )
            matches_df.to_csv(save_dir_path / f'{f}.csv')
    
    return all_matches_df
