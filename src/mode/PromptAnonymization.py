from nlp import AnonymizeResponse
from mode.StrategyAnonymization import StrategyAnonymization

class PromptAnonymization(StrategyAnonymization):
    def anonymize(self, text: str) -> AnonymizeResponse:
        return self.perform_anonymization(text)
