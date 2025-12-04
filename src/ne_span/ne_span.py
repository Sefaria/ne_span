from abc import ABC, abstractmethod
from functools import cached_property
from .tokenizer import get_tokenizer
from enum import Enum

TOKENIZER = get_tokenizer()

# keys correspond named entity labels in the models
# values are properties in RefPartType
LABEL_TO_REF_PART_TYPE_ATTR = {
    # HE
    "כותרת": 'NAMED',
    "מספר": "NUMBERED",
    "דה": "DH",
    "סימן-טווח": "RANGE_SYMBOL",
    "לקמן-להלן": "RELATIVE",
    "שם": "IBID",
    "לא-רציף": "NON_CTS",
    # EN
    "title": 'NAMED',
    "number": "NUMBERED",
    "DH": "DH",
    "range-symbol": "RANGE_SYMBOL",
    "dir-ibid": "RELATIVE",
    "ibid": "IBID",
    "non-cts": "NON_CTS",
}


# keys correspond named entity labels in spacy models
# values are properties in NamedEntityType
LABEL_TO_NAMED_ENTITY_TYPE_ATTR = {
    # HE
    "מקור": "CITATION",
    "בן-אדם": "PERSON",
    "קבוצה": "GROUP",
    # EN
    "Person": "PERSON",
    "Group": "GROUP",
    "Citation": "CITATION",
}


class NamedEntityType(Enum):
    PERSON = "person"
    GROUP = "group"
    CITATION = "citation"

    @classmethod
    def span_label_to_enum(cls, span_label: str) -> 'NamedEntityType':
        """
        Convert span label from spacy named entity to NamedEntityType
        """
        return getattr(cls, LABEL_TO_NAMED_ENTITY_TYPE_ATTR[span_label])


class RefPartType(Enum):
    NAMED = "named"
    NUMBERED = "numbered"
    DH = "dibur_hamatchil"
    RANGE_SYMBOL = "range_symbol"
    RANGE = "range"
    RELATIVE = "relative"
    IBID = "ibid"
    NON_CTS = "non_cts"

    @classmethod
    def span_label_to_enum(cls, span_label: str) -> 'RefPartType':
        """
        Convert span label from spacy named entity to RefPartType
        """
        return getattr(cls, LABEL_TO_REF_PART_TYPE_ATTR[span_label])


class _Subspannable(ABC):
    """
    Abstract base class for objects that contain text and can be subspanned (meaning, they can be sliced to create smaller spans).
    """

    @property
    @abstractmethod
    def text(self) -> str:
        pass

    @property
    @abstractmethod
    def doc(self) -> 'NEDoc':
        pass

    def word_length(self) -> int:
        """
        Returns the number of words in the text.
        Words are defined as runs of non-whitespace characters.
        """
        return len(self.__word_spans)

    def subspan(self, item: slice, span_label: str = None) -> 'NESpan':
        if isinstance(item, slice):
            start = item.start or 0
            end = item.stop
        else:
            raise TypeError("Item must be a slice")
        return NESpan(self, start, end, span_label)

    @cached_property
    def __word_spans(self):
        doc = TOKENIZER(self.text)
        # extract start and end character indices of each word
        spans = [(token.idx, token.idx+len(token)) for token in doc if not token.is_space]
        return spans

    def subspan_by_word_indices(self, word_slice: slice) -> 'NESpan':
        """
        Return an NESpan covering words [start_word, end_word), where words
        are runs of non-whitespace. 0-based, end_word is exclusive.
        """
        spans = self.__word_spans
        word_span_slice = spans[word_slice]
        if not word_span_slice:
            if word_slice.start is not None and word_slice.start > len(spans):
                raise IndexError(f"Word indices out of range: {word_slice}. Document has {len(self.__word_spans)} words.")
            # slice is empty, return a span of zero length
            start_char = end_char = 0
        else:
            start_char = word_span_slice[0][0]
            end_char = word_span_slice[-1][1]
        return self.subspan(slice(start_char, end_char))


class NEDoc(_Subspannable):

    def __init__(self, text: str):
        self.__text = text

    @property
    def text(self) -> str:
        return self.__text

    @property
    def doc(self):
        return self


class NESpan(_Subspannable):
    """
    Span of text which represents a named entity before it has been identified with an object in Sefaria's DB
    """
    def __init__(self, doc: _Subspannable, start: int, end: int, label: str = None):
        """
        :param doc: The document containing the text
        :param start: Start index of the span in the text
        :param end: End index of the span in the text
        :param label
        """
        self.__doc = doc
        self.__start = start or 0
        self.__end = end if end is not None else len(doc.text)
        self.__label = label

    def __str__(self):
        return f"NESpan(text='{self.text}', label='{self.label}', range={self.range})"

    @property
    def doc(self) -> _Subspannable:
        return self.__doc

    @property
    def text(self) -> str:
        return self.__doc.text[self.__start:self.__end]

    @property
    def label(self) -> str:
        return self.__label

    @property
    def range(self) -> tuple[int, int]:
        return self.__start, self.__end
    
    def get_range_relative_to_doc(self) -> tuple[int, int]:
        """
        Get the range of the span relative to the root document.
        :return: A tuple (start, end) representing the range in the root document.
        """
        parent_span = self.doc
        start, end = self.range
        while hasattr(parent_span, "range"):
            start += parent_span.range[0]
            end += parent_span.range[0]
            parent_span = parent_span.doc
        return start, end

    def __hash__(self):
        return hash((self.__doc.text, self.__start, self.__end, self.__label))

    def serialize(self, with_text=False) -> dict:
        """
        Serialize the NESpan to a dictionary.
        :param with_text: If True, include the text of the span in the serialization.
        :return: A dictionary representation of the NESpan.
        """
        data = {
            "range": self.range,
            "label": self.__label
        }
        if with_text:
            data["text"] = self.text
        return data
