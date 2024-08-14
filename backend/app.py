from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, send_from_directory
from flask_migrate import Migrate
from datetime import datetime, timedelta
import os
from config import DevelopmentConfig, TestingConfig, ProductionConfig
from models import db, Todo, Image, Comment
import logging
from dotenv import load_dotenv
from io import BytesIO
from forms import CommentForm
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_cors import CORS

# app = Flask(__name__, static_folder='frontend/my-react-app/build', template_folder='frontend/my-react-app/build')
app = Flask(__name__, static_folder='frontend/my-react-app/build', template_folder='frontend/my-react-app/build')
CORS(app, supports_credentials=True)
load_dotenv()

app.config['SECRET_KEY'] = '9988551100'
csrf = CSRFProtect(app)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

env = os.environ.get('FLASK_ENV', 'development')

if env == 'development':
    app.config.from_object(DevelopmentConfig)
elif env == 'testing':
    app.config.from_object(TestingConfig)
else:
    app.config.from_object(ProductionConfig)

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), os.path.pardir, 'db.sqlite')}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
app.secret_key = 'supersecretkey'

db.init_app(app)
migrate = Migrate(app, db)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react_app(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/image/<int:id>')
def get_image(id):
    image = Image.query.get_or_404(id)
    return send_file(BytesIO(image.data), mimetype='image/jpeg')


@app.route('/upload_images/<int:id>', methods=['POST'])
@csrf.exempt
def upload_images(id):
    if 'files' not in request.files:
        return jsonify({"error": "No files part"}), 400
    
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "No files selected"}), 400
    
    try:
        for file in files:
            if file.filename == '':
                continue
            
            image = Image(
                filename=file.filename,
                data=file.read(),
                todo_id=id
            )
            db.session.add(image)
        
        db.session.commit()
        return jsonify({"message": "Files uploaded successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/tasks/<int:id>', methods=['GET'])
def get_task(id):
    todo = Todo.query.get_or_404(id)
    comments = Comment.query.filter_by(todo_id=id).order_by(Comment.created_at.desc()).all()
    
    offset = timedelta(hours=9)
    comments_data = [
        {
            'id': comment.id,
            'content': comment.content,
            'created_at': (comment.created_at + offset).strftime('%Y-%m-%d %H:%M:%S')
        }
        for comment in comments
    ]
    
    images_data = [
        {
            'id': image.id,
            'filename': image.filename,
            'url': url_for('get_image', id=image.id)
        }
        for image in todo.images
    ]

    return jsonify({
        'id': todo.id,
        'content': todo.content,
        'description': todo.description,
        'created_at': todo.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'due_date': todo.due_date.strftime('%Y-%m-%dT%H:%M:%S'),
        'comments': comments_data,
        'images': images_data
    })

@app.route('/search', methods=['GET'])
def search_tasks():
    query = request.args.get('query', '')
    
    if not query:
        return jsonify([])  # クエリがない場合は空のリストを返す
    
    # データベースからクエリに一致するタスクを検索し、created_atでソート
    tasks = Todo.query.filter(Todo.content.ilike(f'%{query}%')).order_by(Todo.created_at.desc()).all()
    
    # タスクを辞書形式で返す
    result = [task.to_dict() for task in tasks]
    
    return jsonify(result)
    
@app.route('/api/tasks/<int:id>', methods=['POST'])
@csrf.exempt
def update_task(id):
    todo = Todo.query.get_or_404(id)
    data = request.json
    todo.content = data['content']
    todo.description = data['description']
    todo.due_date = datetime.strptime(data['due_date'], '%Y-%m-%dT%H:%M')
    db.session.commit()
    return jsonify({'message': 'Task updated successfully'}), 200

@app.route('/api/tasks/<int:id>/comments', methods=['POST'])
@csrf.exempt
def add_comment(id):
    data = request.json
    new_comment = Comment(content=data['content'], todo_id=id)
    db.session.add(new_comment)
    db.session.commit()
    return jsonify({'message': 'Comment added successfully'}), 200

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    try:
        tasks = Todo.query.order_by(Todo.created_at.desc()).all()
        task_list = [task.to_dict() for task in tasks]
        logging.debug(task_list)  # デバッグ用のログ
        return jsonify(task_list)
        print(task_list)
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({'error': 'An error occurred'}), 500

# @app.errorhandler(404)
# def not_found_error(error):
#     return render_template('404.html'), 404

@app.route('/add', methods=['POST'])
@csrf.exempt
def add():
    if request.method == 'POST':
        data = request.get_json()
        content = data.get('content')
        description = data.get('description')
        due_date_str = data.get('dueDate')

        try:
            due_date = datetime.fromisoformat(due_date_str)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid date format"}), 400

        new_task = Todo(
            content=content,
            description=description,
            due_date=due_date
        )
        db.session.add(new_task)
        db.session.commit()
        return jsonify({"message": "Task created"}), 201
    
@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@csrf.exempt
def delete_task(task_id):
    task = Todo.query.get_or_404(task_id)
    
    for image in task.images:
        db.session.delete(image)
    for comment in task.comments:
        db.session.delete(comment)

    db.session.delete(task)
    db.session.commit()
    
    return '', 204

@app.route('/get-csrf-token', methods=['GET'])
def get_csrf_token():
    token = generate_csrf()
    logging.debug(f"CSRF Token: {token}")
    return jsonify({'csrf_token': token})

@app.route('/api/images/<int:id>', methods=['DELETE'])
@csrf.exempt
def delete_image(id):
    image = Image.query.get(id)
    if image:
        db.session.delete(image)
        db.session.commit()
        return jsonify({'message': 'Image deleted successfully'}), 200
    else:
        return jsonify({'error': 'Image not found'}), 404
    
@app.route('/api/comments/<int:comment_id>', methods=['PUT', 'DELETE'])
@csrf.exempt
def modify_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if request.method == 'PUT':
        data = request.json
        comment.content = data['content']
        db.session.commit()
        return jsonify({'message': 'Comment updated successfully'}), 200

    elif request.method == 'DELETE':
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'message': 'Comment deleted successfully'}), 200

@app.route('/detail/<int:id>', methods=['GET', 'POST'])
def detail(id):
    todo = Todo.query.get_or_404(id)
    comment_form = CommentForm()
    
    if request.method == 'POST':
        if 'update_task' in request.form:
            todo.content = request.form['content']
            todo.description = request.form['description']
            todo.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%dT%H:%M')
            db.session.commit()
            return redirect(url_for('detail', id=id))
        
        elif 'add_comment' in request.form:
            if comment_form.validate_on_submit():
                new_comment = Comment(content=comment_form.content.data, todo_id=id)
                db.session.add(new_comment)
                db.session.commit()
                return redirect(url_for('detail', id=id))
            return redirect(url_for('detail', id=id))

    comments = Comment.query.filter_by(todo_id=id).order_by(Comment.created_at.desc()).all()

    for comment in comments:
        offset = timedelta(hours=9)
        comment.created_at_local = (comment.created_at + offset).strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template('detail.html', todo=todo, form=comment_form, comments=comments)

@app.route('/comment/delete/<int:id>', methods=['POST'])
@csrf.exempt
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    return redirect(request.referrer or url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

