from decimal import Decimal
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from .models import OrderItem, Order
from .cache_utils import bump_order_detail_version

@receiver(post_save, sender=OrderItem)
def order_item_saved(sender, instance: OrderItem, **kwargs):
    instance.order.recalculate_total()
    bump_order_detail_version()

@receiver(post_delete, sender=OrderItem)
def order_item_deleted(sender, instance: OrderItem, **kwargs):
    instance.order.recalculate_total()
    bump_order_detail_version()

@receiver(post_save, sender=Order)
def order_saved(sender, instance: Order, **kwargs):
    # bump version to invalidate cached details after status changes
    bump_order_detail_version()
