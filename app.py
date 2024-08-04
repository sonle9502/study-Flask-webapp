from flask import Flask, render_template, request, redirect, url_for, send_from_directory   
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os
from config import DevelopmentConfig, TestingConfig, ProductionConfig
from models import db, Todo ,Image # Import from models
import logging
from email.mime.text import MIMEText
import smtplib
from dotenv import load_dotenv
from threading import Thread
import schedule
from sendmail import check_due_tasks
import time

# from celeryF import make_celery


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

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
app.secret_key = 'supersecretkey'

# Ensure the uploads directory exists at startup
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# データベースの初期化
db.init_app(app)
migrate = Migrate(app, db)

@app.route('/image/<int:id>')
def get_image(id):
    # Query for the image by its ID
    image = Image.query.get_or_404(id)
    # Get the filename from the Image object
    filename = image.filename
    # Return the image file from the upload directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload_images/<int:id>', methods=['POST'])
def upload_images(id):
    app.logger.debug(f"Request method: {request.method}")
    todo = Todo.query.get_or_404(id)
    if 'files' not in request.files:
        app.logger.error('No files part')
        return redirect(request.url)

    files = request.files.getlist('files')
    if not files:
        app.logger.error('No files uploaded')
        return redirect(request.url)

    for file in files:
        if file and file.filename != '':
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Ensure the directory exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            file.save(file_path)
            new_image = Image(filename=filename, todo_id=todo.id)
            db.session.add(new_image)
            app.logger.info(f'File {filename} uploaded successfully')

    db.session.commit()
    return redirect(url_for('index', id=todo.id))


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
        todo.content = request.form['content']
        todo.description = request.form['description']
        due_date = request.form['due_date']
        if due_date:
            todo.due_date = datetime.strptime(due_date, '%Y-%m-%dT%H:%M')
        else:
            todo.due_date = None
        
        
        
        db.session.commit()
        return redirect(url_for('detail', id=todo.id))

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

@app.route('/sendmail', methods=['GET'])
def send_email():
    try:
        msg = MIMEText('This is a test email')
        msg['Subject'] = 'Test Email'
        msg['From'] = os.getenv('MAIL_USERNAME')
        msg['To'] = os.getenv('MAIL_USERNAME')

        with smtplib.SMTP(os.getenv('MAIL_SERVER'), int(os.getenv('MAIL_PORT'))) as server:
            if os.getenv('MAIL_USE_TLS') == 'True':
                server.starttls()
            server.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
            server.send_message(msg)
        print("Test email sent successfully")
    except Exception as e:
        print(f"Failed to send test email: {e}")
    return redirect(url_for('index'))

schedule.clear()  # 既存のスケジュールをクリア
# schedule.every().minute.at(":01").do(check_due_tasks, app=app)
# schedule.every().second.do(check_due_tasks, app=app)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(5)

if __name__ == "__main__":
    with app.app_context():
        logging.debug("This is an info log message")
        db.create_all()  # Ensure all tables are created
        # Thread(target=run_scheduler).start()
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)


