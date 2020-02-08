from django.shortcuts import render, redirect
from django.views.generic import View
from django.core.urlresolvers import reverse
from goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner, GoodsSKU, Goods, \
    GoodsImage
from django_redis import get_redis_connection
from django.core.cache import cache
from order.models import OrderGoods
from django.core.paginator import Paginator


# Create your views here.
class IndexView(View):
    def get(self, request):
        context = cache.get('index_page_cache')

        if context is None:
            # 获取商品种类信息
            types = GoodsType.objects.all()

            # 获取首页轮播商品信息
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')

            # 获取首页促销活动信息
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

            # 获取首页分类商品
            for type in types:
                # 获取type种类首页分类商品的图片展示信息
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
                # 获取type种类首页分类商品的文字展示信息
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
                # 动态给type增加属性
                type.image_banners = image_banners
                type.title_banners = title_banners

            # 组织模版上下文
            context = {'types': types,
                       'goods_banners': goods_banners,
                       'promotion_banners': promotion_banners
                       }
            # 设置缓存
            cache.set('index_page_data', context, 3600)

        # 获取购物车中商品数目
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            #  用户登录
            conn = get_redis_connection('default')
            cart_key = "cart_%d" % user.id
            cart_count = conn.hlen(cart_key)
        context.update(cart_count=cart_count)

        return render(request, 'index.html', context)


# /goods/商品id
class DetailView(View):
    def get(self, request, goods_id):
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse('goods:index'))

        # 获取商品的分类信息
        types = GoodsType.objects.all()

        # 获取商品的评论信息
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')
        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-creat_time')[:2]

        # 获取同一个SPU的其他规格商品
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            #  用户登录
            conn = get_redis_connection('default')
            cart_key = "cart_%d" % user.id
            cart_count = conn.hlen(cart_key)
            # 添加历史记录
            history_key = 'history_%d' % user.id
            # 更新历史记录
            # 移除列表中的goods_id
            conn.lrem(history_key, 0, goods_id)
            # 把goods——id插入到左边
            conn.lpush(history_key, goods_id)
            conn.ltrim(history_key, 0, 4)

        context = {
            'sku': sku,
            'types': types,
            'sku_orders': sku_orders,
            'new_skus': new_skus,
            'same_spu_skus': same_spu_skus,
            'cart_count': cart_count
        }
        return render(request, 'detail.html', context)


# 种类id 页码 排序方式
# /list/种类id/页码/排序方式
class ListView(View):
    def get(self, request, type_id, page):
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            return redirect(reverse('goods:index'))

        types = GoodsType.objects.all()
        # 按照默认id排序(排序方式：id 价格 人气 销量)
        sort = request.GET.get('sort')

        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('sales')
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        # 分页
        paginator = Paginator(skus, 1)
        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page第实力对象
        skus_page = paginator.page(page)

        # 进行页码第控制，页面上最多显示5页
        # 如果当前页是第三页，显示1-5页
        # 如果当前页是最后3页，显示后5页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-creat_time')[:2]

        # 获取购物车中商品数目
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            #  用户登录
            conn = get_redis_connection('default')
            cart_key = "cart_%d" % user.id
            cart_count = conn.hlen(cart_key)
        context = {
            'type': type,
            'types': types,
            'skus_page': skus_page,
            'new_skus': new_skus,
            'cart_count': cart_count,
            'pages': pages,
            'sort': sort
        }
        return render(request, 'list.html', context)
