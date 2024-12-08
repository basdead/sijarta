from django.shortcuts import render, redirect
from django.contrib import messages

# Create your views here.

def show_discount_page(request):
    """
    View for showing available discounts
    """
    # Check authentication
    is_authenticated = request.session.get('is_authenticated', False)
    user_type = request.session.get('user_type', None)
    
    if not is_authenticated or user_type != 'pelanggan':
        messages.error(request, 'Please log in as a customer to view discounts')
        return redirect('main:login_user')
        
    context = {
        # Add any context data needed for the template
    }
    
    return render(request, 'diskon.html', context)
