import zipfile
import xml.etree.ElementTree

import lxml


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
TEI_NAMESPACE = {'tei': 'http://www.tei-c.org/ns/1.0'}


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
            row_text = get_elem_text(row, format_dict)
            data, metadata_is_over = treat_row_text(
                row_text, data, metadata_is_over, field_norm
            )
    if data.get('meta_id') is None:
        data['meta_id'] = data['file_id']
        print(f'No ID found in file {path.stem}')
    return data


def parse_epist(path, field_norm):
    format_dict = DOC_FORMATS[path.suffix.lower()]

    with zipfile.ZipFile(path) as doc:
        tree = xml.etree.ElementTree.XML(doc.read(format_dict['content_file']))

    data = {'file_id': path.stem}
    for table in tree.iter(format_dict['TABLE']):
        cell_iter = table.iter(format_dict['CELL'])
        while 'raw_text' not in data:
            field = get_elem_text(next(cell_iter), format_dict)
            content = get_elem_text(next(cell_iter), format_dict)
            if field in field_norm:
                data[field_norm[field]] = content
    return data


def get_elem_text(elem, format_dict):
    elem_text = '\n'.join(
        ''.join(t for t in p.itertext())
        for p in elem.iter(format_dict['PARA'])
    )
    # Strip \n for case in which there are additional empty cells on same row.
    return elem_text.strip('\n')


def treat_row_text(row_text, data, metadata_is_over, field_norm):
    if row_text.strip().lower() == 'transcripción paleográfica':
        metadata_is_over = True
    elif not metadata_is_over:
        field_split = row_text.split(':')
        field = field_split[0]
        if len(field_split) >= 2 and field in field_norm:
            data[field_norm[field]] = ''.join(field_split[1:]).strip()
    elif 'raw_text' not in data:
        data['raw_text'] = row_text
    return data, metadata_is_over


def parse_ps(path, ns=TEI_NAMESPACE, **process_token_kw):
    tree = lxml.etree.parse(path)

    data = {'file_id': path.stem.split('_')[0]}
    data['meta_id'] = data['file_id'] # no better option it seems

    header = tree.find('tei:teiHeader', ns)
    data['abstract'] = getattr(header.find('.//tei:summary', ns), 'text', '')

    # keywords = header.find('.//tei:keywords', ns).findall('tei:term', ns)
    # data['keywords'] = ', '.join([getattr(e, 'text') for e in keywords])
    keywords = header.find('.//tei:keywords', ns)
    data['keywords'] = ', '.join([t.strip(' \n\t') for t in keywords.itertext()])

    sender = header.find(".//tei:correspAction[@type='sent']", ns)
    data['author'] = sender.find('tei:persName', ns).text
    place_elems = sender.find('tei:location/tei:placeName', ns).text.split(', ')
    if len(place_elems) == 1:
        data['locality'] = place_elems[0]
    else:
        data['country'], data['region'] = place_elems[:2]
        if len(place_elems) == 3:
            data['region'] = place_elems[2]
    data['date'] = sender.find('tei:date', ns).attrib.get('when', '')

    letter_type = header.find(".//tei:catRef[@scheme='psodd:ps_type']", ns).attrib.get('target', '').split(':')[-1]
    content_type = header.find(".//tei:catRef[@scheme='psodd:ps_pragmatics']", ns).attrib.get('target', '').split(':')[-1]
    data['doc_type'] = f'{letter_type} letter, for {content_type}'

    body = tree.find('tei:text/tei:body', ns)
    possible_parts = ['opener', 'p', 'closer', 'postscript/tei:p']
    parts = body.xpath(' | '.join(f'./tei:{p}' for p in possible_parts), namespaces=ns)

    paragraphs = []
    for p_elem in parts:
        p = process_paragraph(p_elem, ns, **process_token_kw)
        paragraphs.append(p)

    data['text'] = '\n\n'.join(paragraphs)
    return data


def process_paragraph(p_elem, ns, **process_token_kw):
    ns_key = list(ns.keys())[0]
    tag_format = f"{{{{{ns[ns_key]}}}}}{{}}"
    w = tag_format.format('w')
    pc = tag_format.format('pc')
    lb = tag_format.format('lb')
    p = ''

    for elem in p_elem.xpath(
        './/tei:w[not(ancestor::tei:w)] | .//tei:lb[not(ancestor::tei:w)] | .//tei:pc',
        namespaces=ns
    ):
        p += process_token(elem, ns, w, pc, lb, **process_token_kw)

    return p


def process_token(elem, ns, w, pc, lb, expand=False, capitalize=False):
    token = ''
    is_w = elem.tag == w
    # expand_choice_tag = 'expan' if expand else 'abbr'

    if is_w or elem.tag == pc:
        prev_space = ' ' if is_w else ''
        has_hyphen = elem.find('.//tei:lb', ns) is not None
        choices = elem.find('tei:choice', ns)
        if choices is not None:
            # TODO: when reg starts with capital letter and orig does not, take reg?
            choice_dict = {
                e.tag.split('}')[1]: ''.join(t.strip('\n\t ') for t in e.itertext())
                for e in choices.findall('./')
            }
            # is_abbr = 'abbr' in choice_dict
            # if is_abbr and expand:
            #     token = choice_dict.get('expan', choice_dict['abbr'])
            # elif not is_abbr and capitalize:
            #     token = choice_dict.get('reg', choice_dict['orig'])
            # else:
            #     token = choice_dict.get('orig') or choice_dict.get('abbr')
            original = choice_dict.get('orig', '') or choice_dict.get('abbr', '')
            normed = choice_dict.get('reg', '')
            expanded = choice_dict.get('expan')
            if expand and expanded is not None:
                token = expanded
            elif capitalize and normed.lower() == original:
                token = normed
            else:
                token = original
                if token == '' and elem.tag != pc:
                    print(choices.findall('.//'))

            # for c in choices.xpath(f'./tei:orig | ./tei:{expand_choice_tag}', namespaces=ns):
            #     # if c.text is None:
            #     #     c = c.find('tei:supplied', ns)
            #         # token = ''.join(
            #         #     t.strip('\n\t ') for t in .itertext()
            #         # )
            #     token = ''.join(t.strip('\n\t ') for t in c.itertext())

        elif not has_hyphen:
            # In this case itertext would get the sub <w> tags corresponding to the
            # decomposition in word parts (eg: del: de el). Also for some reason
            # when there are these sub parts the elem.text is padded with a \n and
            # several \t, which are not part of the original text, so we strip them
            # off.
            if elem.text is None:
                supplied = elem.findall('.//tei:supplied', ns)
                for s in supplied:
                    if s.text is not None:
                        token += s.text.strip('\n\t ')
            else:
                token = elem.text.strip('\n\t ')

        else:
            # if hyphen, using itertext is the only way I found to get the text
            # after the  <lb>
            token = ''.join([t.strip('\n\t ') for t in elem.itertext()])

        token = prev_space + token + has_hyphen * '\n'

    elif elem.tag == lb:
        token = '\n'

    return token
