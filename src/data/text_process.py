import re

def clean(text, space_after_newline=True):
    text = text.replace('>', '').replace('<', '')
    text = re.sub(r'\{.*\}', '', text)
    # remove (potentially) nested square brackets content: for the moment stars and latin
    text = re.sub(r'\[[\*]{3}\]', '', text)
    text = re.sub(r'\[.*?\]', '', text, flags=re.DOTALL)
    # reassemble words split by end of line hyphenations
    text = re.sub(r'(\w+)\-\n(\w+)', r'\n\g<1>\g<2>', text)
    if space_after_newline:
        text = re.sub(r'(\w+)\n(\w+)', r'\n\g<1>\g<2>', text)
    return text
