from __future__ import annotations

import html
import os
from functools import lru_cache
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple, Union

import requests
from django.conf import settings

LanguageCode = str
Translations = Dict[str, str]

COUNTRY_LANGUAGE_MAP: Dict[str, LanguageCode] = {
    "czech": "cs",
    "czech republic": "cs",
    "czechia": "cs",
    "cesko": "cs",
    "slovak": "sk",
    "slovakia": "sk",
    "slovak republic": "sk",
}


def _normalize_country(value: Union[str, None]) -> str:
    if not value:
        return ""
    return value.strip().lower()


def get_language_for_country(country: Union[str, None]) -> Union[LanguageCode, None]:
    normalized = _normalize_country(country)
    if not normalized:
        return None
    for key, code in COUNTRY_LANGUAGE_MAP.items():
        if key in normalized:
            return code
    return None


def _get_api_key() -> Union[str, None]:
    return (
        getattr(settings, "GOOGLE_TRANSLATE_API_KEY", None)
        or os.environ.get("GOOGLE_TRANSLATE_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )


def _translate_list(values: Sequence[str], target_language: LanguageCode) -> List[str]:
    if not values:
        return list(values)

    api_key = _get_api_key()
    if not api_key:
        return list(values)

    endpoint = "https://translation.googleapis.com/language/translate/v2"
    payload = {
        "q": list(values),
        "target": target_language,
        "format": "text",
        "source": "en",
        "key": api_key,
    }

    try:
        response = requests.post(endpoint, data=payload, timeout=6)
        response.raise_for_status()
        data = response.json()
        translations = data.get("data", {}).get("translations", [])
        if len(translations) != len(values):
            return list(values)
        return [html.unescape(item.get("translatedText", original)) for item, original in zip(translations, values)]
    except Exception:
        return list(values)


@lru_cache(maxsize=256)
def _translate_tuple(values_tuple: Tuple[str, ...], target_language: LanguageCode) -> Tuple[str, ...]:
    translated = _translate_list(list(values_tuple), target_language)
    return tuple(translated)


def translate_strings(strings: Mapping[str, str], target_language: Union[LanguageCode, None]) -> Translations:
    if not target_language:
        return dict(strings)
    keys = tuple(strings.keys())
    values_tuple = tuple(strings[key] for key in keys)
    translated_tuple = _translate_tuple(values_tuple, target_language)
    return {key: value for key, value in zip(keys, translated_tuple)}


def translate_sequence(sequence: Iterable[str], target_language: Union[LanguageCode, None]) -> List[str]:
    values = list(sequence)
    if not target_language:
        return values
    translated_tuple = _translate_tuple(tuple(values), target_language)
    return list(translated_tuple)


def should_localize(country: Union[str, None]) -> bool:
    return get_language_for_country(country) is not None


