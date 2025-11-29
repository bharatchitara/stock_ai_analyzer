"""
Background task handling for portfolio operations
"""
import json
import logging
from datetime import datetime
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class TaskProgress:
    """Track progress of long-running tasks"""
    
    @staticmethod
    def create_task(task_id, task_type, total_items=0):
        """Create a new task progress tracker"""
        cache.set(f'task_{task_id}', {
            'task_id': task_id,
            'task_type': task_type,
            'status': 'PENDING',
            'progress': 0,
            'total': total_items,
            'current_item': '',
            'message': 'Starting...',
            'started_at': timezone.now().isoformat(),
            'completed_at': None,
            'result': None,
            'error': None,
        }, timeout=3600)  # 1 hour timeout
        
        return task_id
    
    @staticmethod
    def update_progress(task_id, progress, current_item='', message=''):
        """Update task progress"""
        task_data = cache.get(f'task_{task_id}')
        if task_data:
            task_data['progress'] = progress
            task_data['status'] = 'IN_PROGRESS'
            if current_item:
                task_data['current_item'] = current_item
            if message:
                task_data['message'] = message
            cache.set(f'task_{task_id}', task_data, timeout=3600)
    
    @staticmethod
    def complete_task(task_id, result=None, error=None):
        """Mark task as complete"""
        task_data = cache.get(f'task_{task_id}')
        if task_data:
            task_data['status'] = 'COMPLETED' if not error else 'FAILED'
            task_data['progress'] = 100
            task_data['completed_at'] = timezone.now().isoformat()
            task_data['result'] = result
            task_data['error'] = error
            task_data['message'] = 'Completed!' if not error else f'Error: {error}'
            cache.set(f'task_{task_id}', task_data, timeout=3600)
    
    @staticmethod
    def get_progress(task_id):
        """Get current task progress"""
        return cache.get(f'task_{task_id}')
    
    @staticmethod
    def cleanup_task(task_id):
        """Remove task from cache"""
        cache.delete(f'task_{task_id}')
