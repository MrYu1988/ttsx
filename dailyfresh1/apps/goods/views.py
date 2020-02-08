from django.shortcuts import render
from django.views.generic import View
from goods.models import GoodsType,IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner
from django_redis import get_redis_connection

# Create your views here.
class IndexView(View):
    def get(self, request):
        #获取商品种类信息
        types = GoodsType.objects.all()

        #获取首页轮播商品信息
        goods_banners = IndexGoodsBanner.objects.all().order_by('index')

        #获取首页促销活动信息
        promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

        #获取首页分类商品
        for type in types:
            #获取type种类首页分类商品的图片展示信息
            image_banners = IndexTypeGoodsBanner.objects.filter(type = type,display_type=1).order_by('index')
            #获取type种类首页分类商品的文字展示信息
            title_banners = IndexTypeGoodsBanner.objects.filter(type = type,display_type=0).order_by('index')
            #动态给type增加属性
            type.image_banners = image_banners
            type.title_banners = title_banners

        #获取购物车中商品数目
        user = request.user
        if user.is_authenticated():
            # 用户登录
            conn = get_redis_connection('default')
            cart_key = "cart_%d" % user.id
            cart_count = conn.hlen(cart_key)
        else:
            cart_count = 0

        #组织模版上下文
        context ={'types':types,
                  'goods_banners':goods_banners,
                  'promotion_banners':promotion_banners,
                  'cart_count':cart_count,
        }
        return render(request, 'index.html', context)