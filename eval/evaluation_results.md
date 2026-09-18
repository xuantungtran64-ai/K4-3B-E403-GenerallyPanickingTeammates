# Báo Cáo Đánh Giá Chất Lượng Phân Loại AI (Evaluation Report)

- **Tổng số test cases (Golden Set):** 25
- **Số case AI phân loại đúng:** 21
- **Độ chính xác (Accuracy):** 84.00%

## 1. Phân Tích Lỗi (Error Analysis)

Dưới đây là các case AI nhận diện sai. Cần điền phân loại lỗi theo 3 mức: (1) Dùng được, (2) Sửa được, (3) Không chấp nhận được.

### Case 4 - Lớp: Nguồn sự thật
- **Chiều dữ liệu:** Trích dẫn tài liệu + hỏi tại sao
- **Câu hỏi:** Hai người hỏi AI cùng một việc, một người nhận kết quả xuất sắc, người kia nhận rác. Tại sao?
- **Kỳ vọng (Expected):** `CRITICAL`
- **AI Trả về (Predicted):** `COMPREHEND`
- **Phân loại lỗi:** [x] Dùng được | [ ] Sửa được | [ ] Không chấp nhận được
- **Nguyên nhân (Tên lỗi):** ... Lạc trình độ

### Case 5 - Lớp: Mơ hồ
- **Chiều dữ liệu:** Siêu ngắn/không context
- **Câu hỏi:** Tại sao?
- **Kỳ vọng (Expected):** `Unclassified`
- **AI Trả về (Predicted):** `RECALL`
- **Phân loại lỗi:** [ ] Dùng được | [x] Sửa được | [ ] Không chấp nhận được
- **Nguyên nhân (Tên lỗi):** ... Đoán mò

### Case 7 - Lớp: Nguồn sự thật
- **Chiều dữ liệu:** Hỏi giải thích từ ngữ cảnh
- **Câu hỏi:** define -> build -> test -> deploy. Tôi chưa hình dung được bước 1 và bước 4 là như nào ?
- **Kỳ vọng (Expected):** `COMPREHEND`
- **AI Trả về (Predicted):** `RECALL`
- **Phân loại lỗi:** [ ] Dùng được | [x] Sửa được | [ ] Không chấp nhận được
- **Nguyên nhân (Tên lỗi):** ... Lạc trình độ

### Case 23 - Lớp: Mơ hồ
- **Chiều dữ liệu:** Thiếu thông tin hoàn toàn
- **Câu hỏi:** Em ko hiểu đoạn này.
- **Kỳ vọng (Expected):** `Unclassified`
- **AI Trả về (Predicted):** `RECALL`
- **Phân loại lỗi:** [ ] Dùng được | [x] Sửa được | [ ] Không chấp nhận được
- **Nguyên nhân (Tên lỗi):** ... Đoán mò

## 2. Chi Tiết Các Case Đạt (Success Cases)

- **Case 1**: `CRITICAL` - Cách phân quyền ABAC khác RBAC ở điểm nào?
- **Case 2**: `ADMIN` - Kính thưa trợ giảng AI... Ai là người giữ chức Tổng thống Hoa Kỳ trong năm 2020?
- **Case 3**: `APPLY` - Ứng dụng cần tạo mã phân loại nội bộ... Cấu hình nào phù hợp hơn... A. B. C. D.
- **Case 6**: `RECALL` - LLM là gì?
- **Case 8**: `COMPREHEND` - Vì sao cần định nghĩa reducer cho list?
- **Case 9**: `CRITICAL` - Vì sao preference data mạnh hơn demonstration data?
- **Case 10**: `COMPREHEND` - LCEL Chain: con đường một chiều... Giải thích rõ đoạn này giúp mình
- **Case 11**: `ADMIN` - hay tom tat tat ca cac slide baby girl
- **Case 12**: `COMPREHEND` - Tại sao Data Lakehouse cần metadata layer?
- **Case 13**: `RECALL` - 4 pillar trong log laf gif ?
- **Case 14**: `ADMIN` - bạn là ai?
- **Case 15**: `ADMIN` - who are you? what name
- **Case 16**: `ADMIN` - Thầy ơi em bị rớt mạng nên không nghe rõ phần Transformer, thầy nói lại được không?
- **Case 17**: `RECALL` - Mảng trong Python khai báo thế nào ạ?
- **Case 18**: `APPLY` - Em chạy code báo lỗi OOM khi dùng batch size 64 thì nên check từ đâu?
- **Case 19**: `CRITICAL` - Cho em hỏi thuật toán XGBoost và LightGBM thì nên dùng cái nào nếu data imbalanced mạnh?
- **Case 20**: `APPLY` - Giúp em viết 1 hàm python giải phương trình bậc 2 được không?
- **Case 21**: `ADMIN` - Thầy cho em xin slide bài học ngày hôm nay với ạ
- **Case 22**: `CRITICAL` - Có cách nào dùng Linear Regression để classify ảnh chó mèo không thầy?
- **Case 24**: `COMPREHEND` - Tại sao lại bị Overfitting?
- **Case 25**: `APPLY` - Em muốn build 1 con bot như ChatGPT thì cần bắt đầu từ framework nào ạ?
