import re
from functools import lru_cache
from typing import List

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

SLANG_MAP = {
    "gk": "tidak", "ga": "tidak", "nggak": "tidak", "ngga": "tidak",
    "tdk": "tidak", "bgt": "banget", "bgtt": "banget", "dgn": "dengan",
    "yg": "yang", "dr": "dari", "krn": "karena", "aja": "saja",
    "udh": "sudah", "sdh": "sudah", "blm": "belum", "bikin": "buat",
    "mantul": "mantap", "gaje": "tidak_jelas", "btw": "omong_omong",
    "klo": "kalau", "kl": "kalau", "jg": "juga", "utk": "untuk",
    "tp": "tapi", "dpt": "dapat", "sy": "saya", "gw": "saya",
    "gue": "saya", "lu": "kamu", "km": "kamu", "org": "orang",
    "trs": "terus", "sm": "sama", "pdhl": "padahal", "rt": "",
}

CUSTOM_STOPWORDS = {
    "nya", "nih", "dong", "sih", "deh", "ya", "kok", "lah", "pun",
    "jadi", "buat", "para", "agar", "biar", "guna", "sebuah"
}

@lru_cache(maxsize=1)
def _stemmer():
    return StemmerFactory().create_stemmer()

@lru_cache(maxsize=1)
def _stopwords():
    factory = StopWordRemoverFactory()
    return set(factory.get_stop_words()) | CUSTOM_STOPWORDS


def clean_text(text: str) -> str:
    text = str(text)
    text = text.lower()
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"#(\w+)", r" \1 ", text)
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_tokens(tokens: List[str]) -> List[str]:
    return [SLANG_MAP.get(token, token) for token in tokens if token]


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z_]+", text)


def preprocess_text(text: str) -> str:
    text = clean_text(text)
    tokens = tokenize(text)
    tokens = normalize_tokens(tokens)
    stopwords = _stopwords()
    tokens = [t for t in tokens if t not in stopwords and len(t) > 1]
    stemmer = _stemmer()
    stems = [stemmer.stem(token) for token in tokens]
    return " ".join(stems)
