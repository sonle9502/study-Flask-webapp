from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, send_from_directory
from flask_migrate import Migrate
from datetime import datetime, timezone, timedelta
import os
from config import DevelopmentConfig, TestingConfig, ProductionConfig
from models.flaskmodel import SQLAlchemy_db, Todo, Image, Comment
from models.mysql import MysqlClass
import changeImage
from PIL import Image as IM
import logging
from dotenv import load_dotenv
from io import BytesIO
from forms import CommentForm
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_cors import CORS
import openai
# import tensorflow as tf
# import torch
import librosa
import cv2
import numpy as np
import base64
import io
from werkzeug.utils import secure_filename
import pymysql
import pytz

app = Flask(__name__, static_folder='frontend/my-react-app/build', template_folder='frontend/my-react-app/build')

flask_sqlalchemy = 0
mySql = 1
# MySQLflask_sqlalchemyのURIを設定
if flask_sqlalchemy:
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'data', 'db.sqlite')}"
    db = SQLAlchemy_db
    db.init_app(app)
    migrate = Migrate(app, db)

# MySQLデータベースのURIを設定
if mySql:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://FlaskDB:Future0308@localhost:3306/tododb'
    db = MysqlClass.mysql_db
    db.init_app(app)
    migrate = Migrate(app, db)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'

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

# モデルのロード
# try:
#     model = tf.keras.models.load_model('/app/modelsAI/editmodel.h5')
#     print("Model loaded successfully!")
# except Exception as e:
    # print(f"Error loading model: {e}")

#画像認識
@app.route('/predict-image', methods=['POST'])
@csrf.exempt
def predict_image():
    try:
        logging.info("Starting image processing...")
        datafile = request.json.get('file')
        index_value = request.json.get('index')
        if not datafile:
            raise ValueError("No data received")
        
        logging.info(f"Received image data length: {datafile}")
        logging.info(f"Received image data length: {index_value}")

        # デバッグ用ログ
        logging.info("Calling changeImage()")
        image_array = changeImage.changeImage(datafile)
        changeImage.saveimage(image_array)
        print(f"changeImage() returned shape: {np.array(image_array).shape}")

        if index_value == 'number':
            # 画像データをモデルに入力して予測を行う
            predictions = model.predict(image_array)
            # すべてのクラスの予測確率を含めて返す
            prediction_probabilities = predictions[0].tolist()
        elif index_value == 'kanji':
            # 画像データをモデルに入力して予測を行う
            # predictions = model.predict(image_array)
            # すべてのクラスの予測確率を含めて返す
            prediction_probabilities = [1, 2, 3]
            logging.info(f"Received image data length: {prediction_probabilities}")

        return jsonify({'predictions': prediction_probabilities}), 200

    except Exception as e:
        logging.error(f"Error processing image: {e}")
        return jsonify({'error': 'Failed to process image'}), 500
    
#音声処理
@app.route('/predict-audio', methods=['POST'])
@csrf.exempt
def predict_audio():
    file = request.files['audio']
    audio, sr = librosa.load(file, sr=None)
    # モデルの推論コードをここに記述
    prediction = "dummy_result"  # モデルの予測結果
    return jsonify({'prediction': prediction})

#staticpath
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react_app(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

#getimage
@app.route('/image/<int:id>')
def get_image(id):
    if mySql:
        try:
            # MySQLから画像データを取得
            result = MysqlClass.get_image(id)
            
            if isinstance(result, dict) and 'filename' in result and 'data' in result:
                filename = result['filename']
                image_data = result['data']

                # データをbase64にエンコード
                encoded_image = base64.b64encode(image_data).decode('utf-8')
                
                # JSON形式で返す
                return jsonify({
                    'filename': filename,
                    'image': encoded_image
                })
            else:
                return jsonify({'error': 'Image not found or invalid data format'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        try:
            image = Image.query.get_or_404(id)
            return send_file(BytesIO(image.data), mimetype='image/jpeg')
        except Exception as e:
            return jsonify({'error': str(e)}), 500

#generate-description by openAI
@app.route('/api/generate-description', methods=['POST'])
@csrf.exempt
def generate_description():
    try:
        data = request.json
        query = data.get('query')

        # 新しいOpenAI APIの呼び出し
        response = openai.Completion.create(
            model="text-davinci-003",  # または他のモデル
            prompt=query,
            max_tokens=150
        )

        # レスポンスから説明文を取得
        description = response['choices'][0]['text'].strip()
        return jsonify({"description": description}), 200
    except Exception as e:
        app.logger.error("Error generating description: %s", str(e))
        return jsonify({"error": str(e)}), 500

#uploadimage
@app.route('/upload_images/<int:id>', methods=['POST'])
@csrf.exempt
def upload_images(id):
    if mySql:
        if 'files' not in request.files:
            return jsonify({"error": "No files part"}), 400
        
        files = request.files.getlist('files')
        if not files:
            return jsonify({"error": "No files selected"}), 400
        
        try:
            for file in files:
                if file.filename == '':
                    continue
                
                filename_tuple=file.filename,
                filename = filename_tuple[0]
                image_data=file.read(),
                todo_id=id
                result = MysqlClass.upload_image(filename, todo_id, image_data)
            if result:
                return jsonify({'message': 'Image uploaded successfully', 'id': result}), 200
            else:
                return jsonify({'error': 'Failed to upload image'}), 500
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
        
    else:
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
    
#gettask
@app.route('/api/taskdetail/<int:id>', methods=['GET'])
@csrf.exempt
def get_task(id):
    if mySql:
        task_tuple = MysqlClass.get_task_detail(id)
        task = task_tuple[0]
        if task is None:
            return jsonify({"error": "Data retrieval error"}), 500

        # Backend: 適切な形式に変換
        task['due_date'] = task['due_date'].strftime('%Y-%m-%dT%H:%M')

        # コメントをcreated_atでソート（新しいものが上）し、フォーマットを変更
        task['comments'] = sorted(
            task['comments'], 
            key=lambda x: datetime.strptime(x['created_at'], '%Y-%m-%d %H:%M:%S.%f'), 
            reverse=True
        )

        # ソート後、created_atを希望の形式に変更
        for comment in task['comments']:
            comment['created_at'] = datetime.strptime(comment['created_at'], '%Y-%m-%d %H:%M:%S.%f').strftime('%Y/%m/%d - %H:%M')

        result = jsonify(task)

        return result, 200
    else:
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

#searchtasks
@app.route('/search', methods=['GET'])
def search_tasks():
    if request.method == 'GET':
            try:
                query = request.args.get('query', '')   
                if not query:
                    return jsonify([])  # クエリがない場合は空のリストを返す
                result = MysqlClass.search(query)
                print(result)
                if result:
                    return jsonify(result)
                else:
                    return jsonify({'error': 'Failed to upload image'}), 500
            except Exception as e:
                print(f"Unexpected error: {e}")
                return jsonify({'error': 'Internal Server Error'}), 500
    else:
        query = request.args.get('query', '')
        
        if not query:
            return jsonify([])  # クエリがない場合は空のリストを返す
        
        # データベースからクエリに一致するタスクを検索し、created_atでソート
        tasks = Todo.query.filter(Todo.content.ilike(f'%{query}%')).order_by(Todo.created_at.desc()).all()
        
        # タスクを辞書形式で返す
        result = [task.to_dict() for task in tasks]
        
        return jsonify(result)

#Updatetask
@app.route('/api/update_task/<int:id>', methods=['POST'])
@csrf.exempt
def update_task(id):
    if mySql:
        if request.method == 'POST':
            try:
                data = request.get_json()
                content = data.get('content')
                description = data.get('description')
                due_date_str = data.get('due_date')
                
                # ISO 8601 形式の文字列を UTC datetime オブジェクトに変換
                utc_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                
                # JST (UTC+9) のタイムゾーンオブジェクトを作成
                jst = pytz.timezone('Asia/Tokyo')
                
                # UTC datetime を JST に変換
                due_date = utc_date.astimezone(jst)
                result = MysqlClass.update_task(id,content,description,due_date)
                if result:
                    return jsonify({'message': 'Image uploaded successfully', 'id': result}), 200
                else:
                    return jsonify({'error': 'Failed to upload image'}), 500
            except Exception as e:
                print(f"Unexpected error: {e}")
                return jsonify({'error': 'Internal Server Error'}), 500
        return result
    else:
        todo = Todo.query.get_or_404(id)
        data = request.json
        todo.content = data['content']
        todo.description = data['description']
        todo.due_date = datetime.strptime(data['due_date'], '%Y-%m-%dT%H:%M')
        db.session.commit()
        return jsonify({'message': 'Task updated successfully'}), 200
#addcomment
@app.route('/api/tasks/<int:id>/comments', methods=['POST'])
@csrf.exempt
def add_comment(id):
    if mySql:
        if request.method == 'POST':
            data = request.json
            todo_id=id
            new_comment = data['content']
            result = MysqlClass.add_comment(todo_id,new_comment)
            return jsonify({'message': 'Comment added successfully'}), 200
    else:
        data = request.json
        new_comment = Comment(content=data['content'], todo_id=id)
        db.session.add(new_comment)
        db.session.commit()
        return jsonify({'message': 'Comment added successfully'}), 200

#getalltasks
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    if mySql:
        try:
            # タスクのリストを取得
            tasks = MysqlClass.get_all_data()  # データベースからタスクを取得
            logging.debug(tasks)  # デバッグ用のログ
            if tasks is None:
                return jsonify({"error": "Data retrieval error"}), 500

            # データが取得できた場合はJSON形式で返す
            return jsonify(tasks), 200
        except Exception as e:
            print(f"An error occurred: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    else:
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
# 東京時間 (JST) タイムゾーンを定義
JST = pytz.timezone('Asia/Tokyo')
#addtask
@app.route('/add', methods=['POST'])
@csrf.exempt
def add():
    if mySql:
        if request.method == 'POST':
            try:
                data = request.get_json()
                content = data.get('content')
                description = data.get('description')
                due_date_str = data.get('dueDate')
                
                # ISO 8601 形式の文字列を UTC datetime オブジェクトに変換
                utc_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                
                # JST (UTC+9) のタイムゾーンオブジェクトを作成
                jst = pytz.timezone('Asia/Tokyo')
                
                # UTC datetime を JST に変換
                due_date = utc_date.astimezone(jst)

                # Add task to the database
                task_id = MysqlClass.add_task(content, description, due_date)

                if task_id:
                    return jsonify({'taskId': task_id}), 201
                else:
                    return jsonify({'error': 'Failed to add task'}), 500
            except Exception as e:
                print(f"Unexpected error: {e}")
                return jsonify({'error': 'Internal Server Error'}), 500
    else:
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

#deletetask
@app.route('/api/deletetask/<int:task_id>', methods=['DELETE'])
@csrf.exempt
def delete_task(task_id):
    if mySql:
        # MySQLから画像データを取得
        success = MysqlClass.delete_task(task_id)
        if success:
            return jsonify({"message": "Task deleted successfully"}), 200
        else:
            return jsonify({"message": "Task not found or error occurred"}), 404
    else:
        task = Todo.query.get_or_404(task_id)
        
        for image in task.images:
            db.session.delete(image)
        for comment in task.comments:
            db.session.delete(comment)

        db.session.delete(task)
        db.session.commit()
        
        return '', 204

#getcsrftoken
@app.route('/api/csrf-token', methods=['GET'])
def csrf_token():
    token = generate_csrf()
    app.logger.debug(f"CSRF Token: {token}")
    return jsonify({'csrfToken': token})



#deleteimage
@app.route('/api/images/<int:id>', methods=['DELETE'])
@csrf.exempt
def delete_image(id):
    if mySql:
        # MySQLから画像データを取得
        success = MysqlClass.delete_image(id)
        if success:
            return jsonify({"message": "Task deleted successfully"}), 200
        else:
            return jsonify({"message": "Task not found or error occurred"}), 404
    else:
        image = Image.query.get(id)
        if image:
            db.session.delete(image)
            db.session.commit()
            return jsonify({'message': 'Image deleted successfully'}), 200
        else:
            return jsonify({'error': 'Image not found'}), 404
    
#updatecomment,deletecomment    
@app.route('/api/comment/<int:comment_id>', methods=['PUT', 'DELETE'])
@csrf.exempt
def modify_comment(comment_id):
    if mySql:
        if request.method == 'PUT':
            data = request.json
            content = data['content']
            success = MysqlClass.update_comment(comment_id,content)
            if success:
                return jsonify({"message": "Task deleted successfully"}), 200
            else:
                return jsonify({"message": "Task not found or error occurred"}), 404
        elif request.method == 'DELETE':
            # MySQLから画像データを取得
            success = MysqlClass.delete_comment(comment_id)
            if success:
                return jsonify({"message": "Task deleted successfully"}), 200
            else:
                return jsonify({"message": "Task not found or error occurred"}), 404
    else:
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

@app.errorhandler(Exception)
def handle_exception(e):
    # エラーの詳細をログに出力
    import traceback
    app.logger.error(f"Exception: {str(e)}")
    app.logger.error(traceback.format_exc())
    return jsonify(error=str(e)), 500

@app.route('/comment/delete/<int:id>', methods=['POST'])
@csrf.exempt
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    return redirect(request.referrer or url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # ここでテーブルを作成します
    app.run(host='0.0.0.0', port=5000)


