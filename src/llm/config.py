import os
import yaml
from dotenv import load_dotenv

from src.llm.mcq.gemini_llm import GeminiLLM as mcq_gemini
# from mcq.openai_llm import OpenAILLM as mcq_openai
# from mcq.huggingface_llm import HuggingFaceLLM as mcq_huggingface

from src.llm.qna.gemini_llm import GeminiLLM as qna_gemini
# from qna.openai_llm import OpenAILLM as qna_openai
# from qna.huggingface_llm import HuggingFaceLLM as qna_huggingface

load_dotenv()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

with open(os.path.join(PROJECT_ROOT, "config/path.yaml"), "r", encoding="utf-8") as f:
    path_config = yaml.safe_load(f)

with open(os.path.join(PROJECT_ROOT, "config/parameters.yaml"), "r", encoding="utf-8") as f:
    parameter_config = yaml.safe_load(f)

CLEANED_DIR = path_config["preprocessed"]["cleaned"]
DATA_TYPE = parameter_config.get("data_type", "mcq")
GENERATED_DIR = path_config["generated"] + DATA_TYPE + "/"
TIME_DELAY_SECONDS = parameter_config.get("time_delay_seconds", 15)


def load_llm_config():
    for name, section in parameter_config.items():
        if not isinstance(section, dict):
            continue
        
        llm_class = section.get("class", "").lower()

        if "openai" in llm_class:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(f"Missing OPENAI_API_KEY in environment for section '{name}'")
            section["api_key"] = api_key

        elif "gemini" in llm_class:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError(f"Missing GEMINI_API_KEY in environment for section '{name}'")
            section["api_key"] = api_key
            

def load_model(model_config, prompt_lang, is_validator=False, api_key=None, type_data="mcq"):
    llm_class = model_config.get("class").lower()
    model = model_config.get("model")
    if "openai" in llm_class:
        if type_data == "mcq":
            return mcq_openai(model=model, key=api_key, prompt_lang=prompt_lang, is_validator=is_validator)
        return qna_openai(model=model, key=api_key, prompt_lang=prompt_lang, is_validator=is_validator)
    elif "gemini" in llm_class:
        if type_data == "mcq":
            return mcq_gemini(model=model, key=api_key, prompt_lang=prompt_lang, is_validator=is_validator)
        return qna_gemini(model=model, key=api_key, prompt_lang=prompt_lang, is_validator=is_validator)
    elif "huggingface" in llm_class:
        if type_data == "mcq":
            return mcq_huggingface(model=model, prompt_lang=prompt_lang, is_validator=is_validator)
        return qna_huggingface(model=model, prompt_lang=prompt_lang, is_validator=is_validator)
    else:
        raise ValueError(f"Unsupported LLM class: {llm_class}")
    


load_llm_config()
generator_config = parameter_config.get("generator")
validator_config = parameter_config.get("validator")
prompt_lang = parameter_config.get("prompt_lang", "vi")

print("========== Loading LLM Configuration ==========")

generator = load_model(
    generator_config,
    prompt_lang,
    is_validator=False,
    api_key=generator_config.get("api_key"),
    type_data=DATA_TYPE
)

validator = load_model(
    validator_config,
    prompt_lang,
    is_validator=True,
    api_key=validator_config.get("api_key"),
    type_data=DATA_TYPE
)