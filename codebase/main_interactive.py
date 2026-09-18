import time
import sys
import numpy as np
import Q_tools as Qt
from Q_tools import ChatDataIngestor as CDI
import S_tools as St
from datetime import datetime, timedelta
import os

def Q_filter(messages, LLM_filter=True, candidate_Bsize=10):
    valid_questions = [] 
    if LLM_filter:
        candidate_queue = []
        for msg in messages:
            status = Qt.classify_message_rulebase(msg['student_question'])
            
            if status == Qt.STATUS_SURE_QUESTION:
                valid_questions.append(msg)
                
            elif status == Qt.STATUS_CANDIDATE:
                candidate_queue.append(msg)
                
                if len(candidate_queue) >= candidate_Bsize:            
                    llm_verified_questions = St.LLM_Qfilter(candidate_queue)
                    valid_questions.extend(llm_verified_questions)
                    candidate_queue.clear()
                    
        if len(candidate_queue) > 0:
            llm_verified_questions = St.LLM_Qfilter(candidate_queue)
            valid_questions.extend(llm_verified_questions)
            candidate_queue.clear()
            
    else:
        for msg in messages:
            if Qt.is_question_rulebase(msg['student_question']):
                valid_questions.append(msg)
                
    return valid_questions



def Q_cluster(clusters, embedded_Q, threshold=0.85):
    for item in embedded_Q:
        question = item["student_question"]
        turn_id = item["turn_id"]
        vector = item['embedding']
        clusters = Qt.vector_cluster(clusters, vector, question, turn_id, threshold)
        """ output format
            'vectors': [vectors],
            'center_vector': new_vector, 
            'count': 1, 
            'messages': [{"turn_id": turn_id, "text": new_question_text}],
            'representative_msg': {"turn_id": turn_id, "text": new_question_text}
            """
        
def LLM_cluster(clusters):
    for c in clusters:
        if "taxonomy_level" not in c:
            taxonomy_level = St.get_taxonomy_level(c['representative_msg']['text'])
            c['taxonomy_level'] = taxonomy_level

                



                


class main:
    def __init__(self,data_path,current_simulated_time,LLM_Qfilter =True, pdf_path = None):
        self.data_path = data_path
        self.current_simulated_time = current_simulated_time
        self.LLM_Qfilter = LLM_Qfilter
        self.clusters = []
        self.data_ingestor = CDI(data_path)
        
        # 1. Trích xuất text từ PDF
        lecture_text = St.PDF_EXTRACT(pdf_path) if pdf_path else ""
        # 2. Sinh embedding vector từ text
        self.lecture_vectors = St.material_embedding(lecture_text) if lecture_text else []
        
        
    def main(self):

        print('program started')
        current_time = datetime.strptime(self.current_simulated_time, "%Y-%m-%d %H:%M:%S")
        try:
            while True:
                print(f"đang quét tin nhắn lúc: {current_time}")
                new_msg = self.data_ingestor.fetch_new_messages(current_time.strftime("%Y-%m-%d %H:%M:%S"))
                if new_msg:
                    try: 
                        print(f"lọc câu hỏi")
                        valid_questions = Q_filter(new_msg, LLM_filter=True)
                        embedded_Q = St.sentence_embedding(valid_questions)
                        print(f"phân cụm")
                        Q_cluster(self.clusters, embedded_Q, threshold=0.85)
                        LLM_cluster(self.clusters)
                        print(f"chấm điểm")
                        Qt.scoring(self.clusters, lecture_vectors = self.lecture_vectors)

                    except Exception as e:
                        print(f"Lỗi khi xử lý tin nhắn: {e}")

                        continue
                else:
                    print("there is no new message")

                print("\n" + "="*50)
                print("🌟 TOP CÂU HỎI ĐẮT GIÁ HIỆN TẠI 🌟")
                print("="*50)
                for i, c in enumerate(self.clusters[:5]):
                    print(f"[{i+1}] ({c.get('final_score', 0)}đ | {c.get('count', 1)} người hỏi | {c.get('taxonomy_level', 'Unclassified')})")
                    print(f"    -> {c['representative_msg']['text']}\n")

                print("-" * 50)
                print("Hành động:")
                print(" - Gõ [1, 2, 3...] để đánh dấu ĐÃ TRẢ LỜI (xóa khỏi danh sách).")
                print(" - Gõ [t1, t2, t3...] để GỬI CHO TRỢ GIẢNG (TA) hỗ trợ.")
                print(" - Bấm phím [Enter] để lướt qua (quét tiếp 30s tin nhắn mới).")
                
                user_input = input("\nLựa chọn của bạn: ").strip().lower()
                
                if user_input:
                    try:
                        if user_input.startswith('t'):
                            idx = int(user_input[1:]) - 1
                            if 0 <= idx < len(self.clusters):
                                msg = self.clusters[idx]['representative_msg']['text']
                                print(f"\n[!] ĐÃ GỬI CHO TA: '{msg}'")
                                self.clusters.pop(idx)
                            else:
                                print("Số không hợp lệ!")
                        else:
                            idx = int(user_input) - 1
                            if 0 <= idx < len(self.clusters):
                                msg = self.clusters[idx]['representative_msg']['text']
                                print(f"\n[v] ĐÃ TRẢ LỜI: '{msg}'")
                                self.clusters.pop(idx)
                            else:
                                print("Số không hợp lệ!")
                    except ValueError:
                        print("Cú pháp không hợp lệ. Vui lòng nhập số (vd: 1) hoặc t+số (vd: t2).")

                current_time += timedelta(seconds=30)
                # Bỏ time.sleep(5) vì input() đã đóng vai trò chờ (blocking) rồi

        except KeyboardInterrupt:
            sys.exit(0)

#CONFIG
data_path = os.path.join(os.path.dirname(__file__), '..', 'mock_tutor_turns.csv')
current_simulated_time = '2026-07-23 15:20:00'
LLM_Qfilter = True
pdf_path = r'D:\vin\Hackathon_mini\banned\K4-3B-Day05-06-AI-Product-Hackathon-main\data\vlearn-pack\slides\d1-slide-hackathon.pdf'

if __name__ == "__main__":
    app = main(data_path,current_simulated_time,LLM_Qfilter,pdf_path)

    app.main()