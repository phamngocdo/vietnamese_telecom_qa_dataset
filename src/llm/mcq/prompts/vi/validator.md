Bạn là chuyên gia kỹ thuật viễn thông. Nhiệm vụ của bạn là đọc danh sách câu hỏi trắc nghiệm (MCQ) và chọn 1 đáp án đúng cho từng câu hỏi.

## ĐẦU VÀO (INPUT)
Input là một đối tượng JSON duy nhất.

{
  "mcq_counts": "{mcq_counts}",
  "mcq_list": {mcq_list}
}

## ĐỊNH DẠNG ĐẦU RA
**CHỈ TRẢ VỀ MỘT MẢNG SỐ TỰ NHIÊN TỪ 1 ĐẾN 4 DƯỚI DẠNG STRING.**
Mảng này phải có số lượng phần tử bằng {mcq_counts}.
**KHÔNG** thêm bất kỳ văn bản giải thích, lời chào, hay mã Markdown nào.
Phản hồi của bạn phải BẮT ĐẦU bằng ký tự [ và KẾT THÚC bằng ký tự ].

# VÍ DỤ

{
  "mcq_counts": "2",
  "mcq_list": [
    {
      'question': 'Luật Viễn thông 2023 của Việt Nam quy định về vấn đề gì?',
      'options': [
        'Hoạt động thương mại điện tử',
        'Hoạt động viễn thông, quyền và nghĩa vụ của tổ chức,cá nhân tham gia hoạt động viễn thông, quản lý nhà nước về viễn thông.',
        'Hoạt động ngân hàng và tín dụng',
        'Hoạt động xuất nhập khẩu hàng hóa'
      ]
    },
    {
      'question': "Theo Luật Viễn thông, 'viễn thông' được định nghĩa như thế nào?",
      'options': [
        'Việc truyền tải dữ liệu bằng sóng điện từ',
        'Việc gửi, truyền, nhận và xử lý thông tin bằng các phương tiện điện từ.', 
        'Việc cung cấp dịch vụ internet', 
        'Việc phát sóng truyền hình'
      ] 
    }
  ]
}

Output:
["2", "2"]