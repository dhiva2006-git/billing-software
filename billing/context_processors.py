from .models import ShopProfile


def shop_profile_context(request):
    """Make shop profile available in all templates."""
    profile = None
    if request.user.is_authenticated:
        try:
            profile = request.user.userprofile.shop
        except Exception:
            pass
    return {'shop_profile': profile}
