import re

'''
Rules / regex
Use for things like:
[EMAIL]
[PHONE]
[URL]
[IP]
[ACCOUNT_ID]
[ORDER_ID]
These are deterministic and fast.

'''


REGEX_RULES: dict[str, re.Pattern[str]] = {
    "EMAIL": re.compile(
        r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
    ),
    "PHONE": re.compile(
        r"\b(?:\+33|0)[1-9](?:[\s.\-]?\d{2}){4}\b"
    ),
    "URL": re.compile(
        r"\bhttps?://[^\s/$.?#].[^\s]*\b"
    ),
    "DATE": re.compile(
        r"\b(?:0?[1-9]|[12][0-9]|3[01])[\/\-.](?:0?[1-9]|1[0-2])[\/\-.](?:19|20)\d{2}\b"
    ),
    "POSTAL_CODE_FR": re.compile(
        r"\b\d{5}\b"
    ),
    "IPV4": re.compile(
        r"\b(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
        r"(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}\b"
    ),
    "NIR_FR": re.compile(
        r"\b[12]\s?\d{2}\s?(?:0[1-9]|1[0-2])\s?"
        r"(?:\d{2}|2A|2B)\s?\d{3}\s?\d{3}\s?\d{2}\b",
        re.IGNORECASE,
    ),
    "IBAN": re.compile(
        r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}[A-Z0-9]{0,4}\b"
    ),
    "LICENSE_PLATE": re.compile(
        r"\b[A-Z]{3}\s?\d{3}\b"
    ),
    "CREDIT_CARD": re.compile(
        r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|6(?:011|5[0-9]{2})[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11})\b"
    ),
    "health insurance" : re.compile(
        r"\b(?:[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}[A-Z0-9]{0,4}\b)"
    ),
    "IDENTITY_CARD" : re.compile(
        r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}[A-Z0-9]{0,4}\b"
    ),
    "SEPA_CREDIT_TRANSFER" : re.compile(
        r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|6(?:011|5[0-9]{2})[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11})\b"
    ),
    "SEPA_DIRECT_DEBIT" : re.compile(
        r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|6(?:011|5[0-9]{2})[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11})\b"
    ),
    "PASSPORT_CARD" : re.compile(
        r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}[A-Z0-9]{0,4}\b"
    ),
    "DRIVER_LICENSE" : re.compile(
        r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}[A-Z0-9]{0,4}\b"
    )

}


def find_regex_matches(text: str) -> list[dict[str, int | str]]:
    matches: list[dict[str, int | str]] = []

    for label, pattern in REGEX_RULES.items():
        for match in pattern.finditer(text):
            matches.append(
                {
                    "label": label,
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(),
                    "source": "regex"
                }
            )

    matches.sort(key=lambda item: (int(item["start"]), -(int(item["end"]) - int(item["start"]))))
    return matches