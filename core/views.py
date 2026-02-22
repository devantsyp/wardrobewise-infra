from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render


def healthz(request):
    return JsonResponse({'status': 'ok'})


def index(request):
    return render(request, 'core/index.html')


@login_required
def wardrobe_placeholder(request):
    return render(request, 'core/wardrobe_placeholder.html')
