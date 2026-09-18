from groq import Groq
import os
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
load_dotenv() 

#Q filter
GROQ_API_KEY_Qf = os.getenv("GROQ_API_KEY_Qf")
client_qf = Groq(api_key = GROQ_API_KEY_Qf)

def LLM_Qfilter(candidate_list):
    verified_list = []
    prompt = "Xác định xem các câu sau có phải là câu hỏi không. Trả lời Yes/No cho từng câu.\n"
    for i, msg in enumerate(candidate_list):
        prompt += f"{i+1}. {msg['student_question']}\n" 
    #call llm api
    try:
        response = client_qf.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=[

                {"role": "system",
                "content": "Bạn là một hệ thống phân loại câu hỏi. Chỉ trả về danh sách các câu trả lời dạng '1. Yes', '2. No' tương ứng với số thứ tự, tuyệt đối không giải thích thêm."
                },

                {"role": "user",
                "content": prompt}],
            temperature=0.1, 
            max_tokens=256,)
        
        llm_response_text = response.choices[0].message.content
        
    except Exception as e:
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
GROQ_API_KEY_Ct = os.getenv('GROQ_API_KEY_Ct')
client = Groq(api_key = GROQ_API_KEY_Ct)

def get_taxonomy_level(question_text):
    if not isinstance(question_text, str) or len(question_text.strip()) == 0:
        return "Unclassified"

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
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
        
        if result not in VALID_LEVELS:
            return "Unclassified"
            
        return result

    except Exception as e:
        print(f"[LỖI LLM] Gặp sự cố khi gọi API phân loại: {e}")
        return "Unclassified"