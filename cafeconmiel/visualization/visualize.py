import matplotlib.pyplot as plt
import seaborn as sns

import cafeconmiel.utils.paths as paths_utils


class TranslationDict(dict):
    def __missing__(self, key):
        return key


def heatmap(
    freq_df, #xticks_labels, yticks_labels,
    save_fname=None, freq_mult=1, token_sums=None, lang_vocab=None, corpus_name='all'
):
    if lang_vocab is None:
        lang_vocab = TranslationDict()

    if token_sums is None:
        plot_df = freq_df
        fmt = ',d'
        cbar_label = f"{lang_vocab['occurrences']}"
    else:
        freq_mult = int(freq_mult)
        plot_df = freq_mult * (freq_df.T / token_sums).T
        fmt = '.1f'
        cbar_label = f"{lang_vocab['occurrences']} {lang_vocab['per']} {freq_mult:,d} {lang_vocab['tokens']}".replace(',', ' ')

    fig, ax = plt.subplots()
    ax = sns.heatmap(
        plot_df, cmap='Blues', cbar_kws={'label': cbar_label},
        annot=True, fmt=fmt, ax=ax,
    )
    ax.set_xlabel('')
    ax.set_ylabel('')
    # ax.xaxis.set_ticklabels(xticks_labels)
    # ax.yaxis.set_ticklabels(yticks_labels)
    fig.show()
    if save_fname is not None:
        save_dir_path = paths_utils.format_path(
            paths_utils.ProjectPaths().charact_words_freqs, corpus_name=corpus_name
        )
        fig.savefig(save_dir_path / save_fname)
    return ax
