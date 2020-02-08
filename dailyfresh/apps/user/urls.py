from django.conf.urls import include, url
from user.views import RegisterVeiw,ActiveView,LoginView,LogoutView,UserInfoView,UserOrderView,AddressView
from django.contrib.auth.decorators import login_required

urlpatterns = [
    #url(r'^register$', views.register, name='register'), #注册
    # url(r'^register_handle$', views.register_handle, name='register_handle'), #注册处理
    url(r'^register', RegisterVeiw.as_view(), name='register'),
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),
    url(r'^login$', LoginView.as_view(), name='login'),
    url(r'^logout$', LogoutView.as_view(), name='logout'),

    # url(r'^order$', login_required(UserOrderView.as_view()), name='order'),
    # url(r'^address$', login_required(AddressView.as_view()), name='address'),
    # url(r'^$', login_required(UserInfoView.as_view()), name='user'),

    url(r'^order/(?P<page>\d+)$',UserOrderView.as_view(), name='order'),
    url(r'^address$', AddressView.as_view(), name='address'),
    url(r'^$', UserInfoView.as_view(), name='user'),
]
