from django.test import TestCase
from decimal import Decimal
import random, string
from django.contrib.auth import get_user_model
from django.apps import apps

def _rand_word(n=6):
    rng = random.Random(42)
    return "".join(rng.choice(string.ascii_letters) for _ in range(n))

class TestFlowIdempotency(TestCase):
    @classmethod
    def setUpTestData(cls):
        # RNG fijo
        cls.rng = random.Random(1234)

        # ---- Usuario ----
        User = get_user_model()
        cls.user = User.objects.create_user(
            username=f"buyer_{_rand_word()}",
            email=f"{_rand_word()}@test.com",
            password="pass1234",
        )

        # ---- Modelos externos ----
        cls.Product = apps.get_model("catalog", "Product")
        cls.Category = apps.get_model("catalog", "Category")
        cls.Order = apps.get_model("order", "Order")
        cls.OrderItem = apps.get_model("order", "OrderItem")

        # Helpers para usar solo campos existentes
        def field_names(model):
            # Solo campos de base (excluye M2M reverse, etc.)
            names = set()
            for f in model._meta.get_fields():
                # f.concrete True = FK/PK/normal; omitimos reverse relations
                if getattr(f, "concrete", False):
                    names.add(f.name)
            return names

        product_fields = field_names(cls.Product)
        category_fields = field_names(cls.Category)

        # ---- Category (mínimos) ----
        cat_kwargs = {}
        if "name" in category_fields:
            cat_kwargs["name"] = "Perifericos"
        if "slug" in category_fields:
            cat_kwargs["slug"] = "perifericos"
        # Agrega más si tu modelo lo exige:
        # if "is_active" in category_fields: cat_kwargs["is_active"] = True
        cls.category = cls.Category.objects.create(**cat_kwargs)

        # ---- Datos aleatorios coherentes ----
        price_int = cls.rng.randint(50_000, 250_000)  # ENTERO en COP
        price = Decimal(price_int)                    # como Decimal para campos DecimalField
        stock_quantity = cls.rng.randint(5, 20)
        cls.qty = cls.rng.randint(1, 3)

        # ---- Product (solo lo que exista) ----
        prod_kwargs = {}
        if "name" in product_fields:
            prod_kwargs["name"] = f"Teclado {_rand_word()}"
        if "slug" in product_fields:
            prod_kwargs["slug"] = f"teclado-{_rand_word(4)}"
        if "price" in product_fields:
            prod_kwargs["price"] = price
        if "stock_quantity" in product_fields:
            prod_kwargs["stock_quantity"] = stock_quantity
        if "category" in product_fields:
            prod_kwargs["category"] = cls.category
        if "is_active" in product_fields:
            prod_kwargs["is_active"] = True
        if "sku" in product_fields:
            prod_kwargs["sku"] = f"SKU-{cls.rng.randint(10000, 99999)}"
        if "short_description" in product_fields:
            prod_kwargs["short_description"] = ""
        if "description" in product_fields:
            prod_kwargs["description"] = ""

        cls.product = cls.Product.objects.create(**prod_kwargs)

        # ---- Order + Items ----
        total_amount = (prod_kwargs.get("price", price) or price) * cls.qty
        order_kwargs = {"user": cls.user}
        # Ajusta si tu modelo tiene otros NOT NULL (shipping_address, etc.)
        order_fields = field_names(cls.Order)
        # status/total_amount si existen
        if "status" in order_fields:
            order_kwargs["status"] = "pending"
        if "total_amount" in order_fields:
            order_kwargs["total_amount"] = total_amount

        cls.order = cls.Order.objects.create(**order_kwargs)

        oi_kwargs = {"order": cls.order, "product": cls.product, "quantity": cls.qty}
        cls.OrderItem.objects.create(**oi_kwargs)

        # URL de proceso
        from django.urls import reverse
        cls.process_url = reverse("payment:process", args=[cls.order.id])

        # Tarjeta válida (Luhn OK y no cae en reglas de rechazo del simulador)
        valid_cards = ["4111111111111111", "4012888888881881", "5555555555554444"]
        cls.form_ok = {
            "cardholder_name": f"{_rand_word()} {_rand_word()}",
            "card_number": cls.rng.choice(valid_cards),
            "expiry": f"{cls.rng.randint(10,12):02d}/{cls.rng.randint(30,36)}",
            "cvv": f"{cls.rng.randint(100,999)}",
            "zip_code": f"05{cls.rng.randint(0,999):03d}1",
        }
