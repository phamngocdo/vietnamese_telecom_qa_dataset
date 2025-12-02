import os
import yaml

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

with open(os.path.join(PROJECT_ROOT, "config/path.yaml"), "r", encoding="utf-8") as f:
    data_paths = yaml.safe_load(f)

GENERATOR_DIR = data_paths["generated"]
FINAL_FILE = data_paths["final"]
STAGING_PENDING_DIR = data_paths["postprocessed"]["pending"]

with open(os.path.join(PROJECT_ROOT, "config/parameters.yaml"), "r", encoding="utf-8") as f:
    parameters = yaml.safe_load(f)

DATA_TYPE = parameters["data_type"]

SPARK_MEMORY = "4g"
SPARK_APP_NAME = "TelecomQA_Postprocessing"

FORBIDDEN_KEYWORDS = {
    "part_1": [
        "theo", "dựa theo", "tuân theo", "làm theo", "dựa vào", "căn cứ vào", "căn cứ theo",
        "nhìn vào", "quan sát", "xem", "tham khảo", "xét", "thông qua", "qua",
        "trong", "tại", "ở", "trên", "dưới", "bên trên", "bên dưới",
        "phía trên", "phía dưới", "đằng trước", "đằng sau",
        "bên trái", "bên phải", "bên cạnh", "kế bên", "giữa", "đầu", "cuối",
        "liền trước", "liền sau", "kế tiếp", "tương ứng với", "minh họa cho", "hiển thị",
        "được liệt kê", "được trình bày", "được mô tả"
    ],
    "part_2": [
        "hình", "hình ảnh", "hình vẽ", "hình minh họa", "hình số",
        "sơ đồ", "lược đồ", "biểu đồ", "đồ thị", "bản đồ", "tranh",
        "bảng", "bảng biểu", "bảng số liệu", "bảng tính", "table", "tab", "tab.",
        "cột", "hàng", "dòng", "ô", "trục", "số liệu", "dữ liệu", "thông số", "giá trị",
        "mục", "tiểu mục", "chương", "phần", "bài", "đoạn", "đoạn văn", "khổ", "khổ thơ", "khổ văn",
        "trang", "số trang", "dòng thứ", "câu", "từ", "ngữ", "cụm từ",
        "chú thích", "ghi chú", "phụ lục", "mục lục",
        "tài liệu", "tài liệu tham khảo", "nguồn", "tiêu đề", "đề mục",
        "công thức", "phương trình", "biểu thức", "hệ phương trình",
        "ký hiệu", "biểu tượng", "ngữ cảnh",
        "bài báo", "nghiên cứu", "báo cáo", "luận văn", "giáo trình",
        "tác giả", "nhóm tác giả", "sách", "tài liệu"
    ]
}