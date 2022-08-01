import itertools
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


def seseo_corr(w, dictionary):
    list_s = ['s', 'z', 'c']
    matches = list(re.finditer(r'(s)|(z)|(ci)|(ce)', w))
    nr_matches = len(matches)
    if nr_matches > 0 and w not in dictionary:
        list_switches = []
        for m in matches:
            grps = m.groups()
            idx_match_group = [i for i in range(len(grps)) if grps[i] is not None][0]
            start, end = m.span()
            if end - start == 2: # ci or ce
                next_char = w[end - 1]
            elif end < len(w):
                next_char = w[end]
            else:
                next_char = ''

            if next_char == '': # end of word
                # can only be matched if last statement above is true
                switch_to_idc = [1 - idx_match_group] # 0 -> 1 or 1 -> 0
            elif next_char in ('i', 'e'): 
                # can be matched when one of first two statements above is true
                switch_to_idc = [i for i in range(3) if i != idx_match_group]
            else: # followed by a, o, u or consonant
                # can only be matched when second statement above is true
                switch_to_idc = [1 - idx_match_group]
            list_switches.append(switch_to_idc)

        for nr_subs in range(1, nr_matches + 1):
            # depending on number of substitutions (subs) you do at once, you'll have
            # different subsets of matches the subs will occur on
            subsets_of_matches_to_sub = list(
                itertools.combinations(range(nr_matches), nr_subs)
            )
            for m_idc in subsets_of_matches_to_sub:
                # For one subset of matches, there can be more different subs
                # to perform than the size of the subset, as for some matches
                # ((s|z|c)(i|e)) there are 2 different subs that can be made.
                possible_s_indices = list(
                    itertools.product(*[list_switches[m_idx] for m_idx in m_idc])
                )

                # This time, one mod_w per iter of next loop:
                for s_idc in possible_s_indices:
                    # Reset to original word and perform all `nr_subs` subs
                    mod_w = w
                    seseo_pos = []
                    for m_idx, s_idx in zip(m_idc, s_idc):
                        m = matches[m_idx]
                        seseo_pos.append(str(m.start()))
                        s = list_s[s_idx]
                        mod_w = mod_w[:m.start()] + s + mod_w[m.start() + 1:]

                    if mod_w in dictionary:
                        return mod_w, ', '.join(seseo_pos)

    return None, None
