from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0003_alter_orderitem_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='total_price',
            field=models.DecimalField(verbose_name='total_price', max_digits=10, decimal_places=2, default=Decimal('0.00')),
        ),
    ]

