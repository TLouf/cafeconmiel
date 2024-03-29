

def normalize(df):
    if 'year' in df.columns:
        has_year = df['year'].notnull()
        df.loc[has_year, 'year'] = (
            df.loc[has_year, 'year'].str.extract(r'([0-9]{4})', expand=False)
            .astype(float)
        )
        if 'date' in df.columns:
            df.loc[~has_year, 'year'] = (
                df.loc[~has_year, 'date'].str.extract(r'([0-9]{4})', expand=False)
                .astype(float)
            )
    else:
        df['year'] = df['date'].str.extract(r'([0-9]{4})').astype(float)
    df['doc_type'] = df['doc_type'].str.lower().str.strip()

    place_cols = ['locality', 'region']
    if 'place' in df.columns:
        has_place = df['place'].notnull()
        df.loc[has_place, place_cols] = (
            df.loc[has_place, 'place']
             .str.split(', ', expand=True)
             .rename(columns={i: place_cols[i] for i in range(len(place_cols))})
        )
    for col in place_cols:
        df[col] = df[col].fillna('').str.strip(to_strip=' ?[]').str.title()
        df.loc[df[col].str.len() <= 1, col] = None

    df = df.drop(
        columns=['raw_text', 'unknown_id', 'revisors', 'century', 'nr_words', 'woman', 'context'],
        errors='ignore',
    )
    
    return df
