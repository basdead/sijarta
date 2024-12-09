from django.shortcuts import render, redirect
from django.contrib import messages
from utils.query import get_db_connection
import logging

logger = logging.getLogger(__name__)

# Create your views here.

def show_my_works(request):
    """
    View for showing worker's assigned jobs
    """
    # Check authentication
    is_authenticated = request.session.get('is_authenticated', False)
    user_type = request.session.get('user_type', None)
    user_id = request.session.get('user_id', None)
    
    if not is_authenticated or not user_type or not user_id:
        messages.error(request, 'Please log in to continue')
        return redirect('main:login_user')
    
    if user_type != 'pekerja':
        messages.error(request, 'Only workers can access this page')
        return redirect('main:show_home_page')

    return render(request, 'my_works.html')

def show_work_status(request):
    """
    View for managing work status
    """
    # Check authentication
    is_authenticated = request.session.get('is_authenticated', False)
    user_type = request.session.get('user_type', None)
    user_id = request.session.get('user_id', None)
    
    if not is_authenticated or not user_type or not user_id:
        messages.error(request, 'Please log in to continue')
        return redirect('main:login_user')
    
    if user_type != 'pekerja':
        messages.error(request, 'Only workers can access this page')
        return redirect('main:show_home_page')

    return render(request, 'work_status.html')
