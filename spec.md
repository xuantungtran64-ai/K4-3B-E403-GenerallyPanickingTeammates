# AI SPEC — Live Q&A Radar · Nhóm GenerallyPanickingTeammates · Lớp 3B - Phòng E403
Hướng: [ ] A — VLearn  [ ] B — Trợ lý Học viên  [x] E — Làn mở (Track E)
Loại: [ ] Tối ưu tính năng có sẵn  [x] Tính năng mới

## §1. User & Job
- **Job executor + workflow:** Giảng viên / Diễn giả Workshop. Khi bước vào 15 phút Q&A cuối giờ, giảng viên nhìn vào khung chat để tìm các câu hỏi hay, giải đáp trực tiếp trên livestream.
- **Core JTBD:** Lọc và chọn ra các câu hỏi trọng tâm, có tính chuyên môn cao nhất từ hàng trăm tin nhắn của học viên để trả lời trong giới hạn 15 phút.
- **Problem statement:** Giảng viên tốn quá nhiều thời gian lướt đọc và phân loại thủ công hàng loạt tin nhắn, dẫn đến việc bỏ sót những câu hỏi đào sâu kiến thức và lãng phí thời gian vào các câu hỏi hành chính, tin nhắn rác hoặc những câu trùng lặp nhau.
- **Evidence (Chuẩn B - Data Mining từ repo):**
  - **Số liệu mining:** 
    - Đỉnh điểm phiên học ngày 30/07 có tới **2.579 tin nhắn**.
    - Khung 15 phút Q&A (10:00 - 10:15 ngày 30/07) nhận **341 tin nhắn** (~23 tin/phút).
    - Phân tích ngữ nghĩa: **Chỉ có 41.6%** tin nhắn trên VLearn (5.614/13.494) và **53.7%** tin nhắn tag BOT trên Discord (165/307) thực sự là câu hỏi. Còn lại là rác, trích dẫn, hoặc chit-chat.
  - **≥5 ví dụ nguyên văn + nguồn:**
    - (Hỏi thật) `T00244`: *"mình có thể tải slide bài học bằng cách nào?"*
    - (Hỏi thật) `T00277`: *"model được vlearn tutor dùng là model nào"*
    - (Hỏi thật) `M13974` (Discord): *"[@BOT] xem xp ở đâu"*
    - (Không phải hỏi) `T00311`: *"hi"* / *"chào"*
    - (Không phải hỏi) `M13888` (Discord): *"[@BOT] anh cảm ơn em"*

## §2. Impact & quyết định chọn
- **Bảng impact ≥3 ứng viên:**
  | Ứng viên | Bao nhiêu người | Tần suất | Tốn gì mỗi lần | Khả thi | Chọn? |
  |---|---|---|---|---|---|
  | **1. Trợ lý gom cụm Q&A Radar** | ~10 Giảng viên/Diễn giả | Mỗi buổi Live (Q&A 15p) | Mất 5-10p lọc thủ công, bỏ lỡ câu hỏi đắt giá | Cao | **Có** |
  | **2. Bot tự động trả lời Discord** | ~1.000 Học viên | Hàng ngày | Học viên phải đợi TA trả lời nếu bot sập | Vừa | Không |
  | **3. AI tóm tắt report buổi học** | ~20 TA/Mod | Cuối mỗi buổi | Tốn 30-45p viết report thủ công | Cao | Không |
- **Ứng viên ĐÃ LOẠI + vì sao:** 
  - (2) Bot tự động trả lời: Cost-of-error quá đắt. Sai kiến thức cốt lõi sẽ khiến học viên hiểu sai, làm mất uy tín khóa học.
  - (3) Tóm tắt report: Pain point không "đau" bằng, TA có thể làm từ từ sau giờ học, không bị áp lực "thời gian thực" (real-time) như Giảng viên trên sóng trực tiếp.
- **Ứng viên CHỌN + vì sao:** (1) Q&A Radar. Hỗ trợ ngay lập tức bài toán real-time với khối lượng dữ liệu khổng lồ (341 tin nhắn/15 phút). Giải quyết chính xác nút thắt cổ chai mà con người không thể tự làm.

## §3. Giải pháp tương tự đã nghiên cứu
- **Slido / Mentimeter:**
  - Flow: Người dùng vào link ngoài, nhập câu hỏi, khán giả vote up.
  - Đáng học: Bảng xếp hạng câu hỏi rõ ràng (Top Voted).
  - Đáng né: Bắt người dùng dùng app thứ 3 (context switch), không tận dụng được khung chat có sẵn trên VLearn/Zoom.
  - Mình khác gì: AI tự động phân tích luồng chat có sẵn, tự gom cụm câu trùng lặp mà không cần học viên vote.
- **Zoom Q&A Feature:**
  - Flow: Có box Q&A riêng biệt với chat.
  - Đáng học: Giảng viên có thể mark "Answered live".
  - Đáng né: Vẫn hiển thị mọi câu hỏi, không tự lọc rác hay đánh giá độ sâu kiến thức.

## §4. Thiết kế
- **Lát cắt MỘT CÂU:** Giảng viên bắt đầu 15 phút Q&A $\rightarrow$ AI tự động quét log, gom cụm các câu trùng lặp, lọc rác và đối chiếu Transcript để xếp hạng độ sâu $\rightarrow$ Trình bày Top 5 câu hỏi trọng tâm nhất để Giảng viên trả lời ngay.
- **Non-goals (≥3 thứ KHÔNG build):**
  1. KHÔNG tự động trả lời thay giảng viên (No Auto-reply).
  2. KHÔNG tích hợp trực tiếp thay đổi database hệ thống VLearn (chỉ chạy UI Overlay/Dashboard đọc log).
  3. KHÔNG đánh giá thái độ (sentiment) của người hỏi.
- **Mức prototype nhắm tới:** [ ] Sketch [ ] Mock [x] Working 
  - Phần thật: Backend đọc log, AI nhúng embedding, gom cụm (KMeans) và call LLM để rank độ sâu kiến thức. 
  - Phần mock: UI Frontend đơn giản call API.
- **Automation:** [x] Augment [ ] Conditional [ ] Automate 
  - **Lý do theo cost-of-error:** Nếu AI tự trả lời (Automate) mà sai kiến thức (Hallucinate) thì hậu quả rất nghiêm trọng. AI chỉ đóng vai trò phân tích, xếp hạng (Augment). Quyết định trả lời hay không và trả lời như thế nào hoàn toàn do Giảng viên (nguồn sự thật cuối cùng).
- **§4b. Nguyên tắc đã áp dụng (HAX/PAIR):**
  | Nguyên tắc | Áp cụ thể vào đâu trong prototype |
  |---|---|
  | **G1 - Làm rõ hệ thống làm được gì** | Header UI ghi: "AI đang quét và gợi ý Top 5 câu hỏi từ Chat" |
  | **G2 - Làm rõ nó làm tốt đến đâu** | Cạnh mỗi cụm câu hỏi hiển thị số lượng câu trùng (ví dụ: "3 câu hỏi tương tự") |
  | **G8 - Gạt bỏ dễ dàng** | Giảng viên có nút "Skip/Hide" để ẩn ngay một câu hỏi nếu AI gợi ý sai |
  | **G11 - Giải thích vì sao** | Tooltip hiển thị lý do rank cao: "Matching với keyword của Slide 14" |

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản (≥8)
*(Chi tiết sẽ hoàn thiện trong quá trình build)*
- ① **Nguồn sự thật:** AI xếp hạng cao một câu hỏi nằm ngoài phạm vi khóa học vì tưởng là "chuyên sâu".
- ② **Mơ hồ:** Câu hỏi quá ngắn "Phần này ở đâu?".
- ③ **Ngoài phạm vi:** Học viên hỏi xin code giải bài tập cuối khóa.
- ④ **Đặc thù domain:** Nhận diện nhầm câu "Xin lỗi" thành câu hỏi kiến thức.

## §6. Bốn đường đi của trải nghiệm
- **Happy path:** AI nhận diện đúng cụm câu hỏi, xếp hạng chuẩn, giảng viên trả lời mượt mà.
- **Low-confidence (②):** Câu hỏi thiếu context -> Đẩy vào mục "Câu hỏi khác" thay vì Top 5.
- **Failure/không căn cứ (①):** AI lọc sót rác -> Giảng viên ấn "Skip/Hide".
- **Correction (user sửa):** Giảng viên bấm xem chi tiết các câu gốc trong cụm để hiểu rõ ý học viên hơn thay vì chỉ đọc câu tóm tắt của AI.
- **Khi bị đòi ngoài phạm vi (③):** Đánh dấu tag "Out of scope" mờ đi.
- **Case đặc thù domain (④):** Các câu hỏi về admin (điểm danh, lỗi mạng) bị nhận diện nhầm -> Cung cấp nút để Giảng viên gửi thẳng sang TA.

## §7. Kiểm thử
- **Chiều chất lượng + định nghĩa kiểm chứng được:** 
  1. *Relevance:* Top 5 gợi ý phải là câu hỏi thực sự, không chứa spam/chit-chat.
  2. *Clustering accuracy:* Các câu trong cùng một cụm phải có chung ý nghĩa.
- **Golden set:** (Sẽ bổ sung vào thư mục `eval/` gồm ≥20 case).
- **Quality bar:** "Đạt khi ≥ 80% câu hỏi trong Top 5 không bị Giảng viên ấn nút Hide/Skip, và độ gom cụm đúng ý >85%".
- **Kết quả các lượt chạy:** (Cập nhật sau khi run).

## §8. Phân công & kế hoạch
*(Đội trưởng điền chi tiết vào `README.md`)*
- Spec / Evidence / Prompt / Code / Demo: Chia đều cho các thành viên.
- Willing users: Cần mời 2 giảng viên/TA dùng thử.

## §9. Changelog
| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) |
|---|---|---|
| Mốc CP1 | Cập nhật EDA | Đã chứng minh chatlog chứa >50% tin nhắn rác không phải câu hỏi |

