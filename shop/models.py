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
    product_price = models.FloatField()
    product_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    product_image = CloudinaryField('image')
    product_description = models.TextField(blank=True, null=True)
    product_stock = models.IntegerField()
    is_new = models.BooleanField(default=False)
    
    
    
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



