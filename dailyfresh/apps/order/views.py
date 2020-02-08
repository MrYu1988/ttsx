from django.shortcuts import render, redirect
from django.views.generic import View
from django.http import JsonResponse
from django.core.urlresolvers import reverse
from django_redis import get_redis_connection
from django.db import transaction
from goods.models import GoodsSKU
from user.models import Address
from utils.mixin import LoginRequiredMixin
from order.models import OrderInfo, OrderGoods
from datetime import datetime


# 提交订单
class OrderPlaceView(View):
    def post(self, request):
        user = request.user

        sku_ids = request.POST.get('sku_ids')
        # 数据校验
        if not sku_ids:
            return redirect(reverse('cart:show'))

        # 业务处理:添加购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        skus = []
        total_count = 0
        total_price = 0
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)
            count = conn.hget(cart_key, sku_id)
            amount = sku.price * int(count)
            sku.count = count
            sku.amount = amount
            skus.append(sku)
            total_count += int(count)
            total_price += int(amount)

        # 运费：实际开发的时候，属于一个子系统
        transit_price = 10
        # 实付款
        total_pay = total_price + transit_price
        # 收件地址
        addrs = Address.object.filter(user=user)

        sku_ids = ','.join(sku_ids)  # 组成字符串
        context = {
            'skus': skus,
            'total_count': total_count,
            'total_price': total_price,
            'transit_price': transit_price,
            'total_pay': total_pay,
            'addrs': addrs,
            'sku_ids': sku_ids,
        }
        return render(request, 'place_order.html', context)


# 订单创建 地址 支付方式 用户要购买的商品id
#悲观锁
class OrderCommitView(View):
    '''订单创建'''
    @transaction.atomic
    def post(self, request):
        user = request.user
        if not user.is_authenticated():
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')

        # 数据校验
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整'})

        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法支付方式'})

        try:
            addr = Address.object.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '地址非法'})



        # todo:创建订单核心业务
        order_id = datetime.now().strftime('%Y%m%d%H%M%s') + str(user.id)

        # 运费
        transit_price = 10
        # 总数目和总金额
        total_count = 0
        total_price = 0

        #设置事务保存点
        save_id = transaction.savepoint()
        try:
            #增加记录
            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                addr=addr,
                pay_method=pay_method,
                total_count=total_count,
                total_price=total_price,
                transit_price=transit_price,
            )
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                try:
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                except:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 4, 'errmsg': '商品不存在'})
                # 从redis中获取商品数量
                count = conn.hget(cart_key, sku_id)

                # todo:判断商品的库存
                if int(count) > sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

                # todo: 增加记录
                OrderGoods.objects.create(
                    order=order,
                    sku=sku,
                    count=count,
                    price=sku.price,
                )

                # todo：更新商品的库存和销量
                sku.stock -= int(count)
                sku.sales += int(count)
                sku.save()

                amount = sku.price * int(count)
                total_count += int(count)
                total_price += amount

            # todo:更新数据库中商品数量和金额
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

    # todo:清除用户购物车中的记录[1,3]
        conn.hdel(cart_key, *sku_ids)

        return JsonResponse({'res': 5, 'message': '创建成功'})



