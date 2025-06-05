from decimal import Decimal

from django.core.management.base import BaseCommand

from ems.djangoapps.product.models import Product, ProductType, Category
from ems.djangoapps.warehouse.models import ProductVariant


class Command(BaseCommand):
    help = 'Creates test data for development'

    def handle(self, *args, **options):
        # Create a product type
        product_type, _ = ProductType.objects.get_or_create(
            name='Test Type',
            slug='test-type',
            has_variants=True
        )

        # Create a category
        category, _ = Category.objects.get_or_create(
            name='Test Category',
            slug='test-category'
        )

        # Create some products
        for i in range(1, 4):
            product = Product.objects.create(
                name=f'Test Product {i}',
                slug=f'test-product-{i}',
                description=f'This is test product {i}',
                product_type=product_type,
                category=category,
                price=Decimal(f'{i}9.99'),
                is_active=True,
                is_featured=True
            )

            # Create variants for each product
            for j in range(1, 3):
                ProductVariant.objects.create(
                    name=f'Variant {j} of {product.name}',
                    product=product,
                    price_amount=Decimal(f'{i}{j}.99'),
                    track_inventory=True
                )

        self.stdout.write(self.style.SUCCESS('Successfully created test data'))
