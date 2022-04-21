import re

def remove_match_group(sentence, match, group=1):
    new_s = ''
    lbound = 0
    l, h = match.span(group)
    new_s += sentence[lbound:l]
    lbound = h
    new_s += sentence[h:]
    return new_s


def extract_text(text_soups: list):
    text = ''
    for soup in text_soups:
        new_page = False
        iterator = soup.contents
        if len(iterator) == 1:
            iterator = iterator[0].children
        for s in iterator:
            if isinstance(s, str):
                if new_page and s.strip() != '':
                    last_word_match = re.match(r'.*\b([\w]+)[- ]*$', text, flags=re.DOTALL)
                    if last_word_match is not None:
                        new_page = False
                        last_word = last_word_match.groups()[0]
                        repeated_last = re.match(r'({}\w*)\b'.format(last_word), s.strip())
                        # print('b', last_word, repeated_last, s)
                        if repeated_last is not None and len(repeated_last.groups()[0]) > 2:
                            print(f'{text[slice(*last_word_match.span(1))]} replaced with {s}')
                            text = remove_match_group(text, last_word_match)
                text += s
            elif s.get('class') == ['linea']:
                text += '\n'
            # if new page, delimited by link to page image, and it's not the first one:
            elif s.name == 'a':
                if len(text) > 0:
                    new_page = True
            elif s.text is not None:
                text += s.text

    return text


def extract_metadata(soup, meta_fields, locale_month_name_to_number):
    metadata = {}
    for i, elem in enumerate(soup.find_all(class_='cab')):
        field = meta_fields[i]
        text = elem.text
        elems_in_field = field.split(' ')
        if field == 'date (place)':
            date, place = re.match(r'(.*) \((.*)\)', text).groups()
            metadata['place'] = place
            date_patt = r'([0-9]{4}) (.*) (.*)'
            date_elems_match = re.match(date_patt, date.replace('?', ''))
            if date_elems_match is not None:
                year, month, day = date_elems_match.groups()
            # get original if not in normalised names to see what's wrong a posteriori
                month_nr = locale_month_name_to_number.get(month.lower(), month)
                normed_date = '-'.join([year, month_nr, day.zfill(2)])
            else:
                print(f'{date} not matching format')
                normed_date = date.replace('?', '')
            metadata['date'] = normed_date
        else:
            metadata[field] = text

    metadata['revisors'] = [elem.text for elem in soup.find_all(class_='revisor')]
    return metadata
