from django.utils import timezone

def monthly_review_count(user, is_reply = False):
    now = timezone.now()
    if is_reply:
        return user.reviews.filter(
            created_at__year=now.year,
            created_at__month=now.month,
            reply__isnull=False
        ).count()
    return user.reviews.filter(
        created_at__year=now.year,
        created_at__month=now.month
    ).count()


def is_trail_active(user):
    return user.trail_end and timezone.now <= user.trail_end

def is_plan_active(user):
    if user.plan_expiration is None:
        return True
    return user.plan_expiration and timezone.now <= user.plan_expiration