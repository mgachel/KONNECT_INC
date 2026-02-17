from django.urls import path 
from .views import debug_cloudinary, landing, index, wholesale, get_product, create_order, verify_payment, paystack_webhook



urlpatterns = [
    path('', landing, name='shop-landing'),
    path('retail/', index, name='shop-retail'),
    path('wholesale/', wholesale, name='shop-wholesale'),
    path('api/product/<int:product_id>/', get_product, name='get-product'),
    path('api/create-order/', create_order, name='create-order'),
    path('api/verify-payment/', verify_payment, name='verify-payment'),
    path('api/paystack-webhook/', paystack_webhook, name='paystack-webhook'),
    path('debug/', debug_cloudinary, name='debug'),
]



