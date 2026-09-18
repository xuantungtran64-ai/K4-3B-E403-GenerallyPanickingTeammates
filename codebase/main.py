import time
import sys
import numpy as np
import Q_tools as Qt
from Q_tools import ChatDataIngestor as CDI
import S_tools as St
from datetime import datetime, timedelta

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
    def __init__(self,data_path,current_simulated_time,LLM_Qfilter =True):
        self.data_path = data_path
        self.current_simulated_time = current_simulated_time
        self.LLM_Qfilter = LLM_Qfilter
        self.clusters = []
        self.data_ingestor = CDI(data_path)
        
        
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
                        Qt.scoring(self.clusters, lecture_vectors = None)

                    except Exception as e:
                        print(f"Lỗi khi xử lý tin nhắn: {e}")

                        continue
                else:
                    print("there is no new message")

                print("\n--- TOP 5 CÂU HỎI ĐẮT GIÁ ---")
                for i, c in enumerate(self.clusters[:5]):
                    print(f"Top {i+1} [{c.get('final_score', 0)}đ]: {c['representative_msg']['text']}")

                current_time += timedelta(seconds=30)
                time.sleep(5) 

        except KeyboardInterrupt:
            sys.exit(0)

#CONFIG
data_path = r'D:\vin\Hackathon_mini\banned\K4-3B-Day05-06-AI-Product-Hackathon-main\data\vlearn-pack\chatlog\tutor_turns.csv'
current_simulated_time = '2026-07-23 15:20:00'
LLM_Qfilter = True

if __name__ == "__main__":
    app = main(data_path,current_simulated_time,LLM_Qfilter)

    app.main()