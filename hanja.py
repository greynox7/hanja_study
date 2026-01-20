from flask import Flask, render_template, request, redirect, url_for
import random
from hanja_data import HANJA_DATA

app = Flask(__name__)

# 시크릿 키 설정 (가볍게 고정값 사용)
app.secret_key = 'hanja-study-secret'

@app.route('/')
def home():
    # 데이터에 있는 급수 목록 가져오기
    levels = list(HANJA_DATA.keys())
    return render_template('index.html', levels=levels)

@app.route('/quiz/<level>')
def quiz(level):
    if level not in HANJA_DATA:
        return redirect(url_for('home'))

    # 해당 급수의 전체 한자 리스트 가져오기
    all_hanjas = HANJA_DATA[level]
    
    # 문제 출제 (랜덤 30문제, 데이터가 적으면 있는 만큼)
    num_questions = min(len(all_hanjas), 30)
    questions_raw = random.sample(all_hanjas, num_questions)
    
    quiz_data = []
    
    for q in questions_raw:
        # 정답
        correct_answer = q['mean']
        
        # 오답 보기 만들기 (모든 급수의 한자 뜻 중에서 랜덤으로 3개 추출)
        # 현재 급수에서만 뽑으면 보기가 너무 뻔할 수 있으니 전체 데이터 활용 고려 가능하나,
        # 일단 간단하게 현재 급수 내 다른 한자들로 구성
        other_options = [h['mean'] for h in all_hanjas if h['mean'] != correct_answer]
        
        # 오답 보기가 부족할 경우 (데이터가 너무 적을 때)
        if len(other_options) < 3:
            wrong_answers = other_options
        else:
            wrong_answers = random.sample(other_options, 3)
        
        # 보기 합치고 섞기
        options = wrong_answers + [correct_answer]
        random.shuffle(options)
        
        quiz_data.append({
            "hanja": q['hanja'],
            "options": options,
            "answer": correct_answer
        })
        
    return render_template('quiz.html', level=level, quiz_data=quiz_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
