from celery import shared_task
from django.utils import timezone
from .models import Review

def auto_publish_reviews():
    now = timezone.now()
    reviews = Review.objects.filter(is_published=False, auto_publish_at__lte=now)
    for review in reviews:
        review.is_published = True
        review.save()

@shared_task
def periodic_auto_publish_reviews():
    auto_publish_reviews()
