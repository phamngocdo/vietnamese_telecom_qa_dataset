import os
import re
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from base import LLMBase

load_dotenv()
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
API_KEY = os.getenv("GEMINI_API_KEY")

class GeminiLLM(LLMBase):
    def __init__(self, model, key, prompt_path, prompt_lang, is_validator):
        super().__init__(model, key, prompt_path, prompt_lang, is_validator)
        self.init_client()

    def init_client(self):
        if self.key:
            try:
                self.client = genai.Client(api_key=self.key)
                print("Gemini client initialized.")
            except Exception as e:
                print(f"Failed to initialize Gemini client: {e}")
        else:
            print("Missing GEMINI_API_KEY environment variable.")

    def safe_json_parse(self, text: str):
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return []
        try:
            return json.loads(match.group(0))
        except Exception:
            return []

    def generate_qna(self, context):
        if self.is_validator:
            print("This instance is configured as a validator, not a generator.")
            return []
        
        if not self.client:
            print("Gemini client not initialized.")
            return []

        prompt = self.prompt.replace("{context}", context)

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )

            text = (
                response.candidates[0].content.parts[0].text
                if getattr(response, "candidates", None)
                and response.candidates
                and response.candidates[0].content.parts
                else getattr(response, "text", "")
            )

            qa_pairs = self.safe_json_parse(text)
            if not all(isinstance(x, dict) and "question" in x and "answer" in x for x in qa_pairs):
                print("Invalid QA format.")
                return []
            return qa_pairs

        except Exception as e:
            print(f"API error: {e}")
            return []
        
    def validate_qna(self, context: str, question: str, answer: str):
        pass
