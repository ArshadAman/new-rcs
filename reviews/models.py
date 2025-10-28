from django.db import models
from django.conf import settings
from orders.models import Order
from django.utils import timezone
import uuid

class Review(models.Model):
    RECOMMEND_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    manual_order_id = models.CharField(max_length=100, blank=True, null=True)
    manual_customer_name = models.CharField(max_length=200, blank=True, null=True)
    manual_customer_email = models.CharField(max_length=200, blank=True, null=True)
    recommend = models.CharField(max_length=3, choices=RECOMMEND_CHOICES)
    main_rating = models.PositiveSmallIntegerField(default=5)
    logistics_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    communication_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    website_usability_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    # Dynamic category-specific ratings stored as JSON
    category_ratings = models.JSONField(default=dict, blank=True)
    comment = models.TextField(blank=True)
    is_complete = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    is_flagged_red = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    auto_publish_at = models.DateTimeField(null=True, blank=True)
    reply = models.TextField(blank=True)  # Store/admin reply to review
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)

    def save(self, *args, **kwargs):
        # If recommend is yes, calculate main_rating from sub-ratings
        if self.recommend == 'yes':
            # Set category-specific ratings to 5 if not provided (do this BEFORE calculating main_rating)
            if self.user.business_category:
                from users.models import BusinessCategory
                category_questions = BusinessCategory.get_default_questions().get(self.user.business_category.name, [])
                for question in category_questions:
                    field_name = question['field']
                    if field_name not in self.category_ratings or self.category_ratings[field_name] is None:
                        self.category_ratings[field_name] = 5
            
            # Default standard sub-ratings to 5 if not provided
            if self.logistics_rating is None:
                self.logistics_rating = 5
            if self.communication_rating is None:
                self.communication_rating = 5
            if self.website_usability_rating is None:
                self.website_usability_rating = 5
            
            # Calculate main_rating as average of sub-ratings
            ratings = []
            
            # If business category exists with category ratings, use those
            if self.category_ratings and len(self.category_ratings) > 0:
                # Use only category-specific ratings
                ratings = [int(v) for v in self.category_ratings.values() if v is not None and v != '']
            else:
                # Use standard sub-ratings
                if self.logistics_rating is not None:
                    ratings.append(int(self.logistics_rating))
                if self.communication_rating is not None:
                    ratings.append(int(self.communication_rating))
                if self.website_usability_rating is not None:
                    ratings.append(int(self.website_usability_rating))
            
            if ratings:
                self.main_rating = sum(ratings) / len(ratings)
            
            self.is_complete = True
            self.is_flagged_red = False
            self.is_published = True
            self.auto_publish_at = None
        else:
            # If NO, require min 50 char comment for completion
            self.is_flagged_red = True
            if (self.comment and len(self.comment.strip()) >= 50):
                self.is_complete = True
            else:
                self.is_complete = False
            # Set auto-publish time if not already set
            if not self.auto_publish_at:
                self.auto_publish_at = timezone.now() + timezone.timedelta(days=7)
            self.is_published = self.is_complete  # Only publish if complete
        super().save(*args, **kwargs)

    def __str__(self):
        if self.order_id:
            order_info = f" for {self.order}"
        else:
            order_info = " (Manual Review)"
        return f"Review by {self.user}{order_info} - {'Recommend' if self.recommend == 'yes' else 'Not Recommend'}"
