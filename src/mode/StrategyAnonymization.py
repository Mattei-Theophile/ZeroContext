from uuid import uuid4
from abc import ABC, abstractmethod
from nlp import AnonymizeResponse, _merge_entities
from rules.regex import find_regex_matches
import spacy


class StrategyAnonymization(ABC):
    def __init__(self, language: str = "fr"):
        self.language = language

    @abstractmethod
    def anonymize(self, text: str) -> AnonymizeResponse:
        pass

    def perform_anonymization(self, text: str) -> AnonymizeResponse:
        nlp = self.get_anonymization_pipeline()
        doc = nlp(text)

        transformer_matches = []
        for ent in doc.ents:
            transformer_matches.append({
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "text": ent.text,
                "source": "transformer",
            })

        regex_matches = find_regex_matches(text)

        all_matches = regex_matches + transformer_matches
        anonymized_text, match_table = self.anonymize_from_matches(text, all_matches)

        return AnonymizeResponse(
            uuid=str(uuid4()),
            originalText=text,
            anonymizedText=anonymized_text,
            matchTable=match_table,
            language=self.language
        )

    def get_anonymization_pipeline(self):
        nlp = spacy.blank(self.language)

        if "hf_ner_component" not in nlp.pipe_names:
            nlp.add_pipe("hf_ner_component", config={"language": self.language})

        return nlp

    @staticmethod
    def anonymize_from_matches(
            text: str,
            matches: list[dict[str, int | str | float]],
    ) -> tuple[str, dict[str, str]]:
        entities = _merge_entities(matches)

        replacements: dict[str, str] = {}
        anonymized_parts: list[str] = []
        counters: dict[str, int] = {}
        last_end = 0

        for entity in entities:
            label = str(entity["label"])
            start = int(entity["start"])
            end = int(entity["end"])
            original_text = str(entity["text"])

            anonymized_parts.append(text[last_end:start])

            counters[label] = counters.get(label, 0) + 1
            placeholder = f"[{label}_{counters[label]}]"

            anonymized_parts.append(placeholder)
            replacements[placeholder] = original_text
            last_end = end

        anonymized_parts.append(text[last_end:])

        return "".join(anonymized_parts), replacements

    def __str__(self) -> str:
        return f"StrategyAnonymization: {self.__class__.__name__}"

    def __repr__(self) -> str:
        return f"StrategyAnonymization({self.__class__.__name__})"