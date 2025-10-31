from django.test import TestCase
from django.urls import reverse

from .models import Category, Product, ProductSpecification


class CatalogTests(TestCase):
    def setUp(self):
        self.cat_gaming = Category.objects.create(
            name="Gaming", slug="gaming", category_type="gaming"
        )
        self.cat_pc = Category.objects.create(
            name="Computadores", slug="computadores", category_type="computadores"
        )

        self.prod_game = Product.objects.create(
            name="Juego Pro", slug="juego-pro", price=100000,
            category=self.cat_gaming, is_active=True, stock_quantity=5
        )
        ProductSpecification.objects.create(
            product=self.prod_game, platform_compatibility="PC", genre="Acción", age_rating="+12"
        )

        self.prod_pc = Product.objects.create(
            name="Laptop X", slug="laptop-x", price=3500000,
            category=self.cat_pc, is_active=True, stock_quantity=2
        )
        ProductSpecification.objects.create(
            product=self.prod_pc, processor="Intel i7", ram_memory="16GB", storage_type="SSD", storage_capacity="512GB"
        )

    def test_product_list_filter_gaming(self):
        url = reverse("catalog:product_list") + "?gaming=true"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # Debe incluir producto gaming y no el PC si se filtra por gaming
        names = [p.name for p in resp.context["object_list"]]
        self.assertIn("Juego Pro", names)
        # No garantiza exclusión si otras categorías no se filtran, pero en dataset simple:
        self.assertNotIn("Laptop X", names)

    def test_get_main_specs(self):
        specs_g = self.prod_game.get_main_specs()
        self.assertIn("Plataforma", specs_g)
        self.assertEqual(specs_g["Plataforma"], "PC")

        specs_pc = self.prod_pc.get_main_specs()
        self.assertIn("Procesador", specs_pc)
        self.assertEqual(specs_pc["Procesador"], "Intel i7")

