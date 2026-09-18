# Nhật ký người ngoài dùng thử (R6)

## 1. Danh sách người dùng thử (3 người)
- **Nguyễn Thị Hồng Nhung** - 2A202602557 (Willing user CP1)
- **Vũ Văn Điền** - 2A202602418 (Willing user CP1)
- **Nguyễn Bảo Sơn** - 2A202602402 (Willing user)

## 2. Bảng nhật ký

| Người thử (tên/vai - willing user?) | Task đã giao | Quan sát | Quote nguyên văn | Mức nghiêm trọng |
|---|---|---|---|---|
| Nguyễn Thị Hồng Nhung (Giảng viên - Willing user CP1) | Mở dashboard Q&A, lướt đọc danh sách Top 5 câu hỏi được gợi ý. | User nhìn vào danh sách câu hỏi khá lâu và lúng túng khi thấy có các con số (điểm xếp hạng) nhưng không rõ ý nghĩa. | *"Tính năng thì ổn đấy, gom câu hỏi khá đúng ý, nhưng mình thắc mắc cái điểm số này AI nó tính ra kiểu gì thế? Nhìn số không thế này lỡ nó đánh giá sai mình cũng không biết được."* | Trung bình (Cần làm rõ cơ chế AI để tăng độ tin cậy) |
| Vũ Văn Điền (Giảng viên - Willing user CP1) | Theo dõi bảng Radar trong lúc hệ thống mô phỏng việc đẩy dữ liệu log mới vào liên tục. | User đang đọc dở một câu hỏi thì màn hình bị tải lại đột ngột khiến họ bị mất dấu dòng đang xem. | *"Cái giao diện này sao nó bị refresh liên tục thế? Đang đọc dở một câu hỏi thì bảng nó tự chớp một cái, bất tiện quá."* | Cao (Gây gián đoạn trực tiếp đến trải nghiệm cốt lõi) |
| Nguyễn Bảo Sơn (Trợ giảng - Willing user) | Ấn xem chi tiết bên trong các cụm câu hỏi đã được AI gom nhóm lại. | User phát hiện AI thi thoảng nhận diện nhầm và gộp 2 câu không liên quan vào chung một nhóm. | *"Ủa sao cái câu hỏi về bài tập về nhà với câu thắc mắc về deadline lại bị gộp chung vào một cụm thế này? Nó gom sai rồi."* | Trung bình (Cần tinh chỉnh lại prompt/model gom cụm) |

## 3. Tổng kết (4 dòng)
- **Chủ đề lặp nhiều nhất:** Giao diện bị làm mới tự động gây gián đoạn và AI giải thích chưa rõ ràng về cách tính điểm xếp hạng.
- **Thay đổi đã làm:** Bỏ tính năng tự động refresh bảng dữ liệu (thay bằng báo có tin nhắn mới) và thêm tooltip hiển thị rõ lý do tính điểm khi di chuột vào điểm số.
- **Phần giữ nguyên có lý do:** Chỉ giới hạn hiển thị Top 5 câu hỏi để ép giảng viên tập trung giải quyết trong thời lượng 15 phút Q&A, tránh việc có quá nhiều thông tin khiến họ bị rối.
- **Phần đưa vào backlog:** Việc tinh chỉnh lại thuật toán gom cụm (Clustering) tránh bị dính rác từ khóa sẽ được đưa vào backlog xử lý sau do cần nhiều thời gian tune prompt.
