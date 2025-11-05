import os
from django.core.files import File
from django.core.management.base import BaseCommand
from ctrlstore.apps.catalog.models import Product  # ajusta si tu modelo está en otro módulo

class Command(BaseCommand):
    help = "Asigna imágenes a productos automáticamente según nombre del archivo"

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, required=False, default='media/products',
                            help='Ruta a la carpeta con las imágenes')

    def handle(self, *args, **options):
        path = options['path']
        count = 0

        if not os.path.exists(path):
            self.stdout.write(self.style.ERROR(f"La carpeta {path} no existe"))
            return

        for fname in os.listdir(path):
            name, _ = os.path.splitext(fname)
            # Ajusta aquí según convenga: por name o slug
            product = Product.objects.filter(name__icontains=name).first()

            if product:
                image_path = os.path.join(path, fname)
                with open(image_path, 'rb') as f:
                    product.main_image.save(fname, File(f), save=True)
                count += 1
                self.stdout.write(self.style.SUCCESS(f"✓ {product.name} ← {fname}"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ No se encontró producto para {fname}"))

        self.stdout.write(self.style.SUCCESS(f"\nTotal asignadas: {count}"))
