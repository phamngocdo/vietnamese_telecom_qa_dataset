from abc import ABC, abstractmethod

class LLMBase(ABC):
    def __init__(self, model, prompt_lang, is_validator):
        self.model = model
        self.prompt_lang = prompt_lang
        self.is_validator = is_validator
        self.prompt = self.load_prompt()

    def load_prompt(self):
        if self.is_validator:
            path = f"src/llm/qna/prompts/{self.prompt_lang}/validator.md"
        else:
            path = f"src/llm/qna/prompts/{self.prompt_lang}/generator.md"
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    @abstractmethod
    def generate_qna(self, context):
        pass

    @abstractmethod
    def validate_qna(self, context, qna_list):
        pass

