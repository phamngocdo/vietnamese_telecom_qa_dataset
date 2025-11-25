from abc import ABC, abstractmethod

class LLMBase(ABC):
    def __init__(self, model, prompt_lang, is_validator, data_type):
        self.model = model
        self.prompt_lang = prompt_lang
        self.is_validator = is_validator
        self.data_type = data_type
        self.prompt = self.load_prompt()

    def load_prompt(self):
        if self.is_validator:
            path = f"src/llm/{self.data_type}/prompts/{self.prompt_lang}/validator.md"
        else:
            path = f"src/llm/{self.data_type}/prompts/{self.prompt_lang}/generator.md"
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    @abstractmethod
    def generate(self, context):
        pass

    @abstractmethod
    def validate(self, mcq_list):
        pass

