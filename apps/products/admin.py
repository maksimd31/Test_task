from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_in_stock', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('price', 'stock')
    ordering = ('-created_at',)

    def is_in_stock(self, obj):
        return obj.is_in_stock()
    is_in_stock.boolean = True
    is_in_stock.short_description = 'In Stock'
