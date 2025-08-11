import django_filters
from .models import Review
from django.db import models

class ReviewFilter(django_filters.FilterSet):
    min_rating = django_filters.NumberFilter(field_name='main_rating', lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name='main_rating', lookup_expr='lte')
    logistics_rating = django_filters.NumberFilter(field_name='logistics_rating')
    communication_rating = django_filters.NumberFilter(field_name='communication_rating')
    website_usability_rating = django_filters.NumberFilter(field_name='website_usability_rating')
    recommend = django_filters.CharFilter(field_name='recommend')
    start_date = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    status = django_filters.CharFilter(method='filter_status')
    flagged = django_filters.BooleanFilter(field_name='is_flagged_red')
    replied = django_filters.BooleanFilter(method='filter_replied')
    search = django_filters.CharFilter(method='filter_search')
    sort_by = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created_at'),
            ('main_rating', 'main_rating'),
        )
    )

    class Meta:
        model = Review
        fields = []

    def filter_status(self, queryset, name, value):
        if value == 'published':
            return queryset.filter(is_published=True)
        elif value == 'unpublished':
            return queryset.filter(is_published=False)
        return queryset

    def filter_replied(self, queryset, name, value):
        if value:
            return queryset.exclude(reply='')
        else:
            return queryset.filter(reply='')
        return queryset

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            models.Q(order__order_id__icontains=value) |
            models.Q(order__customer_name__icontains=value) |
            models.Q(comment__icontains=value)
        )