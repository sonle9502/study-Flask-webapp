import schedule
import time
from datetime import datetime, timedelta
from models import db, Todo  # Import from models
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def check_due_tasks():
    now = datetime.now()
    tasks = Todo.query.all()
    for task in tasks:
        if task.due_date and task.due_date <= now:
            subject = "Task Due Reminder"
            body = f"Task '{task.content}' is due now!"
            to = "soncuc182304@gmail.com"  # Replace with the recipient's email
            send_email(subject, body, to)   

# Schedule the task checker to run every minute
schedule.every(1).minutes.do(check_due_tasks)

def send_email(subject, body, to):
    from_email = "soncuc182304@gmail.com"
    password = "Future0308@#"
    smtp_server = "smtp.example.com"
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