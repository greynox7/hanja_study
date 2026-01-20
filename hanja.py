from flask import Flask, render_template, request, redirect, url_for, jsonify
import random
import sqlite3
import datetime
import os
from hanja_data import HANJA_DATA

app = Flask(__name__)

# 시크릿 키 설정 (가볍게 고정값 사용)
app.secret_key = 'hanja-study-secret'

# 데이터 디렉토리 설정 (절대 경로 사용으로 안전하게)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

DB_FILE = os.path.join(DATA_DIR, 'hanja_study.db')

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # history 테이블 생성
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, 
                  level TEXT, 
                  api_score INTEGER,
                  correct_count INTEGER,
                  total_count INTEGER)''')
    conn.commit()
    conn.close()

# 앱 시작 시 DB 초기화
init_db()

@app.route('/')
def home():
    # 데이터에 있는 급수 목록 가져오기
    levels = list(HANJA_DATA.keys())
    return render_template('index.html', levels=levels)

@app.route('/history')
def history():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM history ORDER BY id DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    
    formatted_history = []
    for row in rows:
        formatted_history.append({
            "date": row['date'],
            "level": row['level'],
            "score": row['api_score'],
            "correct": row['correct_count'],
            "total": row['total_count']
        })
    return render_template('history.html', history=formatted_history)

@app.route('/save_score', methods=['POST'])
def save_score():
    data = request.json
    level = data.get('level')
    score = data.get('score')
    correct = data.get('correct')
    total = data.get('total')
    
    # 한국 시간 대략적으로 맞추기 (서버 설정에 따라 다를 수 있음)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO history (date, level, api_score, correct_count, total_count) VALUES (?, ?, ?, ?, ?)",
              (now, level, score, correct, total))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success"})

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
