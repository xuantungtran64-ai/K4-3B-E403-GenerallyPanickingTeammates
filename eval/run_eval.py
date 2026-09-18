import sys
import os
import pandas as pd
import time

# Add codebase to path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'codebase')))
import S_tools as St

def run_evaluation():
    csv_path = os.path.join(os.path.dirname(__file__), 'golden_set.csv')
    df = pd.read_csv(csv_path)
    
    results = []
    correct_count = 0
    total = len(df)
    
    print(f"Bắt đầu chấm điểm {total} cases...")
    
    for idx, row in df.iterrows():
        question = row['student_question']
        expected = row['expected_taxonomy']
        
        # Chạy qua LLM của chúng ta
        predicted = St.get_taxonomy_level(question)
        
        is_correct = (predicted == expected)
        if is_correct:
            correct_count += 1
            
        results.append({
            'case_id': row['case_id'],
            'question': question,
            'expected': expected,
            'predicted': predicted,
            'is_correct': is_correct,
            'difficulty_class': row['difficulty_class'],
            'dimension': row['input_grid_dimension']
        })
        time.sleep(0.5) # Tránh bị Groq API rate limit
        
    acc = correct_count / total * 100
    
    # Xuất báo cáo ra Markdown
    report_path = os.path.join(os.path.dirname(__file__), 'evaluation_results.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Báo Cáo Đánh Giá Chất Lượng Phân Loại AI (Evaluation Report)\n\n")
        f.write(f"- **Tổng số test cases (Golden Set):** {total}\n")
        f.write(f"- **Số case AI phân loại đúng:** {correct_count}\n")
        f.write(f"- **Độ chính xác (Accuracy):** {acc:.2f}%\n\n")
        
        f.write("## 1. Phân Tích Lỗi (Error Analysis)\n\n")
        f.write("Dưới đây là các case AI nhận diện sai. Cần điền phân loại lỗi theo 3 mức: (1) Dùng được, (2) Sửa được, (3) Không chấp nhận được.\n\n")
        
        for r in results:
            if not r['is_correct']:
                f.write(f"### Case {r['case_id']} - Lớp: {r['difficulty_class']}\n")
                f.write(f"- **Chiều dữ liệu:** {r['dimension']}\n")
                f.write(f"- **Câu hỏi:** {r['question']}\n")
                f.write(f"- **Kỳ vọng (Expected):** `{r['expected']}`\n")
                f.write(f"- **AI Trả về (Predicted):** `{r['predicted']}`\n")
                f.write("- **Phân loại lỗi:** [ ] Dùng được | [ ] Sửa được | [ ] Không chấp nhận được\n")
                f.write("- **Nguyên nhân (Tên lỗi):** ... (VD: Lạc trình độ, Đoán mò, Bịa nguồn)\n\n")

        f.write("## 2. Chi Tiết Các Case Đạt (Success Cases)\n\n")
        for r in results:
            if r['is_correct']:
                f.write(f"- **Case {r['case_id']}**: `{r['expected']}` - {r['question']}\n")

    print(f"\nĐã chấm xong! Accuracy: {acc:.2f}%")
    print(f"Báo cáo chi tiết đã được lưu tại: {report_path}")

if __name__ == '__main__':
    run_evaluation()
