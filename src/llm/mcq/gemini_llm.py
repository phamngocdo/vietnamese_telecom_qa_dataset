import re
import json
import time
from google import genai
from google.genai import types
from base import LLMBase

class GeminiLLM(LLMBase):
    def __init__(self, model="gemini-2.0-flash", key=None, prompt_lang="vi",
                is_validator=True, max_tries=3, time_sleep_if_rate_limit=180):
        super().__init__(model, prompt_lang, is_validator)
        self.key = key
        self.max_tries = max_tries
        self.time_sleep_if_rate_limit = time_sleep_if_rate_limit
        self.init_client()


    def init_client(self):
        if self.key:
            try:
                self.client = genai.Client(api_key=self.key)
                print(f"Gemini client for {'validator' if self.is_validator else 'generator'} initialized.")
            except Exception as e:
                print(f"Failed to initialize Gemini client: {e}")
        else:
            print("Missing GEMINI_API_KEY environment variable.")


    def safe_json_parse(self, text):
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return []
        try:
            return json.loads(match.group(0))
        except Exception:
            return []
    

    def strip_mcq_fields(self, mcq_list):
        cleaned = []

        for item in mcq_list:
            if not isinstance(item, dict):
                continue

            new_item = {
                key: value
                for key, value in item.items()
                if key not in ("answer", "explanation")
            }

            cleaned.append(new_item)

        return cleaned


    def generate_mcq(self, context):
        if self.is_validator:
            print("This instance is configured as a validator, not a generator.")
            return []

        if not self.client:
            print(f"Gemini client for {'validator' if self.is_validator else 'generator'} not initialized.")
            return []

        prompt = self.prompt.replace("{context}", context)

        for attempt in range(1, self.max_tries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
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

                mcqs = self.safe_json_parse(text)
                required = {"question", "choices", "explanation", "answer"}

                if not all(isinstance(x, dict) and required.issubset(x) for x in mcqs):
                    print("Invalid MCQ format.")
                    return []

                return mcqs

            except Exception as e:
                err_msg = str(e)
                print(f"Validation API error (attempt {attempt}/{self.max_tries}): {err_msg}")

                if attempt < self.max_tries:
                    print(f"Waiting {self.time_sleep_if_rate_limit / 60} minutes before retry...")
                    time.sleep(self.time_sleep_if_rate_limit)
                    continue
                else:
                    print("Max tries reached for generation.")
                    return None

        return None
    

    def validate_mcq(self, mcq_list):
        if not self.is_validator:
            print("This instance is configured as a generator, not a validator.")
            return None

        if not self.client:
            print("Gemini client not initialized.")
            return None

        mcqs_without_answer = self.strip_mcq_fields(mcq_list)
        print(mcqs_without_answer)
        correct_answers = [mcq.get("answer") for mcq in mcq_list]
        mcq_counts = len(mcq_list)

        prompt = self.prompt.replace("{mcq_counts}", str(mcq_counts))
        prompt = prompt.replace("{mcq_list}", json.dumps(mcqs_without_answer, ensure_ascii=False))
        
        for attempt in range(1, self.max_tries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="text/plain")
                )

                text = (
                    response.candidates[0].content.parts[0].text.strip().lower()
                    if getattr(response, "candidates", None)
                    and response.candidates
                    and response.candidates[0].content.parts
                    else getattr(response, "text", "").strip().lower()
                )

                if text.startswith("```") and text.endswith("```"):
                    text = "\n".join(text.split("\n")[1:-1]).strip()

                try:
                    parsed_output = json.loads(text)
                    if isinstance(parsed_output, list):
                        size = min(len(correct_answers), len(parsed_output))
                        comparison = [
                            str(correct_answers[i]).strip() == str(parsed_output[i]).strip()
                            for i in range(size)
                        ]

                        return comparison
                    else:
                        print(f"Unexpected output type: {type(parsed_output)} -> {parsed_output}")
                        return None
                except json.JSONDecodeError:
                    print(f"Failed to parse output: {text}")
                    return None

            except Exception as e:
                err_msg = str(e)
                print(f"Validation API error (attempt {attempt}/{self.max_tries}): {err_msg}")

                if attempt < self.max_tries:
                    print(f"Waiting {self.time_sleep_if_rate_limit / 60} minutes before retry...")
                    time.sleep(self.time_sleep_if_rate_limit)
                    continue
                else:
                    print("Max tries reached for validation.")
                    return None
        return None