from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)  # 期限を追加
    email_sent = db.Column(db.Boolean, default=False) #メールを送信されたかどうかを判断
    images = db.relationship('Image', backref='todo', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='todo', lazy=True)

    def to_dict(self):
        return {
                'id': self.id,
                'content': self.content,
                'completed': self.completed,
                'description': self.description,
                'due_date': self.due_date.isoformat() if self.due_date else None,
                'email_sent': self.email_sent,
                'images': [{'id': image.id, 'filename': image.filename} for image in self.images],
                'created_at': self.format_date(self.created_at),
                'due_date': self.format_date(self.due_date),
                'images': [{'id': image.id, 'filename': image.filename} for image in self.images],
                'comments': [{'id': comment.id, 'text': comment.content} for comment in self.comments]
            }
        
    def format_date(self, date):
        """Format date as Japanese-style date string."""
        if not date:
            return None
        return date.strftime('%Y年%m月%d日 %H時%M分')
    
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    todo_id = db.Column(db.Integer, db.ForeignKey('todo.id'), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)  # 画像データを保存するカラム

    def __repr__(self):
        return f'<Image {self.id}>'
    
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    todo_id = db.Column(db.Integer, db.ForeignKey('todo.id'), nullable=False)
    
    def __repr__(self):
        return f'<Comment {self.id}>'
    