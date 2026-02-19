from django.db import models
from cloudinary.models import CloudinaryField
import uuid

# Create your models here.



class Category(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name

class Products(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=50)
    product_price = models.FloatField(help_text='Retail price per unit')
    wholesale_price = models.FloatField(blank=True, null=True, help_text='Wholesale unit price per item in a box (leave blank to default to ₵200)')
    quantity_per_box = models.PositiveIntegerField(default=1, help_text='Number of units per box for wholesale')
    product_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    product_image = CloudinaryField('image')
    product_stock = models.IntegerField()
    is_new = models.BooleanField(default=False)

    @property
    def get_wholesale_price(self):
        """Return wholesale unit price if set, otherwise fall back to 200."""
        return self.wholesale_price if self.wholesale_price is not None else 200.0

    @property
    def box_price(self):
        """Price for one full box = unit price × quantity per box."""
        return self.get_wholesale_price * self.quantity_per_box
    
    
    
    def __str__(self): 
        return f"{self.product_name} - {self.category.name}"
    

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    full_name = models.CharField(max_length=100)
    address = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paystack_reference = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order {self.order_id} - {self.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity}x {self.product.product_name}"
    
    @property
    def subtotal(self):
        return self.quantity * self.price



