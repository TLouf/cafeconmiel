
from itertools import chain

import pandas as pd


def integrate_revisions(raw_docs_df, revised_dirs):
    revised_dict = {'meta_id': [], 'text': []}
    revised_doc_iter = chain(*[p.iterdir() for p in revised_dirs])
    for p in revised_doc_iter:
        if not p.name.lower().startswith('xxx') and p.suffix == '.txt':
            revised_dict['meta_id'].append(p.stem)
            revised_dict['text'].append(p.read_text())
    revised_texts = pd.DataFrame.from_dict(revised_dict).set_index('meta_id')
    print(f'integrated {revised_texts.shape[0]} revised texts')
    docs_df = raw_docs_df[raw_docs_df.columns[raw_docs_df.columns != 'text']].join(revised_texts, how='inner')
    return docs_df
