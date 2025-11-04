class LLMBase():
    def __init__(self, model, key, prompt_path, prompt_lang, is_validator):
        self.model = model
        self.key = key
        self.prompt_path = prompt_path
        self.prompt_lang = prompt_lang
        self.is_validator = is_validator
        self.prompt = self.load_prompt()

    def load_prompt(self):
        if self.is_validator:
            path = f"{self.prompt_path}{self.prompt_lang}/validator.md"
        else:
            path = f"{self.prompt_path}{self.prompt_lang}/generator.md"
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def generate_qna(self, context):
        pass

    def validate_qna(self, context, question, answer):
        pass

