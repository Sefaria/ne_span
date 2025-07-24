from spacy.lang.xx import MultiLanguage


def get_tokenizer():
    """
    language agnostic spacy tokenizer
    @return:
    """
    nlp = MultiLanguage()
    return nlp.tokenizer
