# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OrderGoods',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('creat_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now_add=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(verbose_name='删除标记', default=False)),
                ('count', models.IntegerField(verbose_name='商品数目', default=1)),
                ('price', models.DecimalField(max_digits=10, verbose_name='商品价格', decimal_places=2)),
                ('comment', models.CharField(max_length=256, verbose_name='评论')),
            ],
            options={
                'db_table': 'df_order_goods',
                'verbose_name': '订单商品',
                'verbose_name_plural': '订单商品',
            },
        ),
        migrations.CreateModel(
            name='OrderInfo',
            fields=[
                ('creat_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now_add=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(verbose_name='删除标记', default=False)),
                ('order_id', models.CharField(primary_key=True, serialize=False, max_length=128, verbose_name='订单id')),
                ('pay_method', models.SmallIntegerField(choices=[(1, '货到付款'), (2, '微信支付'), (3, '支付宝'), (4, '银联支付')], verbose_name='支付方式', default=3)),
                ('total_count', models.IntegerField(verbose_name='商品数量', default=1)),
                ('total_price', models.DecimalField(max_digits=10, verbose_name='商品总价', decimal_places=2)),
                ('transit_price', models.DecimalField(max_digits=10, verbose_name='订单运费', decimal_places=2)),
                ('order_status', models.SmallIntegerField(choices=[(1, '待支付'), (2, '待发货'), (3, '待收货'), (4, '待评价'), (5, '已完成')], verbose_name='订单状态', default=1)),
                ('trade_no', models.CharField(max_length=128, verbose_name='支付编号')),
            ],
            options={
                'db_table': 'df_order_info',
                'verbose_name': '订单',
                'verbose_name_plural': '订单',
            },
        ),
    ]
