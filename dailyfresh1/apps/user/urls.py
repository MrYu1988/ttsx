from django.conf.urls import include, url
from user.views import RegisterVeiw,ActiveView,LoginView

urlpatterns = [
    #url(r'^register$', views.register, name='register'), #注册
    # url(r'^register_handle$', views.register_handle, name='register_handle'), #注册处理
    url(r'^register', RegisterVeiw.as_view(), name='register'),
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),
    url(r'^login$', LoginView.as_view(), name='login'),
]
