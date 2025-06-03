# E-commerce Management System (EMS)

## Overview

The E-commerce Management System (EMS) is the core shopping platform of Quickcart, responsible for product catalog management, inventory control, order processing, and the customer-facing shopping experience. EMS provides a comprehensive set of APIs and services that power the online store.

## Key Features

- **Product Catalog Management**: Create, update, and organize products, variants, categories, and attributes
- **Inventory Management**: Multi-warehouse inventory tracking with support for:
  - Real-time stock levels
  - Preorders
  - Backorders
  - Reservations
- **Order Processing**: Complete order lifecycle management from creation to fulfillment
- **Checkout System**: Flexible checkout flows with support for multiple payment methods
- **Pricing & Discounts**: Advanced pricing rules and promotional capabilities
- **Customer Accounts**: User registration, profiles, and order history
- **Search & Filtering**: Product search and faceted filtering

## Architecture

EMS follows a Django-based architecture with modular applications organized by business domain:

```
ems/
├── djangoapps/         # Django applications
│   ├── account/        # User accounts and authentication
│   ├── branding/       # Site branding and theming
│   ├── checkout/       # Checkout process and payments
│   ├── core/           # Core functionality and settings
│   ├── discounts/      # Promotions and discount rules
│   ├── order/          # Order management
│   ├── product/        # Product catalog
│   ├── shipping/       # Shipping methods and carriers
│   ├── tax/            # Tax calculation
│   └── warehouse/      # Inventory management
├── envs/               # Environment-specific settings
├── static/             # Static assets
└── templates/          # HTML templates
```

### Design Decisions

- **Modularity**: Each functional area is implemented as a separate Django app for maintainability
- **Service Layer**: Business logic is encapsulated in service classes to separate from view logic
- **REST API**: All functionality is exposed through RESTful APIs
- **Event-Driven**: Uses signals for loose coupling between components
- **Task Queue**: Asynchronous processing for long-running operations

## Module Documentation

### Core Modules

#### Product Catalog (`ems/djangoapps/product/`)

The product catalog module manages product information, categories, and variants. See the [Product README](djangoapps/product/README.md) for details.

#### Warehouse Management (`ems/djangoapps/warehouse/`)

The warehouse module handles inventory across multiple locations. See the [Warehouse README](djangoapps/warehouse/README.md) for details.

#### Order Management (`ems/djangoapps/order/`)

The order module processes customer orders through their complete lifecycle:

- Order creation
- Payment processing
- Fulfillment
- Returns and refunds

#### Checkout (`ems/djangoapps/checkout/`)

The checkout module manages the shopping cart and checkout process:

- Cart management
- Shipping method selection
- Payment processing
- Order submission

## Usage Examples

### Creating a Product

```python
from ems.djangoapps.product.models import Product, ProductType
from decimal import Decimal

# Create a product type
product_type = ProductType.objects.create(name="T-Shirt")

# Create a product
product = Product.objects.create(
    name="Cotton T-Shirt",
    product_type=product_type,
    price=Decimal("19.99"),
    description="Comfortable cotton t-shirt"
)
```

### Managing Inventory

```python
from ems.djangoapps.warehouse.models import Stock, Warehouse
from ems.djangoapps.product.models import ProductVariant

# Get a product variant and warehouse
variant = ProductVariant.objects.get(sku_key="example-sku")
warehouse = Warehouse.objects.get(slug="main-warehouse")

# Create or update stock
stock, created = Stock.objects.get_or_create(
    warehouse=warehouse,
    product_variant_id=variant.sku_key,
    defaults={
        "quantity": 100
    }
)

# If stock already existed, update quantity
if not created:
    stock.quantity += 50
    stock.save()
```

### Processing an Order

```python
from ems.djangoapps.order.interfaces.order_service import OrderService
from ems.djangoapps.checkout.models import Checkout

# Get a completed checkout
checkout = Checkout.objects.get(token="checkout-token")

# Create an order from checkout
order_service = OrderService()
order = order_service.create_order_from_checkout(checkout)

# Process the order
order_service.process_order(order)
```

## Development

### Setting Up a Development Environment

1. Create a virtual environment and install dependencies
2. Configure the EMS environment variables
3. Run migrations: `python manage.py migrate`
4. Start the development server: `python manage.py runserver`

### Running Tests

Run the EMS test suite:

```bash
pytest ems/
```

## Extending EMS

EMS is designed to be extensible through:

1. Custom Django apps that integrate with the core modules
2. Signal handlers for key events
3. Custom service implementations
4. Middleware for request/response processing

See the [Contributing Guidelines](../README.md#contributing) for more details.

