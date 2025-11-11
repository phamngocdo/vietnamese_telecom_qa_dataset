# Hướng dẫn Đánh giá QA Viễn thông
Đánh giá một danh sách các cặp QA [QA_PAIRS] dựa trên một khối ngữ cảnh [CONTEXT].

---

## QUY TẮC CHUNG (CORE RULES)

Một cặp QA được đánh giá là **`true`** (phù hợp) nếu thỏa mãn TẤT CẢ các điều kiện sau:
1.  Câu hỏi liên quan trực tiếp đến nội dung kỹ thuật trong [CONTEXT].
2.  Câu trả lời chính xác và có thể kiểm chứng **từ [CONTEXT] hoặc từ hiểu biết chuyên môn kỹ thuật viễn thông của bạn (nếu context không đủ rõ)**.
3.  Không có suy luận mơ hồ, bịa đặt, hoặc thông tin sai lệch so với thực tế kỹ thuật.
4.  Ngôn ngữ rõ ràng, chính xác, sử dụng đúng thuật ngữ kỹ thuật (3GPP, IEEE, QoS, MIMO…).
5.  Nếu có mâu thuẫn giữa [CONTEXT] và kiến thức của bạn, **ưu tiên [CONTEXT]** làm nguồn xác thực.

Một cặp QA được đánh giá là **`false`** (không phù hợp) nếu:
1.  Câu hỏi hoặc câu trả lời không liên quan đến [CONTEXT] hoặc lĩnh vực kỹ thuật viễn thông.
2.  Câu trả lời chứa thông tin sai so với kiến thức kỹ thuật thực tế hoặc context.
3.  Câu hỏi/Trả lời quá chung chung, cảm tính hoặc không thể xác minh bằng kiến thức viễn thông.
4.  Câu trả lời là mô tả rỗng, đặc biệt khi [CONTEXT] là bảng, danh mục hoặc tiêu đề.


---

## QUY TẮC BIÊN TẬP (EDITING RULES)
* Giữ nguyên đơn vị đo (ms, MHz, Gbps…).
* Viết hoa đúng chuẩn tên tổ chức và công nghệ (3GPP, ITU-R, ETSI, IEEE…).
* Nếu [CONTEXT] chứa bảng, danh mục, công thức → chỉ đánh giá phần có thể hiểu bằng ngôn ngữ tự nhiên.

---

## ĐẦU VÀO (INPUT)
Input là một đối tượng JSON duy nhất.

```json
{
  "context": "{context}",
  "qna_counts": "{qna_counts}",
  "qna_list": {qna_list}
}
```

---

## ĐỊNH DẠNG ĐẦU RA BẮT BUỘC (MANDATORY OUTPUT)
**CHỈ TRẢ VỀ MỘT MẢNG BOOLEAN GỒM DUY NHẤT.**
Mảng này phải có số lượng phần tử bằng chính xác số lượng trong qna_list đầu vào.
**KHÔNG** thêm bất kỳ văn bản giải thích, lời chào, hay mã Markdown nào.
Phản hồi của bạn phải BẮT ĐẦU bằng ký tự [ và KẾT THÚC bằng ký tự ].

---

## VÍ DỤ
**Input:**

```json
{
    "context": "IEEE 802.11ax-2021 định nghĩa Wi-Fi 6 với tốc độ cao và độ trễ thấp.",
    "qna_counts": "2",
    "qna_list": [
        { "question": "IEEE 802.11ax-2021 là chuẩn gì?", "answer": "Là chuẩn Wi-Fi 6 được IEEE định nghĩa để cải thiện tốc độ và giảm độ trễ mạng."},
        { "question": "6G có dùng MIMO không?", "answer": "Có, 6G dự kiến sẽ dùng MIMO cải tiến hơn 5G."}
    ]
}
```

**Output:**
```
[true, false]
```