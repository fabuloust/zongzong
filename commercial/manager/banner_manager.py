from commercial.models import TopBanner


def get_top_banner_db():
    top_banner = TopBanner.objects.filter(is_online=True).order_by('-last_modified')[:1]
    return top_banner[0] if top_banner else None


def build_top_banner(banner):
    return {
        'title': banner.title,
        'activity_id': banner.activity_id,
        'image': banner.image
    }
