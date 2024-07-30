from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from config import Config  

app = Flask(__name__)
app.config.from_object(Config) 
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)  # 期限を追加

    def __repr__(self):
        return f'<Task {self.id}>'
    
@app.route('/')
def index():
    tasks = Todo.query.all()
    return render_template('index.html', todos=tasks)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        task_content = request.form['content']
        new_task = Todo(content=task_content)
        db.session.add(new_task)
        db.session.commit()
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

# if __name__ == "__main__":
#     # Waitress serverを使用してアプリケーションを起動
#     serve(app, host='0.0.0.0', port=8080)

# 開発環境
if __name__ == "__main__":
    app.run(debug=True)
    