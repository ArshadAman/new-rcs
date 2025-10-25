from django.core.management.base import BaseCommand
from users.models import BusinessCategory

class Command(BaseCommand):
    help = 'Populate business categories with default data'

    def handle(self, *args, **options):
        categories_data = [
            ('medical', 'Medical Services / Dentistry', '🏥'),
            ('beauty', 'Beauty Industry / Salon / Barbershop', '💇‍♀️'),
            ('retail', 'Retail Store (Offline)', '🛍️'),
            ('ecommerce', 'Online Store (E-commerce)', '💻'),
            ('hotel', 'Hotel / Apartments / Guesthouse', '🏨'),
            ('auto_service', 'Auto Service / Car Wash / Tire Shop', '🚗'),
            ('car_dealership', 'Car Dealership / Auto Sales', '🚘'),
            ('education', 'Education / Courses / Online School', '🧑‍🏫'),
            ('tourism', 'Tourism / Travel Agency / Excursions', '🧳'),
            ('renovation', 'Renovation / Construction / Finishing', '🏠'),
            ('it_services', 'IT Services / Development / Support', '💻'),
            ('logistics', 'Logistics / Delivery / Courier Service', '🚚'),
            ('real_estate', 'Real Estate / Agency / Rental', '🏢'),
            ('household', 'Household Services / Cleaning / Appliance Repair', '🧰'),
            ('veterinary', 'Veterinary / Grooming / Pet Care', '🐶'),
            ('financial', 'Financial / Insurance / Legal Services', '🧾'),
            ('wellness', 'Health & Wellness (Fitness, Massage, Spa)', '🧴'),
            ('photography', 'Photography / Video Production', '📸'),
            ('furniture', 'Furniture / Interior Design', '🪑'),
            ('telecom', 'Telecommunications / Internet Providers', '📞'),
        ]

        for name, display_name, icon in categories_data:
            category, created = BusinessCategory.objects.get_or_create(
                name=name,
                defaults={
                    'display_name': display_name,
                    'icon': icon,
                    'questions': BusinessCategory.get_default_questions().get(name, [])
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {display_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Category already exists: {display_name}')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully populated business categories!')
        )

