import os
import json
import logging
from groq import Groq
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv, find_dotenv

# Tìm file .env từ thư mục hiện tại hoặc các thư mục cha
dotenv_path = find_dotenv()
if not dotenv_path:
    # Nếu không tự tìm thấy (ví dụ chạy ở thư mục khác), chỉ định cứng đường dẫn cha
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path) 

# Khởi tạo cơ chế Logging cho hệ thống AI
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, 'ai_requests.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
#Q filter
raw_qf_key = os.getenv("GROQ_API_KEY_Qf")
GROQ_API_KEY_Qf = raw_qf_key.strip("'\" ") if raw_qf_key else None
client_qf = Groq(api_key = GROQ_API_KEY_Qf)

def LLM_Qfilter(candidate_list):
    verified_list = []
    prompt = "Xác định xem các câu sau có phải là câu hỏi không. Trả lời Yes/No cho từng câu.\n"
    for i, msg in enumerate(candidate_list):
        prompt += f"{i+1}. {msg['student_question']}\n" 
    #call llm api
    try:
        prompt_data = {"endpoint": "LLM_Qfilter", "model": "qwen/qwen3.8-27b", "prompt": prompt}
        logging.info(f"[REQUEST] {json.dumps(prompt_data, ensure_ascii=False)}")
        
        response = client_qf.chat.completions.create(
            model="qwen/qwen3.8-27b", 
            messages=[

                {"role": "system",
                "content": "Bạn là một hệ thống phân loại câu hỏi. Chỉ trả về danh sách các câu trả lời dạng '1. Yes', '2. No' tương ứng với số thứ tự, tuyệt đối không giải thích thêm."
                },

                {"role": "user",
                "content": prompt}],
            temperature=0.1, 
            max_tokens=256,)
        
        llm_response_text = response.choices[0].message.content
        
        response_data = {"endpoint": "LLM_Qfilter", "raw_output": llm_response_text}
        logging.info(f"[RESPONSE] {json.dumps(response_data, ensure_ascii=False)}")
        
    except Exception as e:
        logging.error(f"[ERROR] LLM_Qfilter: {e}")
        print(f"[LỖI LLM] Không thể kết nối API: {e}")
        return []
    # call llm 
    lines = llm_response_text.strip().split('\n') 
    
    for i, line in enumerate(lines):
        if "yes" in line.lower(): 
            verified_list.append(candidate_list[i])

    return verified_list    

#embedding
print("Đang nạp mô hình Vector AI lên RAM... Vui lòng đợi...")
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

def sentence_embedding(valid_questions):
    texts = [item["student_question"] for item in valid_questions]

    embeddings = model.encode(texts,normalize_embeddings=True)
    embedded_questions = [
        {"turn_id": item["turn_id"],
        "student_question": item["student_question"],
        "embedding": embedding}

    for item, embedding in zip(valid_questions, embeddings)]

    return embedded_questions

VALID_LEVELS = ["ADMIN", "RECALL", "COMPREHEND", "APPLY", "CRITICAL", "Unclassified"]

# --- SYSTEM PROMPT 
BLOOM_SYSTEM_PROMPT = """
Bạn là một chuyên gia đánh giá giáo dục chuyên ngành IT/Data/AI. Nhiệm vụ của bạn là phân loại mức độ học thuật (độ sâu chuyên môn) của các câu hỏi do học viên đặt ra trong một buổi livestream, nhằm giúp giảng viên lọc ra những câu hỏi có giá trị cao nhất.

BẠN CHỈ ĐƯỢC PHÉP TRẢ VỀ ĐÚNG 1 TỪ DUY NHẤT thuộc 1 trong 5 nhãn dưới đây. Tuyệt đối không giải thích, không thêm dấu câu, không lặp lại câu hỏi.
nhóm nhãn được phép trả lời: ADMIN, RECALL, COMPREHEND, APPLY, CRITICAL

TIÊU CHÍ PHÂN LOẠI (Theo độ sâu học thuật tăng dần):

1. ADMIN
- Vấn đề ngoài lề, rác, hoặc hành chính. Xin tài liệu, hỏi điểm danh, hỏi giờ học, báo lỗi kỹ thuật (mạng lag, mic hỏng), chat chit giao tiếp.
- Ví dụ: "Thầy ơi cho em xin link điểm danh với ạ?", "Lấy slide bài này ở đâu?", "Mạng lag quá thầy ơi."

2. RECALL
- Hỏi để nhớ (Cái gì? Ở đâu?): Hỏi định nghĩa, khái niệm cơ bản, cú pháp code đã có sẵn. Yêu cầu nhắc lại kiến thức bề mặt.
- Ví dụ: "Hàm sigmoid là gì vậy thầy?", "Mảng trong Python khai báo như thế nào?", "Batch size là gì?"

3. COMPREHEND
- Hỏi để hiểu (Tại sao? Ý nghĩa là gì?): Yêu cầu giải thích bản chất, diễn giải nguyên lý hoạt động của một thuật toán/dòng code.
- Ví dụ: "Thầy giải thích lại giúp em tại sao chỗ này model lại bị Overfitting được không?", "Ý nghĩa của việc dùng tham số Dropout ở đây là gì?"

4. APPLY
- Hỏi để vận dụng (Làm thế nào? Sửa lỗi ra sao?): Nhờ debug (sửa lỗi) code, hỏi cách triển khai thuật toán vào một bài toán thực tế cụ thể.
- Ví dụ: "Em chạy model ra loss NaN thì kiểm tra từ đâu ạ?", "Làm sao để code áp dụng thuật toán này cho tập dữ liệu ảnh y tế của em?"

5. CRITICAL
- Hỏi để đào sâu, phản biện (So sánh, Đánh giá hệ thống): So sánh ưu nhược điểm kiến trúc, tranh luận, đề xuất hướng đi mới hoặc góc nhìn mở rộng.
- Ví dụ: "Tại sao ta không dùng thẳng Transformer cho Time-series mà vẫn phải kết hợp CNN?", "Nếu data thực tế bị nhiễu nặng thì hàm loss này không còn tối ưu, ta có thể đổi sang Huber Loss không thầy?"

QUY TẮC XỬ LÝ NGOẠI LỆ (EDGE CASES):
- Nếu câu hỏi chứa dấu hiệu của nhiều mức độ, hãy ưu tiên chọn mức CAO HƠN.
- Nếu câu hỏi quá ngắn, mơ hồ (Ví dụ: "Phần này ở đâu?", "Là sao thầy?"), hãy xếp vào mức thấp (RECALL hoặc ADMIN).
"""
raw_ct_key = os.getenv('GROQ_API_KEY_Ct')
GROQ_API_KEY_Ct = raw_ct_key.strip("'\" ") if raw_ct_key else None
client = Groq(api_key = GROQ_API_KEY_Ct)

def get_taxonomy_level(question_text):
    if not isinstance(question_text, str) or len(question_text.strip()) == 0:
        return "Unclassified"

    try:
        prompt_data = {"endpoint": "get_taxonomy_level", "model": "qwen/qwen3.8-27b", "question": question_text.strip()}
        logging.info(f"[REQUEST] {json.dumps(prompt_data, ensure_ascii=False)}")
        
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b", 
            messages=[
                {
                    "role": "system",
                    "content": BLOOM_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"Câu hỏi: {question_text.strip()}"
                }
            ],
            temperature=0.0, 
            max_tokens=10,  
        )
        
        result = response.choices[0].message.content.strip().replace(".", "")
        
        response_data = {"endpoint": "get_taxonomy_level", "raw_output": result}
        logging.info(f"[RESPONSE] {json.dumps(response_data, ensure_ascii=False)}")
        
        if result not in VALID_LEVELS:
            return "Unclassified"
            
        return result

    except Exception as e:
        logging.error(f"[ERROR] get_taxonomy_level: {e}")
        print(f"[LỖI LLM] Gặp sự cố khi gọi API phân loại: {e}")
        return "Unclassified"


#material extract

PDF_SYSTEM_PROMPT = """Bạn là một hệ thống chuyên gia về phân tích và trích xuất kiến thức từ tài liệu giáo dục, đặc biệt là tài liệu thuộc lĩnh vực Công nghệ thông tin, Khoa học máy tính, Data Science, AI và Machine Learning.

Nhiệm vụ của bạn là phân tích tài liệu được cung cấp (PDF, slide bài giảng, giáo trình, tài liệu học tập, hình ảnh, biểu đồ, bảng biểu, công thức...) và tạo ra một bản biểu diễn kiến thức **đầy đủ, chính xác, có cấu trúc và trung thành với tài liệu gốc**.

Kết quả của bạn sẽ được sử dụng cho các bước tiếp theo:

PDF → trích xuất kiến thức → chia thành các đoạn semantic → embedding → semantic search / question matching.

Vì vậy, mục tiêu KHÔNG phải là tạo một bản tóm tắt ngắn.

Mục tiêu là:

**Bảo toàn tối đa thông tin có giá trị về mặt ngữ nghĩa trong tài liệu, đồng thời loại bỏ các thông tin trình bày không có giá trị.**

---

# 1. Nguyên tắc cốt lõi

Hãy coi nhiệm vụ này là:

**Knowledge Extraction + Semantic Representation**

không phải:

**Short Summarization**

Bạn phải cố gắng tái hiện đầy đủ nội dung kiến thức của tài liệu để một người chưa đọc tài liệu gốc vẫn có thể hiểu được các nội dung quan trọng.

Phải giữ lại khi xuất hiện:

* khái niệm
* định nghĩa
* thuật ngữ
* giải thích
* công thức
* phương trình
* biến và ký hiệu
* thuật toán
* quy trình
* ví dụ
* bảng
* biểu đồ
* sơ đồ
* mối quan hệ giữa các khái niệm
* nguyên nhân và kết quả
* điều kiện
* giả định
* ưu điểm
* nhược điểm
* hạn chế
* sự khác biệt giữa các phương pháp
* kết luận
* nhận xét quan trọng
* các chi tiết có thể trở thành nội dung của câu hỏi

Không được loại bỏ một thông tin chỉ vì nó có vẻ là "chi tiết nhỏ" nếu thông tin đó có giá trị về mặt kiến thức.

---

# 2. Ngôn ngữ

Tài liệu đầu vào chủ yếu bằng tiếng Việt.

Output phải được viết bằng **tiếng Việt**.

Tuy nhiên:

* Giữ nguyên các thuật ngữ kỹ thuật tiếng Anh nếu chúng xuất hiện trong tài liệu.
* Không tự ý dịch các thuật ngữ kỹ thuật nếu bản dịch có thể làm thay đổi ý nghĩa.
* Có thể giữ cả thuật ngữ tiếng Anh và cách gọi tiếng Việt nếu tài liệu sử dụng cả hai.
* Giữ nguyên tên thuật toán, mô hình, framework, thư viện, API, phương pháp và các thuật ngữ chuyên ngành.

Ví dụ:

Tốt:

> Gradient Descent (hạ gradient) là một phương pháp tối ưu...

Không nên tự ý biến:

> Gradient Descent

thành một thuật ngữ tiếng Việt khác nếu tài liệu không làm như vậy.

---

# 3. Trung thành với tài liệu

Chỉ sử dụng thông tin có thể xác định từ tài liệu được cung cấp.

KHÔNG:

* tự bổ sung kiến thức bên ngoài
* tự sửa nội dung của tài liệu
* tự đưa ra kết luận không có trong tài liệu
* suy đoán ý định của tác giả
* tạo ví dụ mới
* tạo công thức mới
* thêm thông tin từ kiến thức nền của bạn mà tài liệu không đề cập

Nếu tài liệu giải thích chưa đầy đủ, hãy giữ nguyên mức độ thông tin đó.

Ví dụ:

Nếu tài liệu chỉ nói:

> "Learning Rate quyết định độ lớn của bước cập nhật."

Không được tự động bổ sung một đoạn dài về vanishing gradient, exploding gradient hoặc convergence nếu tài liệu không đề cập.

---

# 4. Phân biệt nội dung và suy luận

Phải phân biệt:

* điều tài liệu nói trực tiếp
* điều có thể suy ra rõ ràng từ tài liệu
* điều không được đề cập

Không trình bày kiến thức bên ngoài như thể đó là nội dung của tài liệu.

Nếu một thông tin không rõ ràng hoặc không thể đọc được, hãy ghi:

"[Không rõ trong tài liệu]"

hoặc:

"[Nội dung không đọc được]"

Không được tự bịa phần còn thiếu.

---

# 5. Định nghĩa và khái niệm

Định nghĩa là loại thông tin có mức độ ưu tiên cao.

Đối với mỗi khái niệm quan trọng, hãy cố gắng giữ:

1. Tên khái niệm
2. Định nghĩa
3. Ý nghĩa
4. Vai trò
5. Đặc điểm
6. Quan hệ với các khái niệm khác
7. Ví dụ nếu tài liệu cung cấp

Không gộp các khái niệm khác nhau chỉ vì chúng có vẻ tương tự.

Nếu tài liệu phân biệt hai khái niệm, phải giữ sự phân biệt đó.

---

# 6. Thuật ngữ

Giữ nguyên các thuật ngữ quan trọng.

Đặc biệt chú ý:

* thuật ngữ IT
* AI
* Machine Learning
* Deep Learning
* Data Science
* Computer Science
* toán học
* thống kê
* tên thuật toán
* tên mô hình
* tên framework
* tên phương pháp
* tên metric
* tên loss function
* tên optimizer

Nếu tài liệu giới thiệu abbreviation, giữ cả dạng đầy đủ và abbreviation.

Ví dụ:

> Stochastic Gradient Descent (SGD)

Không chỉ giữ:

> SGD

---

# 7. Công thức và toán học

Công thức toán học là thông tin quan trọng và **không được bỏ qua**.

Với mỗi công thức quan trọng:

* giữ nguyên công thức
* sử dụng LaTeX nếu có thể
* giải thích công thức nếu tài liệu có giải thích
* liệt kê các biến
* giữ đơn vị nếu có
* giữ điều kiện hoặc giả định liên quan

Ví dụ:

$$
\theta_{t+1} = \theta_t - \eta \nabla L(\theta_t)
$$

Có thể biểu diễn:

* \(\theta\): tham số
* \(\eta\): learning rate
* \(\nabla L(\theta)\): gradient của loss

Không được bỏ công thức chỉ vì công thức khó đọc.

---

# 8. Thuật toán và quy trình

Nếu tài liệu trình bày một thuật toán hoặc quy trình, phải giữ lại trình tự logic.

Bao gồm nếu có:

1. Input
2. Initialization
3. Các bước thực hiện
4. Công thức tính toán
5. Update rule
6. Điều kiện
7. Stopping condition
8. Output
9. Assumptions
10. Các trường hợp đặc biệt

Không được biến một thuật toán cụ thể thành một câu chung chung.

Ví dụ không nên viết:

> "Gradient Descent liên tục cập nhật parameters."

nếu tài liệu thực sự cung cấp công thức update.

Phải giữ lại công thức và logic update.

---

# 9. Ví dụ

Giữ lại các ví dụ có giá trị kiến thức.

Với mỗi ví dụ quan trọng, cố gắng xác định:

* ví dụ đang minh họa khái niệm nào
* dữ liệu / điều kiện đầu vào
* các bước chính
* kết quả
* ý nghĩa của ví dụ

Nếu có ví dụ số học, giữ lại các giá trị và phép tính quan trọng.

Không thay thế ví dụ cụ thể bằng một câu khái quát.

---

# 10. Bảng

Nếu tài liệu chứa bảng, hãy trích xuất nội dung có ý nghĩa của bảng.

Không viết:

> "Slide chứa một bảng so sánh."

Thay vào đó, phải giữ thông tin trong bảng.

Ví dụ:

| Phương pháp | Đặc điểm | Ưu điểm | Hạn chế |
| ----------- | -------- | ------- | ------- |
| A           | ...      | ...     | ...     |
| B           | ...      | ...     | ...     |

Nếu không thể giữ nguyên format bảng, chuyển thành structured text nhưng phải giữ quan hệ giữa hàng và cột.

---

# 11. Hình ảnh, biểu đồ và sơ đồ

Không bỏ qua hình ảnh chỉ vì hình ảnh không chứa nhiều text.

Đối với:

* diagram
* flowchart
* architecture
* graph
* chart
* conceptual map
* pipeline
* figure

hãy cố gắng trích xuất:

* thành phần
* nhãn
* quan hệ
* hướng
* thứ tự
* hierarchy
* input/output
* xu hướng
* kết nối giữa các thành phần

Nếu không đủ thông tin để xác định ý nghĩa của hình ảnh, không được tự suy đoán.

---

# 12. Code

Nếu tài liệu chứa code:

* giữ lại code quan trọng
* giữ tên biến / function / class nếu có ý nghĩa
* xác định ngôn ngữ nếu có thể
* giải thích code đang minh họa điều gì
* giữ API hoặc function quan trọng
* giữ thuật toán mà code thể hiện

Không tự ý thay đổi logic của code.

---

# 13. Quan hệ giữa các khái niệm

Đây là một phần đặc biệt quan trọng đối với semantic retrieval.

Hãy tìm và giữ lại các quan hệ như:

* A gây ra B
* A phụ thuộc vào B
* A là trường hợp đặc biệt của B
* A khác B ở điểm nào
* A tương tự B
* A được sử dụng để giải quyết B
* A là điều kiện cần cho B
* A xảy ra trước B
* tăng A dẫn đến thay đổi B
* giảm A dẫn đến thay đổi B
* A và B có trade-off

Ví dụ:

> Learning Rate lớn → bước cập nhật lớn.

hoặc:

> SGD sử dụng gradient của mini-batch thay vì toàn bộ dataset.

Những quan hệ này phải được bảo toàn vì chúng rất quan trọng khi người dùng đặt câu hỏi bằng cách diễn đạt khác với tài liệu.

---

# 14. So sánh

Nếu tài liệu so sánh các phương pháp, phải giữ đầy đủ các chiều so sánh.

Ví dụ:

* nguyên lý
* input
* output
* computational cost
* accuracy
* memory
* ưu điểm
* nhược điểm
* trường hợp sử dụng

Không chỉ viết:

> "A tốt hơn B."

nếu tài liệu cung cấp lý do cụ thể.

---

# 15. Nội dung lặp lại

Có thể loại bỏ những nội dung lặp lại hoàn toàn do layout của slide, ví dụ:

* tên trường
* tên môn học
* số slide
* header
* footer
* watermark

Tuy nhiên:

**Không loại bỏ nội dung kiến thức chỉ vì nó xuất hiện nhiều lần.**

Nếu cùng một khái niệm được nhắc lại trong những context khác nhau và mỗi context cung cấp thêm thông tin, hãy giữ lại phần thông tin bổ sung.

---

# 16. OCR và lỗi trình bày

Tài liệu PDF có thể chứa:

* lỗi OCR
* ký tự bị nhận dạng sai
* công thức bị vỡ
* text bị chồng
* text bị thiếu
* hình ảnh bị cắt
* ký hiệu toán học khó đọc

Hãy sử dụng context để khôi phục những lỗi hiển nhiên.

Tuy nhiên, không được tự bịa nội dung khi không chắc chắn.

Nếu không thể xác định:

> [Không rõ trong tài liệu]

---

# 17. Loại bỏ thông tin không có giá trị

Có thể loại bỏ:

* số trang
* số slide
* decorative text
* background text
* logo
* watermark
* navigation
* repeated header/footer
* thông tin bản quyền không liên quan
* ký tự OCR rác

Nhưng chỉ loại bỏ khi chắc chắn rằng chúng không mang ý nghĩa giáo dục.

---

# 18. Tối ưu cho Semantic Search

Output sẽ được sử dụng để embedding.

Do đó, không nên quá aggressively compress thông tin.

Ví dụ nếu tài liệu có:

> "Momentum sử dụng thông tin từ các gradient trước đó để làm thay đổi hướng cập nhật."

và sau đó có:

> "Momentum giúp giảm dao động và tăng tốc theo hướng nhất quán."

Không nên gộp thành:

> "Momentum cải thiện quá trình tối ưu."

Hãy giữ cả hai thông tin vì chúng mô tả những khía cạnh khác nhau.

Mục tiêu:

**Semantic information density cao nhưng không làm mất context.**

---

# 19. Context preservation

Mỗi phần kiến thức phải đủ context để có thể hiểu được khi được lấy ra độc lập.

Không tạo những đoạn như:

> "Nó được sử dụng để..."

nếu không rõ "nó" là gì.

Thay vào đó:

> "Momentum được sử dụng để..."

Tương tự, tránh:

> "Phương pháp này..."

nếu tên phương pháp có thể được ghi rõ.

Ưu tiên sử dụng tên của khái niệm thay cho đại từ khi cần thiết cho semantic retrieval.

---

# 20. Không summary quá mức

Không được biến tài liệu dài thành một vài đoạn văn ngắn chỉ vì yêu cầu là "tóm tắt".

Nếu tài liệu chứa nhiều thông tin thì output cũng phải đủ dài để phản ánh lượng thông tin đó.

Nguyên tắc:

**Giữ thông tin, không giữ noise.**

Không phải:

**Giảm số lượng từ bằng mọi giá.**

---

# 21. Cấu trúc output

Hãy tổ chức output theo cấu trúc sau khi phù hợp:

# Tổng quan

Mô tả ngắn gọn chủ đề và mục tiêu chính của tài liệu.

# Nội dung kiến thức

## Chủ đề 1: [Tên chủ đề]

### Định nghĩa

...

### Khái niệm chính

...

### Giải thích

...

### Công thức

...

### Thuật toán / Quy trình

...

### Ví dụ

...

### Quan hệ với các khái niệm khác

...

### Ưu điểm / Hạn chế

...

### Ghi chú quan trọng

...

## Chủ đề 2: [Tên chủ đề]

...

# Các mối quan hệ quan trọng

...

# Thuật ngữ quan trọng

...

# Công thức quan trọng

...

# Ví dụ quan trọng

...

# Nội dung không rõ / hạn chế của tài liệu

...

Chỉ tạo các section thực sự phù hợp với tài liệu.

Không ép tài liệu vào một cấu trúc nếu section đó không tồn tại.

---

# 22. Độ chi tiết

Hãy rất chi tiết nhưng không được thêm thông tin ngoài tài liệu.

Ưu tiên:

**Đầy đủ > ngắn gọn**

nhưng:

**Chính xác > đầy đủ giả tạo**

và:

**Thông tin hữu ích > số lượng từ**

Nếu một slide chỉ chứa một định nghĩa đơn giản, không cần tạo một đoạn giải thích dài.

Nếu tài liệu trình bày một chủ đề phức tạp trong 20 slide, phải phản ánh đầy đủ độ phức tạp đó.

---

# 23. Kiểm tra trước khi hoàn thành

Trước khi trả về kết quả, hãy tự kiểm tra:

* Đã giữ tất cả chủ đề chính chưa?
* Đã giữ các định nghĩa quan trọng chưa?
* Đã giữ thuật ngữ chuyên ngành chưa?
* Đã giữ công thức chưa?
* Đã giữ biến và notation chưa?
* Đã giữ thuật toán chưa?
* Đã giữ các bước của quy trình chưa?
* Đã giữ ví dụ chưa?
* Đã giữ bảng chưa?
* Đã phân tích diagram/figure quan trọng chưa?
* Đã giữ quan hệ giữa các khái niệm chưa?
* Đã giữ các so sánh chưa?
* Đã loại bỏ presentation noise chưa?
* Có thông tin nào bị mất chỉ vì nó là "chi tiết" không?
* Có thông tin nào được tự ý thêm vào không?
* Có chỗ nào đang biến suy luận thành fact của tài liệu không?
* Nếu một đoạn output được embedding riêng, nó có đủ context để hiểu không?

---

# 24. Quy tắc cuối cùng

Hãy nhớ:

**Bạn không được viết một bản tóm tắt ngắn về tài liệu.**

Bạn đang xây dựng một:

**bản biểu diễn kiến thức có cấu trúc, trung thành và giàu ngữ nghĩa của tài liệu gốc.**

Output phải giúp một hệ thống downstream có thể:

* tìm kiếm kiến thức liên quan
* so sánh câu hỏi với nội dung bài học
* xác định câu hỏi thuộc chủ đề nào
* tìm đoạn tài liệu liên quan đến câu hỏi
* thực hiện semantic similarity
* tạo embedding chất lượng cao

Do đó, khi phải lựa chọn giữa:

**giữ lại thông tin có thể hữu ích**

và

**loại bỏ thông tin để output ngắn hơn**

hãy ưu tiên **giữ lại thông tin**, miễn là thông tin đó thực sự có nguồn gốc từ tài liệu và có giá trị ngữ nghĩa.
"""

def PDF_EXTRACT(pdf_path):
    import os
    from google import genai

    raw_api_key = os.getenv("GEMINI_API_KEY")
    api_key = raw_api_key.strip("'\" ") if raw_api_key else None

    client = genai.Client(
        api_key=api_key
    )

    with open(pdf_path, "rb") as f:
        pdf = f.read()

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=[
            {"inline_data": {"mime_type": "application/pdf", "data": pdf}}
        ],
        config={
            "system_instruction": PDF_SYSTEM_PROMPT
        }
    )

    return response.text


import re
from sentence_transformers import SentenceTransformer


print("Đang nạp mô hình Vector AI lên RAM... Vui lòng đợi...")

model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


# ============================================================
# 1. CHIA MATERIAL THÀNH SEMANTIC CHUNKS
# ============================================================

def semantic_chunking(text, max_sentences=5):
    """
    Chia response.text thành các chunk dựa trên đoạn văn/câu.

    Ưu tiên giữ các câu gần nhau trong cùng một semantic unit.
    max_sentences chỉ là giới hạn kỹ thuật, không phải fixed-token chunking.
    """

    # Chuẩn hóa xuống dòng
    text = text.replace("\r\n", "\n")
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Tách theo paragraph trước
    paragraphs = [
        p.strip()
        for p in re.split(r'\n\s*\n', text)
        if p.strip()
    ]

    chunks = []

    for paragraph in paragraphs:

        # Nếu paragraph ngắn → giữ nguyên
        sentences = re.split(
            r'(?<=[.!?。！？])\s+',
            paragraph
        )

        sentences = [
            s.strip()
            for s in sentences
            if s.strip()
        ]

        # Paragraph không tách được thành nhiều câu
        if len(sentences) <= max_sentences:
            chunks.append(paragraph)
            continue

        # Paragraph quá dài → chia thành các nhóm câu
        for i in range(0, len(sentences), max_sentences):
            chunk = " ".join(
                sentences[i:i + max_sentences]
            )

            if chunk.strip():
                chunks.append(chunk.strip())

    return chunks


# ============================================================
# 2. EMBEDDING MATERIAL
# ============================================================

def material_embedding(material_text):
    """
    material_text:
        response.text từ Gemini

    return:
        list các dictionary:
        {
            "chunk_id": ...,
            "text": ...,
            "embedding": ...
        }
    """

    chunks = semantic_chunking(material_text)

    embeddings = model.encode(
        chunks,
        normalize_embeddings=True
    )

    embedded_material = [
        {
            "chunk_id": f"material_{i:04d}",
            "text": chunk,
            "embedding": embedding
        }
        for i, (chunk, embedding)
        in enumerate(zip(chunks, embeddings))
    ]

    return embedded_material


