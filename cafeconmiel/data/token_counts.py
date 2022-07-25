import re

import pandas as pd

WORD_PATT = re.compile(r'\b[^\W\d_]+?\b')

def count_by_doc(doc_df):
    words_count_by_doc = (
        doc_df['text']
         .str.findall(WORD_PATT)
         .explode()
         .rename('word')
         .to_frame()
         .groupby([doc_df.index.name, 'word'])
         .size()
         .rename('count')
         .to_frame()
    )
    words_count_by_doc['word_lower'] = (
        words_count_by_doc.index.get_level_values(level='word').str.lower()
        
    )
    return words_count_by_doc


def doc_counts_to_global(words_count_by_doc):
    global_counts = words_count_by_doc.groupby('word')[['count']].sum()
    global_counts['word_lower'] = global_counts.index.str.lower()
    not_lower = global_counts.index != global_counts['word_lower']
    global_counts.loc[not_lower, 'count_upper'] = (
        global_counts.loc[not_lower, 'count']
    )
    # Here we can round and cast to int, because if everything was previously
    # done correctly (and this makes for a nice test), summing over all cells
    # should give an integer, as counts from bbox places should be entirely
    # spread among intersected cells.
    global_counts = (
        global_counts.groupby('word_lower')
         .sum()
         .rename_axis('word_lower')
         .round()
         .astype(int)
         .sort_values(by='count', ascending=False)
    )
    global_counts['prop_upper'] = global_counts['count_upper'] / global_counts['count']
    global_counts['nr_docs'] = (
        words_count_by_doc.groupby(['meta_id', 'word_lower'])
         .first()
         .groupby('word_lower')
         .size()
    )
    nr_docs = words_count_by_doc.index.levshape[0]
    global_counts['doc_freq'] = global_counts['nr_docs'] / nr_docs
    return global_counts


def word_mask(global_counts, min_df=1, max_df=1., upper_th=1.1):
    min_df_col = 'nr_docs' if isinstance(min_df, int) else 'doc_freq'
    max_df_col = 'nr_docs' if isinstance(max_df, int) else 'doc_freq'
    global_counts['word_mask'] = (
        (global_counts['prop_upper'] < upper_th)
        & (global_counts[min_df_col] >= min_df)
        & (global_counts[max_df_col] <= max_df)
    ).rename('word_mask')
    return global_counts


def filter_doc_counts(words_count_by_doc, word_mask):
    filtered_words_count_by_doc = (
        words_count_by_doc.groupby(['meta_id', 'word_lower'])[['count']]
         .sum()
         .join(word_mask.loc[word_mask], how='inner')
    )
    return filtered_words_count_by_doc


def char_ngrams(filtered_words_count_by_doc, global_counts, min_n=1, max_n=1):
    # Get a dict of all the characters ngrams present in each word of the vocabulary.
    kept_words = global_counts.loc[global_counts['word_mask']].index

    if min_n == 1:
        nchar_dict = {w: list(w) for w in kept_words}
        min_n += 1
    else:
        nchar_dict = {w: list() for w in kept_words}
    
    for w in kept_words:
        for n in range(min_n, max_n+1):
            for i in range(len(w) - n + 1):
                nchar_dict[w].append(w[i : i + n])

    word_char_ngrams = pd.Series(nchar_dict).explode().rename('char_ngram')
    midx = pd.MultiIndex.from_arrays(
        [word_char_ngrams.index, word_char_ngrams.values],
        names=['word_lower', 'char_ngram'],
    )
    # Count the number of occurences of each character ngram in each word.
    count_ncgrams_in_words = pd.Series(
        1, name='count', index=midx
    ).groupby(['word_lower', 'char_ngram']).sum()
    # Join these counts with the word counts by document computed previously. 
    ngram_doc_counts = (
        filtered_words_count_by_doc.rename(columns={'count': 'word_count'})
         .join(count_ncgrams_in_words)
    )
    # For each word, multiply its count by number of times each character ngram appears
    # in it, then sum by doc and ngram to get the final result.
    ngram_doc_counts = (
        ngram_doc_counts['count'].multiply(ngram_doc_counts['word_count'])
         .groupby(['meta_id', 'char_ngram'])
         .sum()
         .rename('count')
         .astype(int)
         .to_frame()
    )
    return ngram_doc_counts
