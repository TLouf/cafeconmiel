import re

def clean(text, space_after_newline=True):
    text = text.replace('>', '').replace('<', '').replace('|', '')
    # Remove (potentially nested) square and curly brackets' content.
    text = re.sub(r'\{.*?\}', '', text)
    # Add match with DOTALL flag to also remove multi-line brackets.
    text = re.sub(r'\{.*?\}', '\n', text, flags=re.DOTALL)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\[.*?\]', '\n', text, flags=re.DOTALL)
    # Reassemble words split by end of line hyphenations
    text = re.sub(r'(\w+)\-\s{,1}\n\s{,1}(\w+)', r'\n\g<1>\g<2>', text)
    if space_after_newline:
        text = re.sub(r'(\w+)\n(\w+)', r'\n\g<1>\g<2>', text)
    # Else we don't know if hyphenation or not... most of the time it's not though, so
    # we don't do anything
    return text


def set_sub(m: re.Match, s: set):
    return '' if m.group() in s else m.group()


def remove_from_list(text, pattern, replace_list):
    # from https://stackoverflow.com/a/30606171/13168978
    s = set(replace_list)
    repl_func = lambda m: set_sub(m, s)
    return re.sub(pattern, repl_func, text)
