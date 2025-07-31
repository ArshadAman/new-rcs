from django.db import models
from django.conf import settings
from orders.models import Order
from django.utils import timezone

class Review(models.Model):
    RECOMMEND_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    recommend = models.CharField(max_length=3, choices=RECOMMEND_CHOICES)
    main_rating = models.PositiveSmallIntegerField(default=5)
    logistics_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    communication_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    website_usability_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    comment = models.TextField(blank=True)
    is_complete = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    is_flagged_red = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    auto_publish_at = models.DateTimeField(null=True, blank=True)
    reply = models.TextField(blank=True)  # Store/admin reply to review

    def save(self, *args, **kwargs):
        # If recommend is yes, auto 5-star and sub-ratings default to 5 if not given
        if self.recommend == 'yes':
            self.main_rating = 5
            if self.logistics_rating is None:
                self.logistics_rating = 5
            if self.communication_rating is None:
                self.communication_rating = 5
            if self.website_usability_rating is None:
                self.website_usability_rating = 5
            self.is_complete = True
            self.is_flagged_red = False
            self.is_published = True
            self.auto_publish_at = None
        else:
            # If NO, require sub-ratings and min 50 char comment for completion
            self.is_flagged_red = True
            if (self.logistics_rating and self.communication_rating and self.website_usability_rating and self.comment and len(self.comment.strip()) >= 50):
                self.is_complete = True
            else:
                self.is_complete = False
            # Set auto-publish time if not already set
            if not self.auto_publish_at:
                self.auto_publish_at = timezone.now() + timezone.timedelta(days=7)
            self.is_published = self.is_complete  # Only publish if complete
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Review by {self.user} for {self.order} - {'Recommend' if self.recommend == 'yes' else 'Not Recommend'}"
