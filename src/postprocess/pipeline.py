import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(PROJECT_ROOT)

import shutil
import glob
from src.postprocess.config import GENERATOR_DIR, STAGING_PENDING_DIR, FINAL_FILE, DATA_TYPE
from src.postprocess.spark_ops import (
    init_spark_session, read_and_merge_data, 
    filter_invalid_questions, internal_deduplication, 
    add_normalization_columns
)
from src.utils.logger import *

def finalize_single_json(spark_output_dir, target_file_path):
    json_files = glob.glob(os.path.join(spark_output_dir, "part-*.json"))
    if json_files:
        source_file = json_files[0]
        os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
        try:
            with open(source_file, 'r', encoding='utf-8') as f_in:
                lines = f_in.readlines()
            lines = [line.strip() for line in lines if line.strip()]
            json_content = "[\n" + ",\n".join(lines) + "\n]"
            
            with open(target_file_path, 'w', encoding='utf-8') as f_out:
                f_out.write(json_content)
        except Exception as e:
            log_error(f"Error converting to JSON Array: {e}")
            return False
        
        shutil.rmtree(spark_output_dir)
        return True
    return False


def global_deduplication(spark, df_local, master_file_path):
    if not os.path.exists(master_file_path):
        return df_local, df_local.count()

    try:
        df_master = spark.read.option("multiline", "true").json(master_file_path)
        
        df_master_norm = add_normalization_columns(df_master)
        master_keys = df_master_norm.select("norm_question", "norm_answer").distinct()
        
        df_final = df_local.join(
            master_keys, 
            on=["norm_question", "norm_answer"], 
            how="left_anti"
        )
        return df_final, df_final.count()
    except Exception as e:
        log_warning(f"  -> Global Dedup Warning: {e}. Proceeding with local dedup only.")
        return df_local, df_local.count()
    

def save_final_dataframe(df, output_file_path):
    cols_to_drop = ["norm_question", "norm_answer", "unified_answer", "source"]
    df_final = df.drop(*cols_to_drop)
    
    desired_order = ["question", "choices", "answer", "explanation"]
    existing_cols = df_final.columns
    final_cols = [c for c in desired_order if c in existing_cols] + \
                 [c for c in existing_cols if c not in desired_order]
    
    df_final = df_final.select(*final_cols)
    
    temp_dir = output_file_path + "_temp_spark_write"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    
    df_final.coalesce(1).write.json(temp_dir)
    
    if finalize_single_json(temp_dir, output_file_path):
        log_info(f"  -> Saved {df_final.count()} samples to: {output_file_path}")
    else:
        log_error("  -> Error saving file.")


def postprocess_file(input_file_path, spark=None):
    if spark is None:
        spark = init_spark_session()
    
    try:
        rel_path = os.path.relpath(input_file_path, GENERATOR_DIR)
    except ValueError:
        rel_path = os.path.basename(input_file_path)

    output_rel_path = os.path.splitext(rel_path)[0] + ".json"
    output_file_path = os.path.join(STAGING_PENDING_DIR, output_rel_path)

    if os.path.exists(output_file_path):
        log_info(f"\nSkipping already processed file: {output_file_path}")
        return

    file_name = os.path.basename(input_file_path)
    log_info(f"\nProcessing: {file_name}")
    
    df_merged, count_raw = read_and_merge_data(spark, input_file_path, output_file_path)
    if df_merged is None:
        log_error(f"-> Error reading file {input_file_path}")
        return

    log_info(f"  -> Raw Input Count: {count_raw}")

    df_filtered, count_filtered = filter_invalid_questions(df_merged)
    log_info(f"  -> After Filtering Invalid: {count_filtered} (Dropped {count_raw - count_filtered})")

    df_internal_dedup, count_internal = internal_deduplication(df_filtered)
    log_info(f"  -> After Internal Dedup: {count_internal} (Dropped {count_filtered - count_internal})")

    df_final, count_final = global_deduplication(spark, df_internal_dedup, FINAL_FILE)
    if count_internal > count_final:
        log_info(f"  -> After Master Dedup: {count_final} (Dropped {count_internal - count_final} duplicates found in Master)")
    else:
        log_info(f"  -> Master Dedup: No duplicates found in Master.")

    if count_final > 0:
        save_final_dataframe(df_final, output_file_path)
    else:
        log_info("  -> Result empty after processing. Nothing to save.")
    return output_file_path


def run_pipeline():
    spark = init_spark_session()
    log_info(f"Source: {GENERATOR_DIR}")
    log_info(f"Target: {STAGING_PENDING_DIR}\n")
        
    log_info(f"\n========== Processing Type: {DATA_TYPE.upper()} ==========")
    
    for root, _, files in os.walk(GENERATOR_DIR):
        for file_name in files:
            if not file_name.endswith(".json"):
                continue
            
            input_path = os.path.join(root, file_name)
            
            postprocess_file(input_path, spark)

    spark.stop()


if __name__ == "__main__":
    log_info("========== POST-PROCESSING STARTED ==========")
    run_pipeline()
    log_info("========== POST-PROCESSING FINISHED ==========")