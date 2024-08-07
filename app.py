from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os
from config import DevelopmentConfig, TestingConfig, ProductionConfig
from models import db, Todo ,Image ,Comment
import logging
from email.mime.text import MIMEText
import smtplib
from dotenv import load_dotenv
from threading import Thread
import schedule
from sendmail import check_due_tasks
import time
from io import BytesIO
from forms import CommentForm
from datetime import datetime, timedelta
from flask_wtf import CSRFProtect

# from celeryF import make_celery
app = Flask(__name__, static_folder='static/my-react-app/build', template_folder='static/my-react-app/build')
load_dotenv()

app.config['SECRET_KEY'] = '9988551100'
csrf = CSRFProtect(app)
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

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), os.path.pardir, 'db.sqlite')}"
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
app.secret_key = 'supersecretkey'

# データベースの初期化
db.init_app(app)
migrate = Migrate(app, db)

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Create tables and any other setup tasks
    with app.app_context():
        db.create_all()

    return app

@app.route('/image/<int:id>')
def get_image(id):
    image = Image.query.get_or_404(id)
    return send_file(BytesIO(image.data), mimetype='image/jpeg')

@app.route('/upload_images/<int:id>', methods=['POST'])
def upload_images(id):
    if 'files' not in request.files:
        return redirect(request.url)
    
    files = request.files.getlist('files')
    if not files:
        return redirect(request.url)
    
    for file in files:
        if file.filename == '':
            continue
        
        image = Image(
            filename=file.filename,
            data=file.read(),  # 画像データを読み込み
            todo_id=id
        )
        db.session.add(image)
    
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/')
def index():
    tasks = Todo.query.order_by(Todo.created_at.desc()).all()
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
    comment_form = CommentForm()
    
    if request.method == 'POST':
        if 'update_task' in request.form:
            # Handle task update
            todo.content = request.form['content']
            todo.description = request.form['description']
            todo.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%dT%H:%M')
            db.session.commit()
            return redirect(url_for('detail', id=id))
        
        elif 'add_comment' in request.form:
            # Handle comment addition
            if comment_form.validate_on_submit():
                new_comment = Comment(content=comment_form.content.data, todo_id=id)
                db.session.add(new_comment)
                db.session.commit()
                return redirect(url_for('detail', id=id))
            return redirect(url_for('detail', id=id))

    # Assuming `created_at` is in UTC
    comments = Comment.query.filter_by(todo_id=id).order_by(Comment.created_at.desc()).all()

    for comment in comments:
        # Adjust to your time zone offset (e.g., UTC+9 for Japan Standard Time)
        offset = timedelta(hours=9)  # Replace with your offset
        comment.created_at_local = (comment.created_at + offset).strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template('detail.html', todo=todo, form=comment_form, comments=comments)

@app.route('/comment/delete/<int:id>', methods=['POST'])
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    todo_id = comment.todo_id
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for('detail', id=todo_id))

@app.route('/comment/edit/<int:id>', methods=['GET', 'POST'])
def edit_comment(id):
    comment = Comment.query.get_or_404(id)
    form = CommentForm(obj=comment)
    
    if form.validate_on_submit():
        comment.content = form.content.data
        db.session.commit()
        return redirect(url_for('detail', id=comment.todo_id))
    
    return render_template('edit_comment.html', form=form, comment=comment)

@app.route('/comment/update/<int:id>', methods=['POST'])
def update_comment(id):
    comment = Comment.query.get_or_404(id)
    data = request.get_json()
    content = data.get('content')

    if content:
        comment.content = content
        db.session.commit()
        return jsonify({'message': 'Comment updated successfully.'}), 200

    return jsonify({'message': 'Invalid data.'}), 400

@app.route('/delete_image/<int:image_id>', methods=['DELETE'])
def delete_image(image_id):
    image = Image.query.get_or_404(image_id)
    db.session.delete(image)
    db.session.commit()
    return '', 204
    
@app.route('/image/<int:image_id>')
def image(image_id):
    img = Image.query.get(image_id)
    if img is None:
        return "Image not found", 404
    return send_file(BytesIO(img.data), mimetype='image/jpeg')

@app.route('/download/<int:image_id>')
def download_image(image_id):
    image = Image.query.get(image_id)
    if image is None:
        return "File not found", 404

    return send_file(BytesIO(image.data),
        download_name=image.filename,
        as_attachment=True)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    tasks = Todo.query.filter(
        (Todo.content.like(f'%{query}%')) | (Todo.description.like(f'%{query}%'))
    ).order_by(Todo.created_at.desc()).all()
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


