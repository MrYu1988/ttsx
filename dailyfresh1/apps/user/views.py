from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from user.models import User
from django.conf import settings
from django.http import HttpResponse
from django.core.mail import send_mail
from celery_tasks.tasks import send_register_active_email


from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
import re

# Create your views here.

class RegisterVeiw(View):
    def get(self, request):
        '''进行页面显示'''
        return render(request, 'register.html')

    def post(self, request):
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 进行数据校验
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            print('用户名不存在')
            user = None

        if user:
            return render(request, 'register.html', {'errmsg': '用户名已存在'})
        # 进行业务处理:进行用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 发送激活邮件，包含激活链接:http://127.0.0.1:8000/user/active/3


        #激活链接中需要包含用户身份信息,并且身份信息进行加密
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm' : user.id}
        token = serializer.dumps(info)
        token = token.decode('utf8')

        #send_mail
        send_register_active_email.delay(email, username, token)

        # 返回应答,跳转到首页

        return redirect(reverse('goods:index'))


class ActiveView(View):
    '''用户激活'''
    def get(self, requeset, token):
        '''进行用户激活'''
        #进行解密
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)

            #获取激活用户的ID
            user_id = info['confirm']
            user = User.objects.get(id = user_id)
            user.is_active = 1
            user.save()

            #跳转到登录界面
            return redirect(reverse('user:login'))
        except SignatureExpired as e :
            return HttpResponse('密钥已过期')


class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')






