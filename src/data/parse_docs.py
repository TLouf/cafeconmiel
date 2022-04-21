import zipfile
import xml.etree.ElementTree

WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
ODT_NAMESPACE = '{{urn:oasis:names:tc:opendocument:xmlns:{env}:1.0}}{elem}'
DOC_FORMATS = {
    '.docx': {
        'TABLE': WORD_NAMESPACE + 'tbl',
        'ROW': WORD_NAMESPACE + 'tr',
        'CELL': WORD_NAMESPACE + 'tc',
        'PARA': WORD_NAMESPACE + 'p',
        'TEXT': WORD_NAMESPACE + 't',
        'content_file': 'word/document.xml',
    },
    '.odt': {
        'TABLE': ODT_NAMESPACE.format(env='table', elem='table'),
        'COLUMN': ODT_NAMESPACE.format(env='table', elem='table-column'),
        'ROW': ODT_NAMESPACE.format(env='table', elem='table-row'),
        'CELL': ODT_NAMESPACE.format(env='table', elem='table-cell'),
        'PARA': ODT_NAMESPACE.format(env='text', elem='p'),
        'content_file': 'content.xml',
    }
}

def parse(path, field_norm):
    format_dict = DOC_FORMATS[path.suffix.lower()]

    with zipfile.ZipFile(path) as doc:
        tree = xml.etree.ElementTree.XML(doc.read(format_dict['content_file']))

    metadata_is_over = False
    data = {'file_id': path.stem}
    for table in tree.iter(format_dict['TABLE']):
        row_iter = table.iter(format_dict['ROW'])
        while 'raw_text' not in data:
            row = next(row_iter)
            # Strip \n for case in which there are additional empty cells on same row.
            cell_text = '\n'.join(
                ''.join(t for t in p.itertext())
                for p in row.iter(format_dict['PARA'])
            ).strip('\n')
            data, metadata_is_over = treat_cell_text(
                cell_text, data, metadata_is_over, field_norm
            )
    return data


def treat_cell_text(cell_text, data, metadata_is_over, field_norm):
    if cell_text.strip().lower() == 'transcripción paleográfica':
        metadata_is_over = True
    elif not metadata_is_over:
        field_split = cell_text.split(':')
        field = field_split[0]
        if len(field_split) >= 2 and field in field_norm:
            data[field_norm[field]] = ''.join(field_split[1:]).strip()
    elif 'raw_text' not in data:
        data['raw_text'] = cell_text
    return data, metadata_is_over
