import os
import logging
import requests
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from .models import Order

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def generate_order_pdf_and_send_email(self, order_id):
    """
    Generate PDF report for an order and send email notification.

    This task is triggered automatically when a new order is created.
    It generates a PDF report containing order details and sends an
    email notification to the customer (simulated via logging).

    Args:
        order_id (int): Primary key of the order to process

    Returns:
        str: Success message indicating completion

    Raises:
        Order.DoesNotExist: If order with given ID doesn't exist
        Exception: For any other processing errors (with retry logic)

    Features:
        - PDF generation using ReportLab
        - Retry mechanism (max 3 attempts with 60s delay)
        - Comprehensive error logging
        - Email simulation via logging
    """
    try:
        order = Order.objects.get(id=order_id)

        # Generate PDF report
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)

        # PDF content with order details
        p.drawString(100, 750, f"Order Report #{order.id}")
        p.drawString(100, 720, f"Customer: {order.user.username}")
        p.drawString(100, 690, f"Email: {order.user.email}")
        p.drawString(100, 660, f"Total Amount: ${order.total_price}")
        p.drawString(100, 630, f"Status: {order.status}")
        p.drawString(100, 600, f"Created: {order.created_at}")

        # Add order items to PDF
        y_position = 570
        p.drawString(100, y_position, "Items:")
        y_position -= 30

        for item in order.order_items.all():
            p.drawString(120, y_position, f"- {item.product.name}: {item.quantity} x ${item.price_at_purchase}")
            y_position -= 20

        p.save()

        # Get PDF content and cleanup
        pdf_content = buffer.getvalue()
        buffer.close()

        # Simulate email sending (in production, use actual email service)
        logger.info(f"Email sent for order {order_id}")
        logger.info(f"PDF generated for order {order_id}, size: {len(pdf_content)} bytes")

        return f"PDF generated and email sent for order {order_id}"

    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Error processing order {order_id}: {exc}")
        raise self.retry(countdown=60, exc=exc)

@shared_task(bind=True, max_retries=3)
def notify_external_api_order_shipped(self, order_id):
    """
    Notify external API when order status changes to 'shipped'.

    This task is triggered when an order's status is updated to 'shipped'.
    It sends order details to an external API endpoint for integration
    with third-party services (shipping, analytics, etc.).

    Args:
        order_id (int): Primary key of the shipped order

    Returns:
        str: Success message with API response details

    Raises:
        Order.DoesNotExist: If order with given ID doesn't exist
        Exception: For API call failures (with retry logic)

    Features:
        - External API integration via HTTP POST
        - Retry mechanism (max 3 attempts with 60s delay)
        - Comprehensive error handling and logging
        - Timeout protection (10 seconds)
        - JSON payload with order details
    """
    try:
        order = Order.objects.get(id=order_id)

        # Prepare payload for external API
        payload = {
            'order_id': order.id,
            'user_id': order.user.id,
            'status': order.status,
            'total_amount': float(order.total_price)
        }

        # Make API call to external service
        response = requests.post(
            'https://jsonplaceholder.typicode.com/posts',
            json=payload,
            timeout=10
        )

        if response.status_code == 201:
            logger.info(f"External API notified for order {order_id}")
            return f"External API notified successfully for order {order_id}"
        else:
            raise Exception(f"API returned status {response.status_code}")

    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Error notifying external API for order {order_id}: {exc}")
        raise self.retry(countdown=60, exc=exc)