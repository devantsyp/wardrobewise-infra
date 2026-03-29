from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from wardrobe.forms import GarmentForm
from wardrobe.models import CareAnalysis, Garment
from wardrobe.services.analysis import (
    AnalysisError,
    BudgetGuardTripped,
    RateLimitExceeded,
    analyze_care_label,
)


@login_required
def garment_list(request):
    from django.db.models import Exists, OuterRef
    garments = Garment.objects.filter(user=request.user).annotate(
        has_analysis=Exists(CareAnalysis.objects.filter(garment=OuterRef('pk')))
    )
    return render(request, 'wardrobe/wardrobe_list.html', {'garments': garments})


@login_required
def garment_detail(request, pk):
    garment = get_object_or_404(Garment, pk=pk, user=request.user)
    try:
        analysis = garment.care_analysis
    except CareAnalysis.DoesNotExist:
        analysis = None
    context = {'garment': garment, 'analysis': analysis}
    return render(request, 'wardrobe/garment_detail.html', context)


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
            updated = form.save(commit=False)
            if 'garment_photo' in request.FILES:
                updated.garment_photo = request.FILES['garment_photo']
            if 'care_label_photo' in request.FILES:
                updated.care_label_photo = request.FILES['care_label_photo']
            updated.save()
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


@login_required
@require_POST
def analyze_care_label_view(request, pk):
    garment = get_object_or_404(Garment, pk=pk, user=request.user)

    if not garment.care_label_photo:
        messages.error(request, "Please upload a care label photo first.")
        return redirect('wardrobe:garment_detail', pk=pk)

    try:
        analyze_care_label(garment, request.user)
        messages.success(request, "Care instructions analyzed successfully.")
    except RateLimitExceeded:
        messages.error(request, "daily_limit_reached")
    except BudgetGuardTripped:
        messages.error(request, "budget_guard_tripped")
    except AnalysisError:
        messages.error(request, "analysis_failed")
    return redirect('wardrobe:garment_detail', pk=pk)


@login_required
def edit_instructions_view(request, pk):
    garment = get_object_or_404(Garment, pk=pk, user=request.user)
    try:
        analysis = garment.care_analysis
    except CareAnalysis.DoesNotExist:
        messages.error(request, "No analysis to edit.")
        return redirect('wardrobe:garment_detail', pk=pk)

    if request.method == 'POST':
        from wardrobe.forms import CareInstructionsForm
        form = CareInstructionsForm(request.POST, instance=analysis)
        if form.is_valid():
            form.save()
            analysis.is_user_edited = True
            analysis.save(update_fields=['is_user_edited'])
            messages.success(request, "Instructions updated.")
            return redirect('wardrobe:garment_detail', pk=pk)
    else:
        from wardrobe.forms import CareInstructionsForm
        form = CareInstructionsForm(instance=analysis)

    return render(request, 'wardrobe/garment_detail.html', {
        'garment': garment,
        'analysis': analysis,
        'editing': True,
        'edit_form': form,
    })


@login_required
@require_POST
def reset_instructions_view(request, pk):
    garment = get_object_or_404(Garment, pk=pk, user=request.user)
    try:
        analysis = garment.care_analysis
    except CareAnalysis.DoesNotExist:
        messages.error(request, "No analysis to reset.")
        return redirect('wardrobe:garment_detail', pk=pk)

    analysis.washing = analysis.ai_washing
    analysis.drying = analysis.ai_drying
    analysis.ironing = analysis.ai_ironing
    analysis.bleach = analysis.ai_bleach
    analysis.is_delicate = analysis.ai_is_delicate
    analysis.summary = analysis.ai_summary
    analysis.personal_notes = ''
    analysis.is_user_edited = False
    analysis.save()
    messages.success(request, "Instructions reset to AI version.")
    return redirect('wardrobe:garment_detail', pk=pk)


@login_required
@require_POST
def delete_analysis_view(request, pk):
    garment = get_object_or_404(Garment, pk=pk, user=request.user)
    try:
        analysis = garment.care_analysis
        analysis.delete()
        messages.success(request, "Analysis deleted.")
    except CareAnalysis.DoesNotExist:
        messages.error(request, "No analysis to delete.")
    return redirect('wardrobe:garment_detail', pk=pk)
