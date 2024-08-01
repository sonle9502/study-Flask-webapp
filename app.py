from flask import Flask, render_template, request, redirect, url_for ,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os
from config import DevelopmentConfig, TestingConfig, ProductionConfig
from sendmail import start_scheduler 
from models import db, Todo  # Import from models
from threading import Thread
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# Cấu hình logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 環境変数から現在の環境を取得
env = os.environ.get('FLASK_ENV', 'development')

# 環境に応じた設定を適用
if env == 'development':
    app.config.from_object(DevelopmentConfig)
elif env == 'testing':
    app.config.from_object(TestingConfig)
else:
    app.config.from_object(ProductionConfig)

# データベースの初期化
db.init_app(app)
migrate = Migrate(app, db)

@app.route('/')
def index():
    tasks = Todo.query.all()
    return render_template('index.html', todos=tasks)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        # フォームからデータを取得
        content = request.form['content']
        description = request.form['description']
        due_date = request.form['due_date']
        # due_date_str を datetime オブジェクトに変換
        try:
            due_date = datetime.fromisoformat(due_date)
        except ValueError:
            # 変換に失敗した場合のエラーハンドリング
            return "Invalid date format", 400
        # Todoオブジェクトを作成
        new_task = Todo(
            content=content,
            description=description,
            due_date=due_date
        )
        # データベースに追加
        db.session.add(new_task)
        db.session.commit()
        # インデックスページにリダイレクト
        return redirect(url_for('index'))
    else:
        return render_template('add.html')

@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)
    db.session.delete(task_to_delete)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/detail/<int:id>', methods=['GET', 'POST'])
def detail(id):
    todo = Todo.query.get_or_404(id)
    if request.method == 'POST':
        # フォームからデータを取得し、タスクを更新する処理
        todo.content =  request.form['content']
        todo.description = request.form['description']
        todo.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%dT%H:%M') if request.form['due_date'] else None
        todo.email_sent = False
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('detail.html', todo=todo)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    tasks = Todo.query.filter(
        (Todo.content.like(f'%{query}%')) | (Todo.description.like(f'%{query}%'))
    ).all()
    return render_template('index.html', todos=tasks)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# @app.route('/sendmail', methods=['GET'])
# def send_email():
#     try:
#         msg = MIMEText('This is a test email')
#         msg['Subject'] = 'Test Email'
#         msg['From'] = os.getenv('MAIL_USERNAME')
#         msg['To'] = os.getenv('MAIL_USERNAME')
        
#         with smtplib.SMTP(os.getenv('MAIL_SERVER'), int(os.getenv('MAIL_PORT'))) as server:
#             if os.getenv('MAIL_USE_TLS') == 'True':
#                 server.starttls()
#             server.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
#             server.send_message(msg)
#         print("Test email sent successfully")
#     except Exception as e:
#         print(f"Failed to send test email: {e}")
#     return redirect(url_for('index'))

if __name__ == "__main__":
    with app.app_context():
        logging.debug("This is an info log message")
        db.create_all()  # Ensure all tables are created
        # スケジューラを独立したスレッドで開始
        scheduler_thread = Thread(target=start_scheduler, args=(app,))
        scheduler_thread.start()
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True) 


