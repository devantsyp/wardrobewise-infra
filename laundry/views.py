import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Exists, Max, OuterRef
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from laundry.models import Basket
from laundry.services.grouping import group_into_loads
from wardrobe.models import CATEGORY_CHOICES, CareAnalysis, Garment


@login_required
def basket_view(request):
    """GET /basket/ — show the basket selection page."""
    # Get or select active basket
    basket_id = request.GET.get('basket_id')
    basket = None
    plan_is_stale = False

    if basket_id:
        try:
            basket = Basket.objects.get(pk=basket_id, user=request.user)
            basket.save()  # touch last_used_at (auto_now)
        except Basket.DoesNotExist:
            basket = None

    if basket is None:
        # Fall back to most recently used basket
        basket = Basket.objects.filter(user=request.user).first()

    # Query analyzed garments only
    analyzed_garments = (
        Garment.objects.filter(user=request.user)
        .annotate(has_analysis=Exists(CareAnalysis.objects.filter(garment=OuterRef('pk'))))
        .filter(has_analysis=True)
        .select_related('care_analysis')
    )

    # All baskets for selector
    user_baskets = Basket.objects.filter(user=request.user)

    # Stale plan detection
    if basket and basket.saved_plan and basket.plan_saved_at:
        last_analysis_update = CareAnalysis.objects.filter(
            garment__pk__in=basket.garment_pks,
            garment__user=request.user,
        ).aggregate(latest=Max('updated_at'))['latest']
        plan_is_stale = (
            last_analysis_update is not None
            and last_analysis_update > basket.plan_saved_at
        )

    context = {
        'garments': analyzed_garments,
        'basket': basket,
        'baskets': user_baskets,
        'plan_is_stale': plan_is_stale,
        'categories': CATEGORY_CHOICES,
    }
    return render(request, 'laundry/basket.html', context)


@login_required
@require_POST
def plan_api(request):
    """POST /basket/api/plan/ — return a JSON laundry plan for selected garments."""
    try:
        body = json.loads(request.body)
        pks = [int(pk) for pk in body.get('garment_pks', [])]
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    if len(pks) < 2:
        return JsonResponse({'error': 'Select at least 2 garments'}, status=400)
    if len(pks) > 20:
        return JsonResponse({'error': 'Maximum 20 garments'}, status=400)

    garments = (
        Garment.objects.filter(pk__in=pks, user=request.user)
        .select_related('care_analysis')
    )

    garment_dicts = []
    for g in garments:
        try:
            a = g.care_analysis
        except CareAnalysis.DoesNotExist:
            continue
        garment_dicts.append({
            'pk': g.pk,
            'name': g.name,
            'photo_url': g.garment_photo.url if g.garment_photo else None,
            'category': g.get_category_display(),
            'color': g.color,
            'washing': a.washing,
            'drying': a.drying,
            'bleach': a.bleach,
            'is_delicate': a.is_delicate,
        })

    plan = group_into_loads(garment_dicts)
    return JsonResponse(plan)


@login_required
@require_POST
def basket_create(request):
    """POST /basket/create/ — create a new named basket (max 5)."""
    if Basket.objects.filter(user=request.user).count() >= 5:
        messages.error(request, "You can have at most 5 baskets.")
        return redirect('laundry:basket')

    name = request.POST.get('name', '').strip() or 'My Basket'
    name = name[:100]
    basket = Basket.objects.create(user=request.user, name=name)
    messages.success(request, f'Basket "{basket.name}" created.')
    return redirect(f'/basket/?basket_id={basket.pk}')


@login_required
@require_POST
def basket_rename(request, pk):
    """POST /basket/<pk>/rename/ — rename an existing basket."""
    basket = get_object_or_404(Basket, pk=pk, user=request.user)
    name = request.POST.get('name', '').strip() or basket.name
    name = name[:100]
    basket.name = name
    basket.save(update_fields=['name'])
    messages.success(request, f'Basket renamed to "{basket.name}".')
    return redirect(f'/basket/?basket_id={basket.pk}')


@login_required
@require_POST
def basket_delete(request, pk):
    """POST /basket/<pk>/delete/ — delete a basket."""
    basket = get_object_or_404(Basket, pk=pk, user=request.user)
    basket.delete()
    messages.success(request, 'Basket deleted.')
    return redirect('laundry:basket')


@login_required
@require_POST
def save_plan(request):
    """POST /basket/save-plan/ — persist a generated plan to the active basket."""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    basket_id = body.get('basket_id')
    plan = body.get('plan')
    basket = get_object_or_404(Basket, pk=basket_id, user=request.user)
    basket.saved_plan = plan
    basket.plan_saved_at = timezone.now()
    basket.save(update_fields=['saved_plan', 'plan_saved_at'])
    return JsonResponse({'status': 'saved'})


@login_required
@require_POST
def update_selection(request):
    """POST /basket/update-selection/ — persist selected garment PKs to active basket."""
    try:
        body = json.loads(request.body)
        basket_id = body.get('basket_id')
        garment_pks = [int(pk) for pk in body.get('garment_pks', [])]
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    basket = get_object_or_404(Basket, pk=basket_id, user=request.user)
    garment_pks = garment_pks[:20]
    basket.garment_pks = garment_pks
    basket.save(update_fields=['garment_pks'])
    return JsonResponse({'status': 'updated', 'count': len(garment_pks)})
