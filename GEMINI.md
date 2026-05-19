# LadiesDream - E-commerce Platform

## Project Overview
LadiesDream is a comprehensive e-commerce platform built with Django. It features a robust product management system with support for variants (size and color), categories, and suppliers. The platform includes customer accounts, a shopping cart, a wishlist, order processing with Nova Poshta integration, and a discount/promo code system.

### Main Technologies
- **Backend:**  [Django 5.2.7](https://www.djangoproject.com/), 
                [PostgreSQL](https://www.postgresql.org/), 
                [Redis](https://redis.io/) (for caching and sessions).

- **Frontend:** [Tailwind CSS](https://tailwindcss.com/) (compiled via npm), 
                [HTMX](https://htmx.org/) for dynamic interactions.
                
- **Integrations:**
  - [Nova Poshta API](https://devcenter.novaposhta.ua/) for delivery services.
  - [LiqPay](https://www.liqpay.ua/) for payment processing.
  - [django-allauth](https://django-allauth.readthedocs.io/) for authentication.
  - [django-ckeditor](https://github.com/django-ckeditor/django-ckeditor) for rich text content.

## Project Structure
- `accounts/`: User registration, profiles, and custom authentication logic.
- `cart/`: Shopping cart and wishlist functionality.
- `discounts/`: Management of promo codes and product-specific discounts.
- `main/`: Core application containing products, categories, suppliers, and home page logic.
- `orders/`: Checkout process, order management, and payment/delivery integrations.
- `reviews/`: Product review and rating system.
- `shop/`: Project configuration, settings, and root URL routing.
- `admin_site.py`: Custom Django Admin implementation with a dashboard for sales statistics.

## Building and Running

### Prerequisites
- Python 3.x
- Node.js & npm (for Tailwind CSS)
- Docker (optional, for Postgres and Redis)

### Key Commands
The project uses a `Makefile` to simplify common tasks:

- **Setup Dependencies:**
  ```bash
  make install      # Install Python dependencies
  npm install       # Install Node.js dependencies
  ```
- **Infrastructure:**
  ```bash
  make up           # Start PostgreSQL and Redis via Docker Compose
  ```
- **Development Server:**
  ```bash
  make run          # Start the Django development server
  npm run css:watch # Start Tailwind CSS watcher (in a separate terminal)
  ```
- **Database Management:**
  ```bash
  make migrations   # Create new migrations
  make migrate      # Apply migrations
  ```

## Development Conventions

### Coding Style
- Follow standard Django and PEP 8 conventions.
- Use the custom `admin_site` for administrative tasks to leverage the dashboard.
- Localization is primarily in Ukrainian (`uk`), and the timezone is `Europe/Kyiv`.

### Frontend
- Styles are managed via Tailwind CSS. Edit `shop/static/main/tailwind_input.css` and ensure the watcher is running to update `tailwind_output.css`.
- Use HTMX for partial page updates to improve user experience without full reloads.

### Configuration
- Environment variables are managed via `.env` (loaded by `python-dotenv`).
- Key variables include `SECRET_KEY`, `DEBUG`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `NP_API_KEY`, etc.
