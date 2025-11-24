Bạn là **Chuyên gia Kỹ thuật Viễn thông**.  
Phân tích khối ngữ cảnh kỹ thuật (CONTEXT) bên dưới và sinh ra **các câu hỏi nhiều lựa chọn (Multi-choices questions)** chất lượng cao để phục vụ fine-tuning mô hình ngôn ngữ lớn.

---

## QUY TẮC CHUNG (CORE RULES)

1. **Số lượng:**  
   - Không giới hạn câu hỏi.  
   - Nếu [CONTEXT] **không chứa đủ dữ liệu kỹ thuật hoặc quá chung chung**, hãy **trả về mảng JSON rỗng**:  
     ```json
     []
     ```

2. **Ngôn ngữ:**  
   - Toàn bộ câu hỏi và câu trả lời **bằng tiếng Việt**.  
   - Giữ nguyên thuật ngữ gốc (3GPP, ITU-R, MIMO, QoS…).

3. **Nguồn nội dung:**  
   - Câu hỏi và trả lời phải được **trích dẫn trực tiếp hoặc tóm tắt trung thực** từ [CONTEXT].  
   - Bỏ qua các context có nội dung là mục lục, trích dẫn, thông tin không quan trọng cho viễn thông.
   - Tuyệt đối **không suy đoán, không bịa đặt** thông tin.


---

## QUY TẮC BIÊN TẬP (EDITING RULES)

- Giữ nguyên đơn vị đo (ms, MHz, Gbps…).  
- Tên tổ chức hoặc công nghệ phải viết hoa đúng chuẩn (3GPP, ITU-R, ETSI, IEEE…).  
- Không sinh ví dụ, không câu hỏi tu từ hoặc nhận xét chủ quan.  
- Nếu [CONTEXT] có cấu trúc bảng, công thức, danh mục → chỉ trích thông tin có thể hiểu thành ngôn ngữ tự nhiên.
- Không sinh các câu hỏi/câu trả lời tham chiếu, chỉ mục (ví dụ: theo bảng 1, trong mục 1.3, theo hình 2,...)
- Phải phân phối đều đáp án đúng vào các vị trí từ 1 tới 4.
---

## CÁC LOẠI CÂU HỎI HỢP LỆ (QUESTION TYPES)

Chỉ sinh khi trong ngữ cảnh có đủ dữ kiện.  
Thứ tự ưu tiên từ cao xuống thấp:

### Định nghĩa / Khái niệm (Definition)
* “LAN viết tắt cho từ gì?”  
* “Khái niệm QoS trong mạng di động có nghĩa là gì?”

### Chức năng / Thành phần / Chuẩn (Functionality & Standards)
* “Vai trò của lớp RRC trong mạng 5G là gì?”  
* “Theo ITU-R, có bao nhiêu dải tần được quy định cho 5G?”

### So sánh / Đặc tính / Thông số kỹ thuật (Comparison & Characteristics)
* “Sự khác biệt giữa 4G và 5G về độ trễ là gì?”  
* “Đặc điểm nổi bật của URLLC là gì?”

### Quy trình / Cơ chế hoạt động (Process & Mechanism)
* “Cách hoạt động của beamforming trong MIMO là gì?”  
* “Handover trong mạng 5G diễn ra như thế nào?”

### Thách thức / Hạn chế kỹ thuật (Challenges & Limitations)
* “Thách thức khi triển khai mạng mmWave là gì?”  
* “Nguyên nhân chính gây nhiễu tín hiệu là gì?”

---

## [CONTEXT]
{context}
---

## ĐỊNH DẠNG ĐẦU RA (Output)

Trả về **chính xác một mảng JSON hợp lệ**, không có mô tả, không có markdown.
Mỗi 1 câu hỏi có 4 phương án lựa chọn (chỉ có duy nhất 1 đáp án đúng và không được cố định vị trí đúng) và có giải thích ngắn gọn cho phương án đúng.
Đáp án đúng "answer" là số thứ tự của phương án đúng.

Ví dụ:
[
  {
    "question": "Dải tần FR2 trong mạng 5G nằm trong khoảng nào?",
    "choices": [
      "410 MHz – 7.125 GHz",
      "24.25 GHz – 52.6 GHz",
      "7.125 GHz – 24.25 GHz",
      "Dưới 1 GHz"
    ],
    "answer": "2",
    "explanation": "Ngữ cảnh xác định FR2 nằm trong khoảng từ 24.25 GHz đến 52.6 GHz."
  },
  {
    "question": "Đặc điểm chính của sóng mmWave (FR2) được nhắc đến là gì?",
    "choices": [
      "Băng thông lớn nhưng độ phủ sóng thấp",
      "Độ phủ sóng rộng hơn FR1",
      "Chỉ sử dụng cho mạng 4G",
      "Không bị ảnh hưởng bởi vật cản"
    ],
    "answer": "1",
    "explanation": "Ngữ cảnh nêu rõ FR2 (mmWave) cung cấp băng thông lớn nhưng độ phủ sóng thấp hơn FR1."
  }
]

Nếu không có câu hỏi hợp lệ, trả về **chính xác**:
[]

