import re
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, lower, trim, coalesce, lit
from pyspark.sql.types import BooleanType
from src.postprocess.config import SPARK_APP_NAME, SPARK_MEMORY, FORBIDDEN_KEYWORDS


def init_spark_session():
    return SparkSession.builder \
        .appName(SPARK_APP_NAME) \
        .config("spark.driver.memory", SPARK_MEMORY) \
        .master("local[*]") \
        .getOrCreate()


def get_regex_patterns():
    p1_patterns = [re.escape(w.lower()) for w in sorted(FORBIDDEN_KEYWORDS["part_1"], key=len, reverse=True)]
    p2_patterns = [re.escape(w.lower()) for w in sorted(FORBIDDEN_KEYWORDS["part_2"], key=len, reverse=True)]
    
    p1_regex = re.compile(r"\b(" + "|".join(p1_patterns) + r")\b", re.IGNORECASE)
    p2_regex = re.compile(r"\b(" + "|".join(p2_patterns) + r")\b", re.IGNORECASE)
    return p1_regex, p2_regex


P1_REGEX, P2_REGEX = get_regex_patterns()

def is_valid_question_logic(question: str) -> bool:
    if not question: return False
    text = question.lower().strip()
    has_p1 = P1_REGEX.search(text) is not None
    has_p2 = P2_REGEX.search(text) is not None
    if has_p1 and has_p2: return False
    return True


is_valid_udf = udf(is_valid_question_logic, BooleanType())


def add_normalization_columns(df):
    has_answer = "answer" in df.columns
    has_explanation = "explanation" in df.columns
    
    df_out = df
    if not has_answer and not has_explanation:
        df_out = df_out.withColumn("unified_answer", lit(""))
    elif has_answer and has_explanation:
        df_out = df_out.withColumn("unified_answer", coalesce(col("answer"), col("explanation")))
    elif has_answer:
         df_out = df_out.withColumn("unified_answer", col("answer"))
    else:
         df_out = df_out.withColumn("unified_answer", col("explanation"))
         
    return df_out.withColumn("norm_question", lower(trim(col("question")))) \
                 .withColumn("norm_answer", lower(trim(col("unified_answer"))))


def read_and_merge_data(spark, input_file_path, output_file_path):
    try:
        df_new = spark.read.option("multiline", "true").json(input_file_path)
        
        try:
            df_old = spark.read.option("multiline", "true").json(output_file_path)
            return df_old.unionByName(df_new, allowMissingColumns=True), df_new.count()
        except Exception:
            return df_new, df_new.count()
    except Exception:
        return None, 0
    

def filter_invalid_questions(df):
    df_filtered = df.filter(is_valid_udf(col("question")))
    return df_filtered, df_filtered.count()


def internal_deduplication(df):
    df_norm = add_normalization_columns(df)
    df_unique = df_norm.dropDuplicates(["norm_question", "norm_answer"])
    return df_unique, df_unique.count()