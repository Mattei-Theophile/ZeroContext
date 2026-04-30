from pydantic import BaseModel
from typing import Optional, Callable
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from spacy.language import Language
from rules.regex import find_regex_matches

class AnonymizeResponse(BaseModel):
    uuid: str
    originalText: str
    anonymizedText: str
    matchTable: dict[str, str]
    language: str = "fr"
    contextLabel: str | None = None
    contextScores: dict[str, float] = {}

    def __str__(self) -> str:
        return (
            f"AnonymizeResponse: {self.uuid} | "
            f"{self.originalText} | {self.anonymizedText} | {self.matchTable} | "
            f"{self.language} | {self.contextLabel} | {self.contextScores}"
        )


_HF_NER_MODELS = {
    "fr": "Jean-Baptiste/camembert-ner",
    "en": "dbmdz/bert-large-cased-finetuned-conll03-english",
}

_HF_NER_PIPELINES: dict[str, Optional[Callable]] = {}

def get_hf_ner(language: str = "fr") -> Optional[Callable]:
    global _HF_NER_PIPELINES
    
    if language not in _HF_NER_MODELS:
        print(f"Language {language} not supported, falling back to 'fr'")
        language = "fr"

    if language in _HF_NER_PIPELINES and _HF_NER_PIPELINES[language] is not None:
        return _HF_NER_PIPELINES[language]
    
    model_name = _HF_NER_MODELS[language]
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForTokenClassification.from_pretrained(model_name)
        ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")
        _HF_NER_PIPELINES[language] = ner_pipeline
        return ner_pipeline
    except Exception as exc:
        print(f"Impossible de charger le modèle Hugging Face pour {language}: {exc}")
        return None

@Language.factory("hf_ner_component", default_config={"language": "fr"})
def create_hf_ner_component(nlp, name, language):
    return HFNERComponent(language)

class HFNERComponent:
    def __init__(self, language: str):
        self.language = language

    def __call__(self, doc):
        ner = get_hf_ner(self.language)
        if ner is None:
            return doc
        try:
            hf_entities = ner(doc.text)
            spans = []
            for ent in hf_entities:
                span = doc.char_span(ent["start"], ent["end"], label=ent["entity_group"], alignment_mode="expand")
                if span is not None:
                    spans.append(span)
            
            # Filter overlapping spans
            filtered_spans = []
            for span in sorted(spans, key=lambda x: len(x), reverse=True):
                if not any(span.start < s.end and span.end > s.start for s in filtered_spans):
                    filtered_spans.append(span)
            
            doc.ents = sorted(filtered_spans, key=lambda x: x.start)
        except Exception as exc:
            print(f"Erreur pendant l'inférence Hugging Face ({self.language}): {exc}")
        return doc

@Language.component("hf_regex_component")
def hf_regex_component(doc):
    for match in find_regex_matches(doc.text):
        print(match)
        span = doc.char_span(
            match["start"],
            match["end"],
            label=match["label"],
            alignment_mode="expand",
        )
        if span is not None:
            doc.spans.setdefault(match["label"], []).append(span)
    return doc



def _sort_entities(
        entities: list[dict[str, int | str | float]],
) -> list[dict[str, int | str | float]]:
    source_priority = {
        "regex": 3,
        "transformer": 2,
        "spacy": 1,
    }
    return sorted(
        entities,
        key=lambda item: (
            int(item["start"]),
            -(int(item["end"]) - int(item["start"])),
            -source_priority.get(str(item.get("source", "")), 0),
            -float(item.get("score", 0.0)),
        ),
    )


def _normalize_label(label: str) -> str:
    mapping = {
        "PER": "PERSON",
        "PERSON_WITH_TITLE": "PERSON",
        "GPE": "LOC",
    }
    return mapping.get(label, label)


def _merge_entities(
        entities: list[dict[str, int | str | float]],
) -> list[dict[str, int | str | float]]:
    merged: list[dict[str, int | str | float]] = []

    for entity in _sort_entities(entities):
        entity["label"] = _normalize_label(str(entity["label"]))
        start = int(entity["start"])
        end = int(entity["end"])

        if any(start < int(existing["end"]) and end > int(existing["start"]) for existing in merged):
            continue

        merged.append(entity)

    return merged


