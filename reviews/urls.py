from django.urls import path
from .views import iframe_widget, review_form, public_reviews, user_reviews_api, reply_to_negative_review

urlpatterns = [
    path('widget/iframe/<uuid:user_id>/', iframe_widget, name='iframe_widget'),
    path('review/<uuid:token>/', review_form, name='review_form'),
    path('public-reviews/<uuid:user_id>/', public_reviews, name='public_reviews'),
    path('my-reviews/', user_reviews_api, name='user_reviews_api'),
    path('reply-to-negative/<uuid:review_id>/', reply_to_negative_review, name='reply_to_negative_review'),
]