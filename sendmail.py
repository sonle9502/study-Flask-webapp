import schedule
import time
from datetime import datetime
from models import db, Todo
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app as app
from threading import Thread

def send_email(subject, body, to):
    from_email = "soncuc182304@gmail.com"
    password = "vrtt wsgn ktup mmga"  # 生成されたアプリ パスワードを入力
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to, text)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

def check_due_tasks(app):
    with app.app_context():  # アプリケーションコンテキストを設定
        now = datetime.now()
        tasks = Todo.query.all()
        for task in tasks:
            if not task.email_sent and task.due_date and task.due_date <= now :
                subject = "Task Due Reminder"
                body = f"Task : '{task.content}'\nDescription : {task.description} is due now!"
                to = "soncuc182304@gmail.com"
                send_email(subject, body, to)
                # メール送信後にフラグを更新
                task.email_sent = True
                db.session.commit()

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_scheduler(app):
    with app.app_context():
        schedule.every(1).minutes.do(check_due_tasks,  app) 
        scheduler_thread = Thread(target=run_scheduler)
        scheduler_thread.start()