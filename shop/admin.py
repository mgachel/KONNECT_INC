from django.contrib import admin
from .models import Category, Products, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price', 'subtotal']
    
    def subtotal(self, obj):
        return f"₵{obj.subtotal:.2f}"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'full_name', 'email', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_id', 'full_name', 'email', 'phone']
    readonly_fields = ['order_id', 'paystack_reference', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order_id', 'status', 'paystack_reference')
        }),
        ('Customer Info', {
            'fields': ('full_name', 'email', 'phone', 'address')
        }),
        ('Payment', {
            'fields': ('total_amount',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Register your models here.
admin.site.register(Category)


@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'product_code', 'category', 'product_price', 'wholesale_price', 'product_stock', 'is_new']
    list_filter = ['category', 'is_new']
    search_fields = ['product_name', 'product_code']
