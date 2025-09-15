from django.db import migrations
from decimal import Decimal

def recalc_total_price(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    OrderItem = apps.get_model('orders', 'OrderItem')
    for order in Order.objects.all():
        total = Decimal('0.00')
        for item in OrderItem.objects.filter(order=order):
            total += item.quantity * item.price_at_purchase
        if order.total_price != total:
            order.total_price = total
            order.save(update_fields=['total_price'])

class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0004_add_total_price_field'),
    ]

    operations = [
        migrations.RunPython(recalc_total_price, migrations.RunPython.noop)
    ]

