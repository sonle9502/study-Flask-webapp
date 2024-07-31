import schedule
import time
from datetime import datetime, timedelta
from models import db, Todo  # Import from models
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

def check_due_tasks():
    with current_app.app_context():
        now = datetime.now()
        tasks = Todo.query.all()
        for task in tasks:
            if task.due_date and task.due_date <= now:
                subject = "Task Due Reminder"
                body = f"Task '{task.content}{task.description}'  is due now!"
                to = "soncuc182304@gmail.com"  # Replace with the recipient's email
                send_email(subject, body, to)

def send_email(subject, body, to):
    from_email = "soncuc182304@gmail.com"
    password = "vrtt wsgn ktup mmga "
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

def run_scheduler():
    schedule.every(1).minutes.do(check_due_tasks)
    while True:
        schedule.run_pending()
        time.sleep(1)
