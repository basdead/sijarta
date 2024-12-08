from django.shortcuts import render

# Create your views here.

def show_mypay(request):
    return render(request, "mypay.html")
