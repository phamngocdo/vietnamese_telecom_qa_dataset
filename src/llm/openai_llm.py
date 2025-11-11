# import re
# import json
# import time
# from openai import OpenAI
# from base import LLMBase

# class OpenAILLM(LLMBase):
#     def __init__(self, model="gpt-4o-mini", key=None, prompt_path=None, prompt_lang="vi",
#                  is_validator=True, max_tries=3, time_sleep_if_rate_limit=300):
#         super().__init__(model, prompt_path, prompt_lang, is_validator)
#         self.key = key
#         self.max_tries = max_tries
#         self.time_sleep_if_rate_limit = time_sleep_if_rate_limit
#         self.init_client()

#     def init_client(self):
#         if self.key:
#             try:
#                 self.client = OpenAI(api_key=self.key)
#                 print("OpenAI client initialized.")
#             except Exception as e:
#                 print(f"Failed to initialize OpenAI client: {e}")
#         else:
#             print("Missing OPENAI_API_KEY environment variable.")

#     def safe_json_parse(self, text):
#         match = re.search(r"\[.*\]", text, re.DOTALL)
#         if not match:
#             return []
#         try:
#             return json.loads(match.group(0))
#         except Exception:
#             return []

#     def generate_qna(self, context):
#         if self.is_validator:
#             print("This instance is configured as a validator, not a generator.")
#             return []

#         if not self.client:
#             print("OpenAI client not initialized.")
#             return []

#         prompt = self.prompt.replace("{context}", context)

#         for attempt in range(1, self.max_tries + 1):
#             try:
#                 response = self.client.chat.completions.create(
#                     model=self.model,
#                     messages=[
#                         {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
#                         {"role": "user", "content": prompt}
#                     ],
#                     response_format={"type": "json_object"}
#                 )

#                 text = response.choices[0].message.content

#                 qa_pairs = self.safe_json_parse(text)
#                 if not all(isinstance(x, dict) and "question" in x and "answer" in x for x in qa_pairs):
#                     print("Invalid QA format.")
#                     return []
#                 return qa_pairs

#             except Exception as e:
#                 err_msg = str(e)
#                 print(f"API error (attempt {attempt}/{self.max_tries}): {err_msg}")

#                 if "429" in err_msg or "rate limit" in err_msg.lower() or "resource" in err_msg.lower():
#                     if attempt < self.max_tries:
#                         print(f"Resource exhausted. Waiting {self.time_sleep_if_rate_limit / 60} minutes before retry...")
#                         time.sleep(self.time_sleep_if_rate_limit)
#                         continue
#                     else:
#                         print("Max tries reached. Skipping this context.")
#                         return []
#                 else:
#                     return []

#         return []

#     def validate_qna(self, context, question, answer):
#         if not self.is_validator:
#             print("This instance is configured as a generator, not a validator.")
#             return None

#         if not self.client:
#             print("OpenAI client not initialized.")
#             return None

#         prompt = self.prompt.replace("{context}", context)
#         prompt = prompt.replace("{question}", question)
#         prompt = prompt.replace("{answer}", answer)

#         for attempt in range(1, self.max_tries + 1):
#             try:
#                 response = self.client.chat.completions.create(
#                     model=self.model,
#                     messages=[
#                         {"role": "system", "content": "You are a strict evaluator. Respond only with 'true' or 'false'."},
#                         {"role": "user", "content": prompt}
#                     ]
#                 )

#                 text = response.choices[0].message.content.strip().lower()

#                 if text in ["true", "false"]:
#                     return text == "true"

#                 print(f"Unexpected response format: {text}")
#                 return None

#             except Exception as e:
#                 err_msg = str(e)
#                 print(f"Validation API error (attempt {attempt}/{self.max_tries}): {err_msg}")

#                 if "429" in err_msg or "rate limit" in err_msg.lower() or "resource" in err_msg.lower():
#                     if attempt < self.max_tries:
#                         print(f"Resource exhausted. Waiting {self.time_sleep_if_rate_limit / 60} minutes before retry...")
#                         time.sleep(self.time_sleep_if_rate_limit)
#                         continue
#                     else:
#                         print("Max tries reached for validation.")
#                         return None
#                 else:
#                     return None

#         return None
