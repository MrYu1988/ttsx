from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from user.models import User,Address
from django.conf import settings
from django.http import HttpResponse
from django.core.mail import send_mail
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate,login,logout
from django_redis import get_redis_connection
from goods.models import GoodsSKU


from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
import re
from utils.mixin import LoginRequiredMixin


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
        #判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
            #使用模板
        return render(request, 'login.html',{'username':username,'checked':checked})


    def post(self, request):
        username =request.POST.get('username')
        password = request.POST.get('pwd')

        if not all([username, password]):
            return render(request, 'login.html', {'errmsg':'数据不完整'})

        user = authenticate(username=username, password = password)
        if user is not None:
            #用户名密码正确
            if user.is_active:
                #用户已激活
                #记录用户激活状态
                login(request,user)
                #获取登录后所要跳转的地址
                #默认跳转到首页
                next_url = request.GET.get('next',reverse('goods:index'))#None
                #跳转到首页
                response = redirect(next_url)
                #判断是否需要记住用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    # 记住用户名
                    response.set_cookie('username',username,max_age=7*24*3600)
                else:
                    response.delete_cookie('username')
                #返回response
                return response
            else:
                #用户未激活
                return render(request, 'login.html', {'errmsg': '账户未激活'})
        else:
            return render(request, 'login.html', {'errmsg': '用户名密码错误'})

class LogoutView(View):
    def get(self,request):
        #清除用户到session信息
        logout(request)
        #跳转到首页
        return redirect(reverse('goods:index'))


#/user/info
class UserInfoView(LoginRequiredMixin,View):
    '''用户中心-信息页'''
    def get(self,request):
        '''显示'''
        # page = 'user'
        #如果用户登录-》user实例
        #如果用户未登录-》anonymous实例
        # request.user.is_authenticated()

        # 获取用户的个人信息
        user = request.user
        address = Address.object.get_default_address(user)

        # 获取用户的历史浏览记录
        # from redis import StrictRedis
        # StrictRedis(host='127.0.0.1', port = '6379', db = 9);
        con = get_redis_connection('default')
        history_key = 'history_%d'%user.id
        #获取用户最新浏览的五个商品的id
        sku_ids = con.lrange(history_key, 0,4)
        #从数据库中查询用户浏览商品的具体信息
        #good_li = GoodsSKU.objects.filter(id_in=sku_ids)
        good_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id = id)
            good_li.append(goods)
        #组织上下文
        context = {'page':'user',
                   'address':address,
                   'good_li':good_li}

        #除了你给模板文件传递的模板变量之外，django会把request.user传给模板文件
        return render(request, 'user_center_info.html',{'page':'user','address':address})

#/user/order
class UserOrderView(LoginRequiredMixin,View):
    '''用户中心-信息页'''
    def get(self, request):
        '''显示'''
        #获取用户的订单信息

        return render(request, 'user_center_order.html',{'page':'order'})

#/user/site
class AddressView(LoginRequiredMixin,View):
    '''用户中心-信息页'''
    def get(self, request):
        '''显示'''
        user = request.user
        address = Address.object.get_default_address(user)
        #获取用户的默认收货地址信息
        return render(request, 'user_center_site.html',{'page':'address','address':address})

    def post(self,request):
        '''地址添加'''
        #接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')


        #校验数据
        if not all([receiver,addr,phone]):
            return render(request, 'user_center_site.html',{'errmsg':'数据不完整'})
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$',phone ):
            return render(request,'user_center_site.html', {'errmsg':'手机格式不正确'})

        #地址添加-业务处理
        #如果用户已存在默认地址，添加的地址不作为默认地址，否则作为默认收货地址
        #获取用户对应的对象
        user = request.user
        # try:
        #     address = Address.objects.get(user=user,is_default=True)
        # except Address.DoesNotExist:
        #     #不存在默认地址
        #     address = None

        address = Address.object.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default = True
        #添加地址
        Address.object.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)

        #返回应答,刷新界面
        return redirect(reverse('user:address'))







