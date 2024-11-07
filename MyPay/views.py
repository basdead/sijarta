from django.shortcuts import render
from .models import MyPayTransaction

def mypay_view(request):
    transactions = MyPayTransaction.objects.filter(guest=request.user)
    return render(request, 'mypay.html', {'transactions': transactions})