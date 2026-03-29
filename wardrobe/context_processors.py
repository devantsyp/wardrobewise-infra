from wardrobe.services.analysis import get_daily_count, budget_guard_active, DAILY_LIMIT


def daily_usage_counter(request):
    """Inject daily usage count into template context.

    Only runs the DB query on wardrobe namespace pages to avoid
    unnecessary queries on admin, auth, and other pages.
    """
    if not request.user.is_authenticated:
        return {}

    # Only inject on wardrobe namespace pages
    try:
        if request.resolver_match is None or request.resolver_match.app_name != 'wardrobe':
            return {}
    except AttributeError:
        return {}

    count = get_daily_count(request.user)
    return {
        'daily_usage_count': count,
        'daily_usage_limit': DAILY_LIMIT,
        'budget_guard_tripped': budget_guard_active(),
    }
