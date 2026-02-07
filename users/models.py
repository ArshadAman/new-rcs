import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class BusinessCategory(models.Model):
    CATEGORY_CHOICES = [
        ('medical', 'Medical Services / Dentistry'),
        ('beauty', 'Beauty Industry / Salon / Barbershop'),
        ('retail', 'Retail Store (Offline)'),
        ('ecommerce', 'Online Store (E-commerce)'),
        ('hotel', 'Hotel / Apartments / Guesthouse'),
        ('auto_service', 'Auto Service / Car Wash / Tire Shop'),
        ('car_dealership', 'Car Dealership / Auto Sales'),
        ('education', 'Education / Courses / Online School'),
        ('tourism', 'Tourism / Travel Agency / Excursions'),
        ('renovation', 'Renovation / Construction / Finishing'),
        ('it_services', 'IT Services / Development / Support'),
        ('logistics', 'Logistics / Delivery / Courier Service'),
        ('real_estate', 'Real Estate / Agency / Rental'),
        ('household', 'Household Services / Cleaning / Appliance Repair'),
        ('veterinary', 'Veterinary / Grooming / Pet Care'),
        ('financial', 'Financial / Insurance / Legal Services'),
        ('wellness', 'Health & Wellness (Fitness, Massage, Spa)'),
        ('photography', 'Photography / Video Production'),
        ('furniture', 'Furniture / Interior Design'),
        ('telecom', 'Telecommunications / Internet Providers'),
    ]
    
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10, default='🏢')
    questions = models.JSONField(default=list)  # Store category-specific questions
    
    def __str__(self):
        return self.display_name
    
    @classmethod
    def get_default_questions(cls):
        """Return default questions for each category"""
        return {
            'medical': [
                {'field': 'treatment_quality', 'label': 'Treatment Quality', 'required': True},
                {'field': 'staff_attentiveness', 'label': 'Staff Attentiveness', 'required': True},
                {'field': 'service_comfort', 'label': 'Service Comfort', 'required': True}
            ],
            'beauty': [
                {'field': 'service_result', 'label': 'Service Result', 'required': True},
                {'field': 'customer_care', 'label': 'Customer Care', 'required': True},
                {'field': 'atmosphere_comfort', 'label': 'Atmosphere / Comfort', 'required': True}
            ],
            'retail': [
                {'field': 'product_range', 'label': 'Product Range', 'required': True},
                {'field': 'staff_service', 'label': 'Staff Service', 'required': True},
                {'field': 'shopping_comfort', 'label': 'Shopping Comfort', 'required': True}
            ],
            'ecommerce': [
                {'field': 'website_usability', 'label': 'Website Usability', 'required': True},
                {'field': 'delivery_speed', 'label': 'Delivery Speed', 'required': True},
                {'field': 'product_quality', 'label': 'Product Quality', 'required': True},
                {'field': 'customer_support', 'label': 'Customer Support', 'required': True}
            ],
            'hotel': [
                {'field': 'cleanliness_comfort', 'label': 'Cleanliness & Comfort', 'required': True},
                {'field': 'staff_service', 'label': 'Staff Service', 'required': True},
                {'field': 'value_money', 'label': 'Value for Money', 'required': True}
            ],
            'auto_service': [
                {'field': 'work_quality', 'label': 'Work Quality', 'required': True},
                {'field': 'service_speed', 'label': 'Service Speed', 'required': True},
                {'field': 'price_transparency', 'label': 'Price Transparency', 'required': True}
            ],
            'car_dealership': [
                {'field': 'vehicle_quality', 'label': 'Vehicle Quality', 'required': True},
                {'field': 'sales_consultant', 'label': 'Sales Consultant Service', 'required': True},
                {'field': 'deal_transparency', 'label': 'Transparency of Deal', 'required': True},
                {'field': 'delivery_process', 'label': 'Delivery / Handover Process', 'required': True}
            ],
            'education': [
                {'field': 'teaching_quality', 'label': 'Teaching Quality', 'required': True},
                {'field': 'material_usefulness', 'label': 'Usefulness of Material', 'required': True},
                {'field': 'learning_convenience', 'label': 'Learning Convenience', 'required': True}
            ],
            'tourism': [
                {'field': 'trip_organization', 'label': 'Trip Organization', 'required': True},
                {'field': 'manager_service', 'label': 'Manager Service', 'required': True},
                {'field': 'expectations_match', 'label': 'Match with Expectations', 'required': True}
            ],
            'renovation': [
                {'field': 'work_quality', 'label': 'Work Quality', 'required': True},
                {'field': 'deadline_compliance', 'label': 'Deadline Compliance', 'required': True},
                {'field': 'cleanliness_accuracy', 'label': 'Cleanliness & Accuracy', 'required': True}
            ],
            'it_services': [
                {'field': 'result_quality', 'label': 'Result Quality', 'required': True},
                {'field': 'response_speed', 'label': 'Response Speed', 'required': True},
                {'field': 'communication_quality', 'label': 'Communication Quality', 'required': True}
            ],
            'logistics': [
                {'field': 'delivery_speed', 'label': 'Delivery Speed', 'required': True},
                {'field': 'shipment_condition', 'label': 'Shipment Condition', 'required': True},
                {'field': 'delivery_convenience', 'label': 'Delivery Convenience', 'required': True}
            ],
            'real_estate': [
                {'field': 'agent_professionalism', 'label': 'Agent Professionalism', 'required': True},
                {'field': 'deal_transparency', 'label': 'Transparency of Deal', 'required': True},
                {'field': 'property_accuracy', 'label': 'Property Accuracy', 'required': True}
            ],
            'household': [
                {'field': 'service_quality', 'label': 'Service Quality', 'required': True},
                {'field': 'responsiveness', 'label': 'Responsiveness', 'required': True},
                {'field': 'price_value', 'label': 'Price / Value', 'required': True}
            ],
            'veterinary': [
                {'field': 'care_quality', 'label': 'Care Quality', 'required': True},
                {'field': 'pet_attitude', 'label': 'Attitude Toward Pet', 'required': True},
                {'field': 'booking_convenience', 'label': 'Booking Convenience', 'required': True}
            ],
            'financial': [
                {'field': 'staff_competence', 'label': 'Staff Competence', 'required': True},
                {'field': 'terms_transparency', 'label': 'Transparency of Terms', 'required': True},
                {'field': 'resolution_speed', 'label': 'Resolution Speed', 'required': True}
            ],
            'wellness': [
                {'field': 'service_quality', 'label': 'Service Quality', 'required': True},
                {'field': 'staff_professionalism', 'label': 'Staff Professionalism', 'required': True},
                {'field': 'atmosphere_comfort', 'label': 'Atmosphere & Comfort', 'required': True}
            ],
            'photography': [
                {'field': 'result_quality', 'label': 'Result Quality', 'required': True},
                {'field': 'creativity_approach', 'label': 'Creativity & Approach', 'required': True},
                {'field': 'communication_punctuality', 'label': 'Communication & Punctuality', 'required': True}
            ],
            'furniture': [
                {'field': 'product_quality', 'label': 'Product Quality', 'required': True},
                {'field': 'design_functionality', 'label': 'Design & Functionality', 'required': True},
                {'field': 'delivery_assembly', 'label': 'Delivery & Assembly', 'required': True}
            ],
            'telecom': [
                {'field': 'connection_quality', 'label': 'Connection Quality', 'required': True},
                {'field': 'customer_support', 'label': 'Customer Support', 'required': True},
                {'field': 'price_performance', 'label': 'Price / Performance', 'required': True}
            ]
        }

class CustomUser(AbstractUser):
    business_name = models.CharField(max_length=100, blank=True)
    website_url = models.URLField(max_length=200, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=50, blank=True)
    widget_clicks = models.PositiveIntegerField(default=0)
    marketing_banner = models.ImageField(upload_to='marketing_banners/', null=True, blank=True)
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    email = models.EmailField(unique=True)  # Make email unique
    business_category = models.ForeignKey(BusinessCategory, on_delete=models.SET_NULL, null=True, blank=True)
    PLAN_CHOICES = [
        ('basic', 'Basic Level'),
        ('advanced', 'Advanced Level'),
        ('pro', 'Pro Level'),
        ('unique', 'Unique Level'),
        ('expired', 'Expired'),
    ]
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES, default='basic')
    plan_expiration = models.DateTimeField(null=True, blank=True)
    monthly_review_count = models.PositiveIntegerField(default=0)  # Online reviews
    monthly_reply_count = models.PositiveIntegerField(default=0)
    monthly_offline_review_count = models.PositiveIntegerField(default=0)  # Offline reviews (separate counter)
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    
    # Custom limits for 'unique' plan (set manually in admin)
    max_branches = models.PositiveIntegerField(null=True, blank=True, help_text="Max branches for unique plan")
    online_limit_per_month = models.PositiveIntegerField(null=True, blank=True, help_text="Online review limit for unique plan")
    offline_limit_per_month = models.PositiveIntegerField(null=True, blank=True, help_text="Offline review limit for unique plan")

    def __str__(self):
        return self.username
    
    def get_plan_limits(self):
        """Get plan limits based on user's plan"""
        PLAN_LIMITS = {
            'basic': {'max_branches': 0, 'online_limit': 100, 'offline_limit': 0},  # No offline for basic
            'advanced': {'max_branches': 5, 'online_limit': 400, 'offline_limit': 10000},
            'pro': {'max_branches': 20, 'online_limit': 1000, 'offline_limit': 50000},
            'unique': {
                'max_branches': self.max_branches or 50,
                'online_limit': self.online_limit_per_month or 5000,
                'offline_limit': self.offline_limit_per_month or 100000,
            },
            'expired': {'max_branches': 0, 'online_limit': 0, 'offline_limit': 0},
        }
        return PLAN_LIMITS.get(self.plan, PLAN_LIMITS['basic'])

class MonthlyRating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    year = models.IntegerField()
    month = models.IntegerField()
    average_rating = models.FloatField()

    class Meta:
        unique_together = ('user', 'year', 'month')