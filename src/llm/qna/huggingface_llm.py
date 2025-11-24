# import re
# import json
# import torch
# from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
# from base import LLMBase

# class HuggingFaceLLM(LLMBase):
#     def __init__(self, model="mistralai/Mistral-7B-Instruct-v0.1", key=None, prompt_path=None,
#                  prompt_lang="vi", is_validator=True, device=None):
#         super().__init__(model, key, prompt_path, prompt_lang, is_validator)
#         self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
#         self.model_pipeline = None
#         self.tokenizer = None
#         self.model_max_length = -1
#         self.init_client()

#     def init_client(self):
#         try:
#             print(f"Loading local model: {self.model}...")
#             self.model_pipeline = pipeline(
#                 "text-generation",
#                 model=self.model,
#                 device_map="auto",
#                 torch_dtype=torch.bfloat16 if self.device == "cuda" else torch.float32
#             )
#             self.tokenizer = self.model_pipeline.tokenizer
#             if hasattr(self.model_pipeline.model.config, "max_position_embeddings"):
#                 self.model_max_length = self.model_pipeline.model.config.max_position_embeddings
#             elif hasattr(self.model_pipeline.tokenizer, "model_max_length"):
#                 self.model_max_length = self.model_pipeline.tokenizer.model_max_length
#             else:
#                 self.model_max_length = 4096
#             print(f"Model loaded on {self.model_pipeline.device}. Max tokens: {self.model_max_length}")
#         except Exception as e:
#             print(f"Failed to initialize Hugging Face model: {e}")

#     def safe_json_parse(self, text):
#         match = re.search(r"```json\s*(\[.*?\])\s*```", text, re.DOTALL)
#         if match:
#             try:
#                 return json.loads(match.group(1))
#             except Exception:
#                 pass
#         match = re.search(r"\[.*\]", text, re.DOTALL)
#         if not match:
#             return []
#         try:
#             return json.loads(match.group(0))
#         except Exception:
#             return []

#     def generate_qna(self, context):
#         if not self.is_validator:
#             print("This instance is configured as a validator, not a generator.")
#             return None
        
#         if not self.model_pipeline:
#             print("Hugging Face model not initialized.")
#             return None
        
#         prompt = self.prompt.replace("{context}", context)
#         try:
#             inputs = self.tokenizer(prompt, return_tensors="pt")
#             input_length = inputs.input_ids.shape[1]
#             if input_length > self.model_max_length:
#                 print(f"HF error: Prompt length ({input_length} tokens) exceeds model's max limit ({self.model_max_length} tokens). Skipping.")
#                 return []
#         except Exception as e:
#             print(f"HF tokenizer error: {e}")
#             return []

#         try:
#             response = self.model_pipeline(
#                 prompt,
#                 max_new_tokens=1024,
#                 do_sample=True,
#                 temperature=0.8,
#                 top_p=0.95,
#                 return_full_text=False,
#                 truncation=False
#             )
#             text = response[0]["generated_text"]
#             qa_pairs = self.safe_json_parse(text)
#             if not all(isinstance(x, dict) and "question" in x and "answer" in x for x in qa_pairs):
#                 print(f"Invalid QA format. Raw: {text[:100]}...")
#                 return []
#             return qa_pairs
#         except Exception as e:
#             print(f"HF error: {e}")
#             return []
        

#     def validate_qna(self, context, question, answer):
#         if not self.is_validator:
#             print("This instance is configured as a generator, not a validator.")
#             return None
        
#         if not self.model_pipeline:
#             print("Hugging Face model not initialized.")
#             return None

#         prompt = self.prompt.replace("{context_chunk}", context)
#         prompt = prompt.replace("{question}", question)
#         prompt = prompt.replace("{answer}", answer)

#         try:
#             inputs = self.tokenizer(prompt, return_tensors="pt")
#             input_length = inputs.input_ids.shape[1]
#             if input_length > self.model_max_length:
#                 print(f"HF validation error: Prompt length ({input_length} tokens) exceeds model's max limit ({self.model_max_length} tokens).")
#                 return None
#         except Exception as e:
#             print(f"HF tokenizer error: {e}")
#             return None

#         try:
#             response = self.model_pipeline(
#                 prompt,
#                 max_new_tokens=10,
#                 do_sample=False,
#                 return_full_text=False,
#                 truncation=False
#             )
#             text = response[0]["generated_text"].strip().lower()
#             if text in ["true", "false"]:
#                 return text == "true"
#             print(f"Unexpected validation result: {text}")
#             return None
#         except Exception as e:
#             print(f"Validation error: {e}")
#             return None
