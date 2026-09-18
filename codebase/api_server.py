import time
import threading
from datetime import datetime, timedelta
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import logic nội bộ từ team bạn
import Q_tools as Qt
from Q_tools import ChatDataIngestor as CDI
import S_tools as St

app = FastAPI()

# Cấu hình CORS để Frontend (Web) ở port khác có thể gọi API được
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cho phép mọi Web kết nối
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 1. BIẾN TOÀN CỤC (GLOBAL STATE)
# ==========================================
clusters = []
data_path = os.path.join(os.path.dirname(__file__), '..', 'mock_tutor_turns.csv')
data_ingestor = CDI(data_path)
current_simulated_time = datetime.strptime('2026-07-23 15:20:00', "%Y-%m-%d %H:%M:%S")

pdf_path = r'D:\vin\Hackathon_mini\banned\K4-3B-Day05-06-AI-Product-Hackathon-main\data\vlearn-pack\slides\d1-slide-hackathon.pdf'
print("Đang xử lý tài liệu bài giảng (PDF)...")
try:
    lecture_text = St.PDF_EXTRACT(pdf_path) if pdf_path else ""
    global_lecture_vectors = St.material_embedding(lecture_text) if lecture_text else []
except Exception as e:
    print(f"Lỗi trích xuất PDF: {e}")
    global_lecture_vectors = []

# ==========================================
# 2. LUỒNG CHẠY NGẦM AI (BACKGROUND THREAD)
# ==========================================
def background_ai_loop():
    global current_simulated_time, clusters
    while True:
        print(f"[AI THREAD] Đang quét tin nhắn lúc: {current_simulated_time}")
        new_msg = data_ingestor.fetch_new_messages(current_simulated_time.strftime("%Y-%m-%d %H:%M:%S"))
        
        if new_msg:
            try:
                # 1. Lọc rác & LLM Qfilter
                valid_questions = []
                candidate_queue = []
                for msg in new_msg:
                    status = Qt.classify_message_rulebase(msg['student_question'])
                    if status == Qt.STATUS_SURE_QUESTION:
                        valid_questions.append(msg)
                    elif status == Qt.STATUS_CANDIDATE:
                        candidate_queue.append(msg)
                
                if candidate_queue:
                    valid_questions.extend(St.LLM_Qfilter(candidate_queue))
                
                if valid_questions:
                    # 2. Nhúng Vector & Phân cụm
                    embedded_Q = St.sentence_embedding(valid_questions)
                    for item in embedded_Q:
                        clusters = Qt.vector_cluster(clusters, item['embedding'], item['student_question'], item['turn_id'], 0.85)
                    
                    # 3. Phân loại Taxonomy
                    for c in clusters:
                        if "taxonomy_level" not in c:
                            c['taxonomy_level'] = St.get_taxonomy_level(c['representative_msg']['text'])
                    
                    # 4. Tính điểm Z-score
                    Qt.scoring(clusters, lecture_vectors=global_lecture_vectors)
            except Exception as e:
                print(f"[AI THREAD] Lỗi: {e}")
        
        current_simulated_time += timedelta(seconds=30)
        time.sleep(5) # Tạm dừng 5 giây thực tế rồi quét tiếp

# Tự động kích hoạt AI Thread khi bật Server API
@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=background_ai_loop, daemon=True)
    thread.start()

# ==========================================
# 3. CÁC API DÀNH CHO FRONTEND
# ==========================================

@app.get("/api/top-questions")
def get_top_questions():
    """
    Frontend dùng Javascript gọi API này mỗi 2 giây.
    Trả về Top 5 câu hỏi xuất sắc nhất.
    """
    top_5_clean = []
    for c in clusters[:5]:
        top_5_clean.append({
            "score": float(c.get("final_score", 0.0)),
            "count": int(c.get("count", 1)),
            "taxonomy_level": str(c.get("taxonomy_level", "Unclassified")),
            "text": str(c['representative_msg']['text'])
        })
        
    return {
        "time_hien_tai": current_simulated_time.strftime("%H:%M:%S"),
        "top_5": top_5_clean
    }

@app.post("/api/action/remove/{index}")
def mark_as_answered(index: int):
    """
    Khi Giảng viên bấm nút "Đã Trả Lời" -> Frontend gọi API này
    VD: POST /api/action/remove/0 (để xóa câu top 1)
    """
    if 0 <= index < len(clusters):
        removed = clusters.pop(index)
        return {"status": "success", "message": f"Đã xóa: {removed['representative_msg']['text']}"}
    return {"status": "error", "message": "Index không hợp lệ"}

@app.post("/api/action/send-ta/{index}")
def send_to_ta(index: int):
    """
    Khi Giảng viên bấm nút "Gửi Trợ Giảng" -> Frontend gọi API này
    """
    if 0 <= index < len(clusters):
        removed = clusters.pop(index)
        return {"status": "success", "message": f"Đã chuyển TA: {removed['representative_msg']['text']}"}
    return {"status": "error", "message": "Index không hợp lệ"}

if __name__ == "__main__":
    print("🚀 API Server đang chạy. Frontend hãy gọi tới http://localhost:8000/api/top-questions")
    uvicorn.run(app, host="0.0.0.0", port=8000)

