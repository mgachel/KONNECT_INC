from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import Category, Products, Order, OrderItem
import json
import requests
import uuid

# Create your views here.

def index(request):
    categories = Category.objects.prefetch_related('products_set').all()
    context = {
        'categories': categories,
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
    }
    return render(request, 'html/index.html', context)


def get_product(request, product_id):
    """Get single product details for cart"""
    try:
        product = Products.objects.get(id=product_id)
        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.product_name,
                'price': float(product.product_price),
                'image': product.product_image.url,
                'stock': product.product_stock,
            }
        })
    except Products.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)


@csrf_exempt
@require_POST
def create_order(request):
    """Create order and initialize Paystack payment"""
    try:
        data = json.loads(request.body)
        
        # Validate cart items
        cart_items = data.get('cart', [])
        if not cart_items:
            return JsonResponse({'success': False, 'error': 'Cart is empty'}, status=400)
        
        # Validate required fields
        email = data.get('email')
        full_name = data.get('full_name')
        phone = data.get('phone')
        address = data.get('address')
        
        if not all([email, full_name, phone, address]):
            return JsonResponse({'success': False, 'error': 'All fields are required'}, status=400)
        
        # Calculate total and validate products
        total = 0
        order_items_data = []
        
        for item in cart_items:
            try:
                product = Products.objects.get(id=item['id'])
                quantity = int(item['quantity'])
                
                if quantity > product.product_stock:
                    return JsonResponse({
                        'success': False, 
                        'error': f'{product.product_name} only has {product.product_stock} in stock'
                    }, status=400)
                
                item_total = float(product.product_price) * quantity
                total += item_total
                order_items_data.append({
                    'product': product,
                    'quantity': quantity,
                    'price': product.product_price
                })
            except Products.DoesNotExist:
                return JsonResponse({'success': False, 'error': f'Product with ID {item.get("id")} not found'}, status=400)
        
        # Create order
        order = Order.objects.create(
            email=email,
            phone=phone,
            full_name=full_name,
            address=address,
            total_amount=total,
            status='pending'
        )
        
        # Create order items
        for item_data in order_items_data:
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                quantity=item_data['quantity'],
                price=item_data['price']
            )
        
        # Initialize Paystack transaction
        paystack_url = 'https://api.paystack.co/transaction/initialize'
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Amount in kobo (multiply by 100)
        paystack_data = {
            'email': email,
            'amount': int(total * 100),
            'reference': str(order.order_id),
            'callback_url': data.get('callback_url', request.build_absolute_uri('/')),
            'metadata': {
                'order_id': str(order.order_id),
                'customer_name': full_name,
                'phone': phone
            }
        }
        
        try:
            response = requests.post(paystack_url, json=paystack_data, headers=headers, timeout=30)
            paystack_response = response.json()
        except requests.exceptions.RequestException as e:
            order.status = 'failed'
            order.save()
            return JsonResponse({'success': False, 'error': f'Payment service unavailable: {str(e)}'}, status=503)
        
        if paystack_response.get('status'):
            order.paystack_reference = paystack_response['data']['reference']
            order.save()
            
            return JsonResponse({
                'success': True,
                'authorization_url': paystack_response['data']['authorization_url'],
                'access_code': paystack_response['data']['access_code'],
                'reference': paystack_response['data']['reference'],
                'order_id': str(order.order_id)
            })
        else:
            order.status = 'failed'
            order.save()
            return JsonResponse({
                'success': False, 
                'error': paystack_response.get('message', 'Payment initialization failed')
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def verify_payment(request):
    """Verify Paystack payment"""
    try:
        data = json.loads(request.body)
        reference = data.get('reference')
        
        if not reference:
            return JsonResponse({'success': False, 'error': 'Reference required'}, status=400)
        
        # Verify with Paystack
        paystack_url = f'https://api.paystack.co/transaction/verify/{reference}'
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        }
        
        response = requests.get(paystack_url, headers=headers)
        paystack_response = response.json()
        
        if paystack_response.get('status') and paystack_response['data']['status'] == 'success':
            # Update order status
            try:
                order = Order.objects.get(order_id=reference)
                order.status = 'paid'
                order.save()
                
                # Update product stock
                for item in order.items.all():
                    item.product.product_stock -= item.quantity
                    item.product.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Payment verified successfully',
                    'order_id': str(order.order_id),
                    'amount': float(order.total_amount)
                })
            except Order.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
        else:
            return JsonResponse({
                'success': False, 
                'error': 'Payment verification failed'
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def paystack_webhook(request):
    """Handle Paystack webhooks"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            event = data.get('event')
            
            if event == 'charge.success':
                reference = data['data']['reference']
                try:
                    order = Order.objects.get(order_id=reference)
                    if order.status != 'paid':
                        order.status = 'paid'
                        order.save()
                        
                        # Update product stock
                        for item in order.items.all():
                            item.product.product_stock -= item.quantity
                            item.product.save()
                except Order.DoesNotExist:
                    pass
                    
            return JsonResponse({'status': 'ok'})
        except:
            return JsonResponse({'status': 'error'}, status=400)
    
    return JsonResponse({'status': 'method not allowed'}, status=405)





def debug_cloudinary(request):
    """Temporary debug view - DELETE AFTER TESTING"""
    from django.http import JsonResponse
    from django.conf import settings
    from .models import Products
    
    return JsonResponse({
        'cloud_name': settings.CLOUDINARY_STORAGE.get('CLOUD_NAME', 'NOT SET'),
        'api_key_set': bool(settings.CLOUDINARY_STORAGE.get('API_KEY')),
        'api_secret_set': bool(settings.CLOUDINARY_STORAGE.get('API_SECRET')),
        'default_storage': getattr(settings, 'DEFAULT_FILE_STORAGE', 'NOT SET'),
        'products': [
            {'name': p.product_name, 'image_url': p.product_image.url if p.product_image else None}
            for p in Products.objects.all()[:3]
        ]
    })