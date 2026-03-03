from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from wardrobe.forms import GarmentForm
from wardrobe.models import Garment


@login_required
def garment_list(request):
    garments = Garment.objects.filter(user=request.user)
    return render(request, 'wardrobe/wardrobe_list.html', {'garments': garments})


@login_required
def garment_detail(request, pk):
    garment = get_object_or_404(Garment, pk=pk, user=request.user)
    return render(request, 'wardrobe/garment_detail.html', {'garment': garment})


@login_required
def garment_create(request):
    if request.method == 'POST':
        form = GarmentForm(request.POST, request.FILES)
        if form.is_valid():
            # Step 1: Save without files so pk is assigned
            garment = form.save(commit=False)
            garment.user = request.user
            garment.save()

            # Step 2: Assign file fields and save again so upload_to has pk
            if 'garment_photo' in request.FILES:
                garment.garment_photo = request.FILES['garment_photo']
            if 'care_label_photo' in request.FILES:
                garment.care_label_photo = request.FILES['care_label_photo']
            garment.save()

            return redirect('wardrobe:garment_detail', pk=garment.pk)
    else:
        form = GarmentForm()
    return render(request, 'wardrobe/garment_form.html', {'form': form, 'action': 'create'})


@login_required
def garment_edit(request, pk):
    garment = get_object_or_404(Garment, pk=pk, user=request.user)
    if request.method == 'POST':
        form = GarmentForm(request.POST, request.FILES, instance=garment)
        if form.is_valid():
            # Delete old files before uploading replacements
            if 'garment_photo' in request.FILES and garment.garment_photo:
                garment.garment_photo.delete(save=False)
            if 'care_label_photo' in request.FILES and garment.care_label_photo:
                garment.care_label_photo.delete(save=False)
            form.save()
            return redirect('wardrobe:garment_detail', pk=garment.pk)
    else:
        form = GarmentForm(instance=garment)
    return render(request, 'wardrobe/garment_form.html', {'form': form, 'garment': garment, 'action': 'edit'})


@login_required
@require_POST
def garment_delete(request, pk):
    garment = get_object_or_404(Garment, pk=pk, user=request.user)
    garment.delete()
    return redirect('wardrobe:garment_list')
