from django.contrib import admin
from django.utils.html import format_html
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
    list_display = ['product_name', 'product_code', 'category', 'product_price', 'wholesale_price', 'quantity_per_box', 'product_stock', 'is_new', 'image_thumbnail']
    list_filter = ['category', 'is_new']
    search_fields = ['product_name', 'product_code']
    readonly_fields = ['image_preview']
    fields = ('category', 'product_name', 'product_code', 'is_new', 'product_price', 'wholesale_price', 'quantity_per_box', 'product_stock', 'product_image', 'image_preview')

    def image_preview(self, obj):
        """Large preview shown on the edit form."""
        if obj.product_image:
            url = obj.product_image.url
            return format_html(
                '<img src="{}" style="max-height:300px;max-width:100%;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.15)" />',
                url
            )
        return 'No image uploaded yet'
    image_preview.short_description = 'Image Preview'

    def image_thumbnail(self, obj):
        """Small thumbnail shown in the list view."""
        if obj.product_image:
            url = obj.product_image.url
            return format_html(
                '<img src="{}" style="height:40px;width:40px;object-fit:cover;border-radius:4px" />',
                url
            )
        return '-'
    image_thumbnail.short_description = 'Image'

    class Media:
        js = ('admin/js/image_preview.js',)
