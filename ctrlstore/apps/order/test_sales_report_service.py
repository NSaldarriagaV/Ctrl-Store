import pytest
import uuid
from decimal import Decimal
from django.utils import timezone

from ctrlstore.apps.order.reporting import ReportGenerator, SalesReportService
from ctrlstore.apps.order.models import Order, OrderItem
from ctrlstore.apps.catalog.models import Category, Product
from ctrlstore.apps.authx.models import User


@pytest.fixture
def order_factory(db):
    def _create_order(
        *,
        created_at=None,
        total_amount=None,
        status="paid",
        user=None,
        product=None,
        quantity=1,
    ):
        # ---------- Usuario ----------
        if user is None:
            user_suffix = uuid.uuid4().hex
            user = User.objects.create_user(
                username=f"user_{user_suffix}",
                email=f"test_{user_suffix}@example.com",  # 👈 email único
                password="test1234",
            )

        # ---------- Producto + categoría ----------
        if product is None:
            cat_suffix = uuid.uuid4().hex  # 👈 también único para el nombre
            category = Category.objects.create(
                name=f"Laptops {cat_suffix}",          # 👈 name único
                slug=f"laptops-{cat_suffix}",          # slug único
                category_type="computadores",          # ajusta si tu modelo lo requiere
                parent=None,
                is_active=True,
            )
            product = Product.objects.create(
                name=f"Laptop Test {cat_suffix}",
                slug=f"laptop-test-{cat_suffix}",
                category=category,
                price=Decimal("100.00"),
                stock_quantity=10,
                is_active=True,
            )

        # ---------- Orden + item ----------
        if created_at is None:
            created_at = timezone.now()

        unit_price = product.price
        line_total = unit_price * quantity

        if total_amount is None:
            total_amount = line_total

        order = Order.objects.create(
            user=user,
            status=status,
            total_amount=total_amount,
            created_at=created_at,
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            unit_price=unit_price,
            quantity=quantity,
            line_total=line_total,  # 👈 ya no es NULL
        )

        return order

    return _create_order

class FakeReportGenerator(ReportGenerator):
    content_type = "application/x-fake"
    file_extension = "fake"

    def __init__(self):
        self.rows = None

    def generate(self, rows):
        self.rows = list(rows)
        return b"FAKE_BYTES"


@pytest.mark.django_db
def test_sales_report_service_builds_rows_correctly(order_factory):
    # Crea un par de órdenes con items usando tu factory existente
    order1 = order_factory()
    order2 = order_factory()

    generator = FakeReportGenerator()
    service = SalesReportService(generator)

    result_bytes = service.build_report([order1, order2])

    assert result_bytes == b"FAKE_BYTES"
    assert len(generator.rows) == 2
    assert "order_id" in generator.rows[0]
    assert "total" in generator.rows[0]
