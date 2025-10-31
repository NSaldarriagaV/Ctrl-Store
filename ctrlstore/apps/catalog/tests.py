from django.test import TestCase
from django.urls import reverse

from .models import Category, Product, ProductSpecification


class CatalogTests(TestCase):
    """Pruebas unitarias para el catálogo de productos."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        # Crear categorías
        self.cat_gaming = Category.objects.create(
            name="Gaming", slug="gaming", category_type="gaming"
        )
        self.cat_pc = Category.objects.create(
            name="Computadores", slug="computadores", category_type="computadores"
        )
        self.cat_celulares = Category.objects.create(
            name="Celulares", slug="celulares", category_type="celulares_tablets"
        )

        # Crear producto gaming con especificaciones
        self.prod_game = Product.objects.create(
            name="Juego Pro",
            slug="juego-pro",
            price=100000,
            category=self.cat_gaming,
            is_active=True,
            stock_quantity=5,
        )
        ProductSpecification.objects.create(
            product=self.prod_game,
            platform_compatibility="PC",
            genre="Acción",
            age_rating="+12",
            multiplayer=True,
        )

        # Crear producto de computador con especificaciones
        self.prod_pc = Product.objects.create(
            name="Laptop X",
            slug="laptop-x",
            price=3500000,
            category=self.cat_pc,
            is_active=True,
            stock_quantity=2,
        )
        ProductSpecification.objects.create(
            product=self.prod_pc,
            processor="Intel i7",
            ram_memory="16GB",
            storage_type="SSD",
            storage_capacity="512GB",
            graphics_card="NVIDIA RTX 3060",
        )

        # Crear producto celular con especificaciones
        self.prod_celular = Product.objects.create(
            name="Smartphone Y",
            slug="smartphone-y",
            price=1200000,
            category=self.cat_celulares,
            is_active=True,
            stock_quantity=10,
        )
        ProductSpecification.objects.create(
            product=self.prod_celular,
            screen_size=6.5,
            screen_resolution="1080x2400",
            ram_memory="8GB",
            internal_storage="128GB",
            main_camera="48MP",
        )

        # Producto inactivo (no debe aparecer en filtros)
        self.prod_inactive = Product.objects.create(
            name="Producto Inactivo",
            slug="producto-inactivo",
            price=50000,
            category=self.cat_gaming,
            is_active=False,
            stock_quantity=0,
        )

    def test_product_list_filter_by_category(self):
        """Prueba filtro por categoría usando parámetro cat."""
        # Filtrar por categoría gaming
        url_gaming = reverse("catalog:product_list") + f"?cat={self.cat_gaming.slug}"
        resp = self.client.get(url_gaming)
        self.assertEqual(resp.status_code, 200)
        names = [p.name for p in resp.context["object_list"]]
        self.assertIn("Juego Pro", names)
        self.assertNotIn("Laptop X", names)
        self.assertNotIn("Smartphone Y", names)

        # Filtrar por categoría computadores
        url_pc = reverse("catalog:product_list") + f"?cat={self.cat_pc.slug}"
        resp = self.client.get(url_pc)
        self.assertEqual(resp.status_code, 200)
        names = [p.name for p in resp.context["object_list"]]
        self.assertIn("Laptop X", names)
        self.assertNotIn("Juego Pro", names)

    def test_product_list_filter_gaming(self):
        """Prueba filtro específico para productos gaming."""
        url = reverse("catalog:product_list") + "?gaming=true"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        names = [p.name for p in resp.context["object_list"]]
        self.assertIn("Juego Pro", names)
        # No debe incluir productos de otras categorías
        self.assertNotIn("Laptop X", names)
        self.assertNotIn("Smartphone Y", names)

    def test_product_list_excludes_inactive(self):
        """Prueba que los productos inactivos no aparecen en el listado."""
        url = reverse("catalog:product_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        names = [p.name for p in resp.context["object_list"]]
        self.assertNotIn("Producto Inactivo", names)

    def test_get_main_specs_gaming(self):
        """Prueba get_main_specs para productos gaming."""
        specs = self.prod_game.get_main_specs()
        self.assertIsInstance(specs, dict)
        self.assertIn("Plataforma", specs)
        self.assertEqual(specs["Plataforma"], "PC")
        self.assertIn("Género", specs)
        self.assertEqual(specs["Género"], "Acción")

    def test_get_main_specs_computadores(self):
        """Prueba get_main_specs para productos de computadores."""
        specs = self.prod_pc.get_main_specs()
        self.assertIsInstance(specs, dict)
        self.assertIn("Procesador", specs)
        self.assertEqual(specs["Procesador"], "Intel i7")
        self.assertIn("RAM", specs)
        self.assertEqual(specs["RAM"], "16GB")
        self.assertIn("Almacenamiento", specs)
        self.assertEqual(specs["Almacenamiento"], "SSD 512GB")
        self.assertIn("GPU", specs)
        self.assertEqual(specs["GPU"], "NVIDIA RTX 3060")

    def test_get_main_specs_celulares(self):
        """Prueba get_main_specs para productos de celulares."""
        specs = self.prod_celular.get_main_specs()
        self.assertIsInstance(specs, dict)
        self.assertIn("Pantalla", specs)
        self.assertIn("RAM", specs)
        self.assertEqual(specs["RAM"], "8GB")
        self.assertIn("Almacenamiento", specs)
        self.assertEqual(specs["Almacenamiento"], "128GB")
        self.assertIn("Cámara", specs)
        self.assertEqual(specs["Cámara"], "48MP")

    def test_get_main_specs_without_specifications(self):
        """Prueba get_main_specs cuando no hay especificaciones."""
        product_no_specs = Product.objects.create(
            name="Sin Specs",
            slug="sin-specs",
            price=50000,
            category=self.cat_gaming,
            is_active=True,
            stock_quantity=1,
        )
        specs = product_no_specs.get_main_specs()
        self.assertIsInstance(specs, dict)
        self.assertEqual(specs, {})

