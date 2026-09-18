import pandas as pd
from datetime import datetime
import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.stats import norm
#DATA
class ChatDataIngestor:
    def __init__(self, csv_path):
        try:
            self.df = pd.read_csv(csv_path)
            self.df['asked_at_vn'] = pd.to_datetime(self.df['asked_at_vn'], errors='coerce')
            
            self.df = self.df.dropna(subset=['student_question', 'asked_at_vn'])
            
            self.df = self.df.sort_values(by='asked_at_vn')
            
        except Exception as e:
            print(f"lỗi khi đọc file: {e}")
            self.df = pd.DataFrame()

        self.last_fetch_time = None

    def fetch_new_messages(self, current_simulated_time):

        if self.df.empty:
            return []

        current_time = pd.to_datetime(current_simulated_time)

        if self.last_fetch_time is None:
            mask = (self.df['asked_at_vn'] <= current_time)
        else:
            mask = (self.df['asked_at_vn'] > self.last_fetch_time) & (self.df['asked_at_vn'] <= current_time)

        new_data_df = self.df[mask]

        self.last_fetch_time = current_time

        return new_data_df[['turn_id', 'asked_at_vn', 'student_question']].to_dict('records')



#Rule based for question identifier

STATUS_SURE_QUESTION = "SURE_QUESTION"
STATUS_SURE_TRASH = "SURE_TRASH"
STATUS_CANDIDATE = "CANDIDATE"

QUESTION_PATTERN = re.compile(
    r'\b(sao|gì|nào|đâu|ai|bao nhiêu|chưa|hả|nhỉ|tại sao|làm sao|như thế nào|có phải|được không|cho em hỏi)\b', re.IGNORECASE)

CHIT_CHAT_PATTERN = re.compile(
    r'\b(chào|cảm ơn|thank|dạ|vâng|ok|điểm danh|xin link)\b', re.IGNORECASE)

def classify_message_rulebase(message):
    if not isinstance(message, str):
        return STATUS_SURE_TRASH
        
    text = message.strip().lower()
    
    if len(text) < 5:
        return STATUS_SURE_TRASH
        
    if '?' in text:
        return STATUS_SURE_QUESTION
        
    if QUESTION_PATTERN.search(text):
        return STATUS_SURE_QUESTION
        
    if CHIT_CHAT_PATTERN.search(text):
        return STATUS_SURE_TRASH
        
    return STATUS_CANDIDATE



def is_question_rulebase(message):
    if not isinstance(message, str):
        return False
        
    text = message.strip().lower()
    
    if len(text) < 5:
        return False
        
    if '?' in text:
        return True
        
    if QUESTION_PATTERN.search(text):
        return True
        
    if CHIT_CHAT_PATTERN.search(text):
        return False
        

#cluster
def cosine_similarity_matrix(vector, matrix):

    vector_norm = np.linalg.norm(vector)
    matrix_norm = np.linalg.norm(matrix, axis=1)
    
    if vector_norm == 0 or np.any(matrix_norm == 0):
        return np.zeros(len(matrix))
        
    return np.dot(matrix, vector) / (matrix_norm * vector_norm)


def vector_cluster(clusters, new_vector, new_question_text, turn_id, threshold=0.85):

    new_vector = np.array(new_vector)
    norm = np.linalg.norm(new_vector)
    if norm > 0:
        new_vector = new_vector / norm

    if not clusters:
        new_cluster = {
            'vectors': [new_vector],
            'center_vector': new_vector, 
            'count': 1, 
            'messages': [{"turn_id": turn_id, "text": new_question_text}],
            'representative_msg': {"turn_id": turn_id, "text": new_question_text} # Câu đại diện
        }
        clusters.append(new_cluster)
        return clusters
    
    center_vectors = np.array([c["center_vector"] for c in clusters])
    
    similarities = cosine_similarity_matrix(new_vector, center_vectors)
    
    best_match_idx = np.argmax(similarities)
    best_score = similarities[best_match_idx]
    
    if best_score >= threshold:
        target_cluster = clusters[best_match_idx]
        
        target_cluster["vectors"].append(new_vector)
        target_cluster["messages"].append({"turn_id": turn_id, "text": new_question_text})
        
        old_count = target_cluster["count"]
        target_cluster["count"] = old_count + 1
        
        old_center = target_cluster["center_vector"]
        new_center = ((old_count * old_center) + new_vector) / target_cluster["count"]
        target_cluster["center_vector"] = new_center / np.linalg.norm(new_center)
        
        all_vectors_in_cluster = np.array(target_cluster["vectors"])
        sims_to_new_center = cosine_similarity_matrix(target_cluster["center_vector"], all_vectors_in_cluster)
        
        rep_idx = np.argmax(sims_to_new_center)
        target_cluster["representative_msg"] = target_cluster["messages"][rep_idx]
        
    else:
        new_cluster = {
            'vectors': [new_vector],
            'center_vector': new_vector, 
            'count': 1, 
            'messages': [{"turn_id": turn_id, "text": new_question_text}],
            'representative_msg': {"turn_id": turn_id, "text": new_question_text}
        }
        clusters.append(new_cluster)

    return clusters



#similarity score
def lecture_similarity(lecture_vectors, cluster):

    if lecture_vectors is None or len(lecture_vectors) == 0:
        return 0.0
    
    cluster_vector = cluster.get('center_vector')

    if cluster_vector is None:
        return 0.0

    cluster_vector = np.array(cluster_vector)
    lecture_matrix = np.array(lecture_vectors)
    
    similarities = cosine_similarity_matrix(cluster_vector, lecture_matrix)

    max_sim = float(np.max(similarities))
    
    return max(0.0, min(1.0, max_sim))


#scoring

def scoring(clusters, lecture_vectors=None):
    taxonomy_mapping = {
        "ADMIN": 1,
        "RECALL": 3,
        "COMPREHEND": 5,
        "APPLY": 7,
        "CRITICAL": 9,
        "Unclassified": 1 
    }
    
    llm_scores = []
    log_counts = []
    
    for c in clusters:
        tax_level = c.get('taxonomy_level', 'Unclassified')
        base_score = taxonomy_mapping.get(tax_level, 1)
        
        if base_score >= 3:
            sim_score = lecture_similarity(lecture_vectors, c)
            c['raw_llm_score'] = base_score + sim_score
            c['log_count'] = np.log1p(c.get('count', 1))
            c['status'] = 'academic'
            
            llm_scores.append(c['raw_llm_score'])
            log_counts.append(c['log_count'])
        else:
            c['final_score'] = 0
            c['status'] = 'trash'
            
    if llm_scores: 
        llm_arr = np.array(llm_scores)
        count_arr = np.array(log_counts)
        
        mean_llm, std_llm = np.mean(llm_arr), np.std(llm_arr)
        mean_count, std_count = np.mean(count_arr), np.std(count_arr)
        
        std_llm = std_llm if std_llm > 0 else 1.0
        std_count = std_count if std_count > 0 else 1.0
        
        for c in clusters:
            if c.get('status') == 'academic':
                z_llm = (c['raw_llm_score'] - mean_llm) / std_llm
                z_count = (c['log_count'] - mean_count) / std_count
                
                z_hybrid = (0.75 * z_llm) + (0.25 * z_count)
                
                mapped_score = 3.0 + (7.0 * norm.cdf(z_hybrid))
                c['final_score'] = round(mapped_score, 2)
                
    clusters.sort(key=lambda x: x.get('final_score', 0), reverse=True)
    