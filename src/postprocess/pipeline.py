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
            print(f"Error converting to JSON Array: {e}")
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
        print(f"  -> Global Dedup Warning: {e}. Proceeding with local dedup only.")
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
        print(f"  -> Saved {df_final.count()} samples to: {output_file_path}")
    else:
        print("  -> Error saving file.")


def process_single_file(spark, input_file_path, output_file_path, master_file_path):
    file_name = os.path.basename(input_file_path)
    print(f"\nProcessing: {file_name}")
    
    df_merged, count_raw = read_and_merge_data(spark, input_file_path, output_file_path)
    if df_merged is None:
        print(f"-> Error reading file {input_file_path}")
        return

    print(f"  -> Raw Input Count: {count_raw}")

    df_filtered, count_filtered = filter_invalid_questions(df_merged)
    print(f"  -> After Filtering Invalid: {count_filtered} (Dropped {count_raw - count_filtered})")

    df_internal_dedup, count_internal = internal_deduplication(df_filtered)
    print(f"  -> After Internal Dedup: {count_internal} (Dropped {count_filtered - count_internal})")

    df_final, count_final = global_deduplication(spark, df_internal_dedup, master_file_path)
    if count_internal > count_final:
        print(f"  -> After Master Dedup: {count_final} (Dropped {count_internal - count_final} duplicates found in Master)")
    else:
        print(f"  -> Master Dedup: No duplicates found in Master.")

    if count_final > 0:
        save_final_dataframe(df_final, output_file_path)
    else:
        print("  -> Result empty after processing. Nothing to save.")


def run_pipeline():
    spark = init_spark_session()
    print(f"Source: {GENERATOR_DIR}")
    print(f"Target: {STAGING_PENDING_DIR}\n")

    source_type_dir = os.path.join(GENERATOR_DIR, DATA_TYPE)
    target_type_dir = os.path.join(STAGING_PENDING_DIR, DATA_TYPE)
        
    print(f"\n========== Processing Type: {DATA_TYPE.upper()} ==========")
    
    for root, _, files in os.walk(source_type_dir):
        for file_name in files:
            if not file_name.endswith(".json"):
                continue
            
            input_path = os.path.join(root, file_name)
            rel_path = os.path.relpath(root, source_type_dir)
            output_dir = os.path.join(target_type_dir, rel_path)
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, file_name)
            if os.path.exists(output_path):
                print(f"  -> Skip (already exists): {output_path}")
                continue
            
            process_single_file(spark, input_path, output_path, FINAL_FILE)

    spark.stop()


if __name__ == "__main__":
    print("========== POST-PROCESSING STARTED ==========")
    run_pipeline()
    print("========== POST-PROCESSING FINISHED ==========")