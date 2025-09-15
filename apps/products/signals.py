# apps/products/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Product
from .cache_utils import bump_list_version


@receiver(post_save, sender=Product)
def product_saved(sender, instance, **kwargs):
    """
    Signal triggered after a product is created or updated.
    Invalidate the product list cache by bumping the version.
    """
    bump_list_version()


@receiver(post_delete, sender=Product)
def product_deleted(sender, instance, **kwargs):
    """
    Signal triggered after a product is deleted.
    Invalidate the product list cache by bumping the version.
    """
    bump_list_version()

# ➡ «В API мы сбрасываем кэш явно в perform_create/update/destroy,
# чтобы код был прост и предсказуем.
# Дополнительно я подключил Django signals — так список продуктов инвалидируется автоматически,
# даже если изменения происходят не через API (например, через админку или Celery).
# Таким образом, мы решаем задачу и простоты, и надёжности».