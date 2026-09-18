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

@app.get("/api/questions")
def get_questions():
    """
    Frontend dùng Javascript gọi API này để lấy toàn bộ danh sách câu hỏi.
    """
    results = []
    # Đảm bảo list clusters được sắp xếp theo final_score giảm dần
    sorted_clusters = sorted(clusters, key=lambda x: x.get('final_score', 0), reverse=True)
    
    for i, c in enumerate(sorted_clusters):
        # Khởi tạo ID duy nhất cho frontend nếu chưa có
        if "id" not in c:
            c["id"] = f"c_{c['representative_msg']['turn_id']}_{i}"
        
        # Trạng thái hiển thị trên UI: active, resolved, hidden
        if "ui_status" not in c:
            c["ui_status"] = "active"

        # Ánh xạ phân loại của backend (academic/trash) sang frontend (academic/admin)
        q_type = "academic" if c.get("status") == "academic" else "admin"

        total_score = float(c.get("final_score", 0.0))
        llm_score = float(c.get("raw_llm_score", 0.0))
        raw_msgs = [msg['text'] for msg in c.get("messages", [])]
        tax = c.get("taxonomy_level", "Unclassified")

        results.append({
            "id": c["id"],
            "main_question": str(c['representative_msg']['text']),
            "count": int(c.get("count", 1)),
            "llm_score": round(llm_score, 1),
            "total_score": round(total_score, 1),
            "reason": f"Phân loại AI: {tax}",
            "type": q_type,
            "status": c["ui_status"],
            "raw_messages": raw_msgs,
            "taxonomy_level": tax
        })
        
    return {
        "time_hien_tai": current_simulated_time.strftime("%H:%M:%S"),
        "clusters": results
    }

@app.post("/api/action/{action_type}/{cluster_id}")
def handle_action(action_type: str, cluster_id: str):
    """
    Xử lý các hành động từ Giảng viên: resolve (đã trả lời), trash (ẩn rác), send-ta (gửi TA).
    """
    for c in clusters:
        if c.get("id") == cluster_id:
            if action_type == "resolve":
                c["ui_status"] = "resolved"
            elif action_type == "trash" or action_type == "hide":
                c["ui_status"] = "hidden"
            elif action_type == "send-ta":
                c["ui_status"] = "resolved" # Đã gửi TA thì coi như xử lý xong trên màn hình GV
            return {"status": "success", "message": f"Thực hiện thành công {action_type}."}
    return {"status": "error", "message": "Không tìm thấy câu hỏi này."}

if __name__ == "__main__":
    print("🚀 API Server đang chạy. Dashboard UI hãy gọi tới http://localhost:8000/api/questions")
    uvicorn.run(app, host="0.0.0.0", port=8000)


