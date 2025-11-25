import os
import json
import yaml
import time
from dotenv import load_dotenv

from mcq.gemini_llm import GeminiLLM as mcq_gemini
# from mcq.openai_llm import OpenAILLM as mcq_openai
# from mcq.huggingface_llm import HuggingFaceLLM as mcq_huggingface

from qna.gemini_llm import GeminiLLM as qna_gemini
# from qna.openai_llm import OpenAILLM as qna_openai
# from qna.huggingface_llm import HuggingFaceLLM as qna_huggingface

load_dotenv()

def load_llm_config(yaml_path):
    with open(yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    for name, section in config.items():
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
    return config


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
    
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
LLM_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config/llm.yaml")

config = load_llm_config(LLM_CONFIG_PATH)
generator_config = config.get("generator")
validator_config = config.get("validator")
prompt_lang = config.get("prompt_lang", "vi")

CLEANED_JSON_DIR = os.path.join(PROJECT_ROOT, "data/preprocessed/cleaned/add")
DATA_TYPE = config.get("data_type", "mcq")
GENERATED_DIR = os.path.join(PROJECT_ROOT, f"data/generated/{DATA_TYPE}/add")
TIME_DELAY_SECONDS = 15

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


def process_single_chunk(chunk, generator, validator):
    context = chunk.get("context")
    source = chunk.get("source")

    if not context or not source:
        return []
    
    time.sleep(TIME_DELAY_SECONDS)

    generated_quest_list = generator.generate(context)
    if not generated_quest_list:
        print("      -> Generator returned no results.")
        return []
    
    time.sleep(TIME_DELAY_SECONDS)

    print(f"      -> Generated {len(generated_quest_list)} Questions. Validating...")

    time.sleep(TIME_DELAY_SECONDS)
    
    if (DATA_TYPE == "mcq"):
        is_valid_list = validator.validate(generated_quest_list)
    if (DATA_TYPE == "qna"):
        is_valid_list = validator.validate(context, generated_quest_list)
    if not is_valid_list or len(is_valid_list) != len(generated_quest_list):
        print("      -> Validator returned an error or mismatched format.")
        return []

    validated_quests = []

    for i, quest in enumerate(generated_quest_list):
        if is_valid_list[i] is True:
            if (DATA_TYPE == "mcq"):
                validated_data = {
                    "question": quest.get("question"),
                    "choices": quest.get("choices"),
                    "answer": quest.get("answer"),
                    "explanation": quest.get("explanation"),
                    "source": source 
                }
            if (DATA_TYPE == "qna"):
                validated_data = {
                    "question": quest.get("question"),
                    "answer": quest.get("answer"),
                    "source": source 
                }
            validated_quests.append(validated_data)
            
    return validated_quests


def create_quest_from_file(file_path, output_file_path, generator, validator):
    file_name = os.path.basename(file_path)
    print(f"\nProcessing file: {file_name}")
    
    quests_created_count = 0

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            cleaned_chunks = json.load(f)
        
        validated_quests_for_this_file = []
        processed_chunk_ids = set()
        existing_questions = set()

        if os.path.exists(output_file_path):
            print("  -> Found existing output file. Loading checkpoint...")
            try:
                with open(output_file_path, "r", encoding="utf-8") as f:
                    validated_quests_for_this_file = json.load(f)
                    
                    processed_chunk_ids = {
                        quest['source']['chunk_order'] 
                        for quest in validated_quests_for_this_file 
                        if 'chunk_order' in quest['source']
                    }
                    
                    for quest in validated_quests_for_this_file:
                        if "question" in quest:
                            existing_questions.add(quest["question"])
                            
                print(f"  -> Loaded {len(processed_chunk_ids)} processed chunks and {len(existing_questions)} existing questions.")
            except json.JSONDecodeError:
                print(f"  -> Warning: Output file {output_file_path} is corrupted. Restarting.")
                validated_quests_for_this_file = []
                processed_chunk_ids = set()
                existing_questions = set()

        chunks_to_process = [
            c for c in cleaned_chunks 
            if c.get('source', {}).get('chunk_order', -1) not in processed_chunk_ids
        ]

        if not chunks_to_process:
            print(f"  -> All chunks already processed. Skipping file.")
            return 0
        
        print(f"  -> {len(chunks_to_process)}/{len(cleaned_chunks)} chunks remaining to process.")

        for i, chunk in enumerate(chunks_to_process):
            chunk_order_id = chunk.get('source', {}).get('chunk_order', f"index_{i}")
            print(f"    -> Processing chunk {chunk_order_id} ({i+1}/{len(chunks_to_process)})...")
            
            new_valid_quests = process_single_chunk(chunk, generator, validator)
            
            if new_valid_quests:
                unique_new_quests = []
                for quest in new_valid_quests:
                    question_text = quest.get("question")
                    if question_text and question_text not in existing_questions:
                        unique_new_quests.append(quest)
                        existing_questions.add(question_text)
                
                if unique_new_quests:
                    quests_created_count += len(unique_new_quests)
                    print(f"      -> Accept {len(unique_new_quests)} valid, unique Questions. Saving checkpoint...")
                    validated_quests_for_this_file.extend(unique_new_quests)
                    
                    with open(output_file_path, "w", encoding="utf-8") as f:
                        json.dump(validated_quests_for_this_file, f, ensure_ascii=False, indent=4)
                else:
                    print(f"      -> Valid Questions found but all were duplicates.")
            else:
                print(f"    -> No valid Questions found for this chunk.")

    except KeyboardInterrupt:
        return quests_created_count 
    except Exception as e:
        print(f"CRITICAL ERROR processing file {file_name}: {e}")
    
    return quests_created_count


def create_quest_from_folder(generator, validator, input_dir=CLEANED_JSON_DIR, output_dir=GENERATED_DIR):
    if not os.path.exists(input_dir):
        print(f"Error: Cleaned data directory not found: {input_dir}")
        return

    os.makedirs(output_dir, exist_ok=True)
    print("Starting Generation Process ...")

    total_quest = 0
    time_start = time.time()

    try:
        for root, _, files in os.walk(input_dir):
            for file_name in files:
                if not file_name.endswith(".json"):
                    continue

                cleaned_file_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(root, input_dir)
                output_dir_file = os.path.join(output_dir, relative_path)
                output_file_path = os.path.join(output_dir_file, file_name)
                
                os.makedirs(output_dir_file, exist_ok=True)
                
                count = create_quest_from_file(cleaned_file_path, output_file_path, generator, validator)
                total_quest += count
                
    except KeyboardInterrupt:
        print(f"\nProcess interrupted by user.")
    finally:
        total_time = (time.time() - time_start) / 60
        print(f"\nProgress completed. Total created {total_quest} Questions in {total_time:.2f} minutes.")


if __name__ == "__main__":
    try:
        print("========== Loading LLM Configuration ==========")        
        print("\n========== Starting Generation Pipeline ==========")
        create_quest_from_folder(generator, validator, CLEANED_JSON_DIR, GENERATED_DIR)
        print("\n========== Generation Pipeline Finished ==========")
        
    except Exception as e:
        print(f"Failed to load LLM instances or run pipeline: {e}")