#使用celery

from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
import time

import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
django.setup()
#创建一个CELERY类的实力对象
app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/8')

#定义人物函数
@app.task
def send_register_active_email(to_email, username, token):
    #发送激活邮件
    subject = '天天生鲜欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = '<a href="http://127.0.0.1:8000/user/active/%s"> http://127.0.0.1:8000/user/active/%s </a>' % (
    token, token)

    send_mail(subject, message, sender, receiver, html_message=html_message)
    time.sleep(5)
