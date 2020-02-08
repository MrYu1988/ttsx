from django.conf.urls import include, url
from goods.views import IndexView,DetailView,ListView



urlpatterns = [
    url(r'^goods/(?P<goods_id>\d+)$', DetailView.as_view(), name='detail'),  # 详情页
    url(r'^index$', IndexView.as_view(), name='index'),
    url(r'^list/(?P<type_id>\d+)/(?P<page>\d+)$', ListView.as_view(), name='list'),

]
