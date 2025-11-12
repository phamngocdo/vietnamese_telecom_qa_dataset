import os
import json
import yaml
import time
from dotenv import load_dotenv
# from openai_llm import OpenAILLM
from gemini_llm import GeminiLLM
# from huggingface_llm import HuggingFaceLLM

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
CLEANED_JSON_DIR = os.path.join(PROJECT_ROOT, "data/preprocessed/cleaned/add")
GENERATED_DIR = os.path.join(PROJECT_ROOT, "data/generated/add")
LLM_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config/llm.yaml")

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


def load_model(model_config, prompt_path, prompt_lang, is_validator=False, api_key=None):
    llm_class = model_config.get("class").lower()
    model = model_config.get("model")
    if "openai" in llm_class:
        return OpenAILLM(model=model, key=api_key, prompt_path=prompt_path,
                         prompt_lang=prompt_lang, is_validator=is_validator)
    elif "gemini" in llm_class:
        return GeminiLLM(model=model, key=api_key, prompt_path=prompt_path,
                         prompt_lang=prompt_lang, is_validator=is_validator)
    elif "huggingface" in llm_class:
        return HuggingFaceLLM(model=model, prompt_path=prompt_path,
                              prompt_lang=prompt_lang, is_validator=is_validator)
    else:
        raise ValueError(f"Unsupported LLM class: {llm_class}")
    
    
def load_llm_instances(config_path=LLM_CONFIG_PATH):
    config = load_llm_config(config_path)
    generator_config = config.get("generator")
    validator_config = config.get("validator")
    prompt_path = config.get("prompt_path")
    prompt_lang = config.get("prompt_lang", "vi")

    generator = load_model(
        generator_config,
        prompt_path,
        prompt_lang,
        is_validator=False,
        api_key=generator_config.get("api_key")
    )

    validator = load_model(
        validator_config,
        prompt_path,
        prompt_lang,
        is_validator=True,
        api_key=validator_config.get("api_key")
    )

    return generator, validator


def process_single_chunk(chunk, generator, validator, time_delay_seconds=10):
    context = chunk.get("context")
    source = chunk.get("source")

    if not context or not source:
        return []
    
    generated_qa_list = generator.generate_qna(context)
    if not generated_qa_list:
        print("      -> Generator returned no results.")
        return []
    
    time.sleep(time_delay_seconds)

    print(f"      -> Generated {len(generated_qa_list)} QA pairs. Validating...")

    time.sleep(time_delay_seconds)
    
    is_valid_list = validator.validate_qna(context, generated_qa_list)
    if not is_valid_list or len(is_valid_list) != len(generated_qa_list):
        print("      -> Validator returned an error or mismatched format.")
        return []

    validated_qas = []

    for i, qa_pair in enumerate(generated_qa_list):
        if is_valid_list[i] is True:
            validated_data = {
                "question": qa_pair.get("question"),
                "answer": qa_pair.get("answer"),
                "source": source 
            }
            validated_qas.append(validated_data)
        else:
            print(f"      -> QA pair rejected by Validator.")
            
    return validated_qas


def create_qna_from_file(generator, validator, input_dir=CLEANED_JSON_DIR, output_dir=GENERATED_DIR, time_delay_seconds=5):
    if not os.path.exists(input_dir):
        print(f"Error: Cleaned data directory not found: {input_dir}")
        return

    os.makedirs(output_dir, exist_ok=True)
    print("Starting QA Generation Process ...")

    total_qna = 0

    time_start = time.time()

    for root, _, files in os.walk(input_dir):
        count_qna_for_file = 0
        for file_name in files:
            if not file_name.endswith(".json"):
                continue

            cleaned_file_path = os.path.join(root, file_name)
            relative_path = os.path.relpath(root, input_dir)
            output_dir_file = os.path.join(output_dir, relative_path)
            output_file_path = os.path.join(output_dir_file, file_name)
            os.makedirs(output_dir_file, exist_ok=True)
            
            print(f"\nProcessing file: {file_name}")
            
            try:
                with open(cleaned_file_path, "r", encoding="utf-8") as f:
                    cleaned_chunks = json.load(f)
                
                validated_qas_for_this_file = []
                processed_chunk_ids = set()
                if os.path.exists(output_file_path):
                    print("  -> Found existing output file. Loading checkpoint...")
                    try:
                        with open(output_file_path, "r", encoding="utf-8") as f:
                            validated_qas_for_this_file = json.load(f)
                            processed_chunk_ids = {qa['source']['chunk_order'] for qa in validated_qas_for_this_file if 'chunk_order' in qa['source']}
                        print(f"  -> Loaded {len(processed_chunk_ids)} processed chunks.")
                    except json.JSONDecodeError:
                        print(f"  -> Warning: Output file {output_file_path} is corrupted. Restarting.")
                        validated_qas_for_this_file = []
                        processed_chunk_ids = set()

                chunks_to_process = [
                    c for c in cleaned_chunks 
                    if c.get('source', {}).get('chunk_order', -1) not in processed_chunk_ids
                ]

                if not chunks_to_process:
                    print(f"  -> All chunks already processed. Skipping file.")
                    continue
                
                print(f"  -> {len(chunks_to_process)}/{len(cleaned_chunks)} chunks remaining to process.")

                for i, chunk in enumerate(chunks_to_process):
                    chunk_order_id = chunk.get('source', {}).get('chunk_order', f"index_{i}")
                    print(f"    -> Processing chunk {chunk_order_id} ({i+1}/{len(chunks_to_process)})...")
                    
                    new_valid_qas = process_single_chunk(chunk, generator, validator, time_delay_seconds)
                    
                    if new_valid_qas:
                        count_qna_for_file += len(new_valid_qas)
                        print(f"      -> Accept {len(new_valid_qas)} valid QAs. Saving checkpoint...")
                        validated_qas_for_this_file.extend(new_valid_qas)
                        
                        with open(output_file_path, "w", encoding="utf-8") as f:
                            json.dump(validated_qas_for_this_file, f, ensure_ascii=False, indent=4)
                    else:
                        print(f"    -> No valid QAs found for this chunk.")

            except KeyboardInterrupt:
                print(f"\nProcess interrupted by user.")
            except Exception as e:
                print(f"CRITICAL ERROR processing file {file_name}: {e}")
            finally:
                total_qna += count_qna_for_file
                time_end = (time.time() - time_start) / 60
                print(f"Progress saved {count_qna_for_file} QA pairs to {output_file_path} in {time_end:.2f} minutes.")

    total_time = (time.time() - time_start) / 60
    print(f"\nProgress completed. Progress created {total_qna} QA pairs in {total_time:.2f} minutes.")


if __name__ == "__main__":
    try:
        print("========== Loading LLM Configuration ==========")
        generator_llm, validator_llm = load_llm_instances()
        
        print("\n========== Starting QA Generation Pipeline ==========")
        create_qna_from_file(generator_llm, validator_llm, CLEANED_JSON_DIR, GENERATED_DIR)
        
        print("\n========== QA Generation Pipeline Finished ==========")
        
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user.")
    except Exception as e:
        print(f"Failed to load LLM instances or run pipeline: {e}")