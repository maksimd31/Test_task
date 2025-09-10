"""
Celery configuration for Test_task project.

This module configures Celery for asynchronous task processing with Redis
as the message broker and result backend. It automatically discovers tasks
from all Django applications.

Features:
    - Redis as broker and result backend
    - Automatic task discovery from Django apps
    - Debug task for testing Celery functionality
    - Integration with Django settings

Usage:
    Start Celery worker:
        celery -A Test_task worker --loglevel=info

    Start Celery beat (for scheduled tasks):
        celery -A Test_task beat --loglevel=info
"""
import os
from celery import Celery

# Set default Django settings module for Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Test_task.settings')

# Create Celery application instance
app = Celery('Test_task')

# Configure Celery using Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatically discover tasks from all Django applications
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    """
    Debug task for testing Celery functionality.

    This task can be used to verify that Celery is working properly
    and can execute tasks successfully.

    Args:
        self: Task instance (bound task)

    Returns:
        None: Prints request information to console
    """
    print(f'Request: {self.request!r}')