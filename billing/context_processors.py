from .models import ShopProfile


def shop_profile_context(request):
    """Make shop profile available in all templates."""
    try:
        profile = ShopProfile.get_profile()
    except Exception:
        profile = None
    return {'shop_profile': profile}
