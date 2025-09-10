from django.db import models
import json

class Category(models.Model):
    """Categorías principales de productos electrónicos"""
    CATEGORY_TYPES = [
        ('celulares_tablets', 'Celulares y Tablets'),
        ('computadores', 'Computadores y Periféricos'),
        ('componentes', 'Componentes y Hardware'),
        ('audio_video', 'Audio y Video'),
        ('gaming', 'Gaming'),
    ]
    
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES, default='computadores')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    @property
    def is_parent(self):
        return self.subcategories.exists()
    
    def get_total_products_count(self):
        """Obtiene el total de productos incluyendo subcategorías"""
        if self.is_parent:
            # Si es categoría padre, sumar productos de todas las subcategorías
            total = 0
            for subcategory in self.subcategories.all():
                total += subcategory.products.count()
            return total
        else:
            # Si es subcategoría, solo contar sus propios productos
            return self.products.count()

class ProductSpecification(models.Model):
    """Especificaciones técnicas de productos"""
    product = models.OneToOneField('Product', on_delete=models.CASCADE, related_name='specifications')
    
    # Características comunes
    brand = models.CharField(max_length=80, blank=True, verbose_name="Marca")
    model = models.CharField(max_length=120, blank=True, verbose_name="Modelo")
    
    # Para Celulares/Tablets/Smartwatches
    operating_system = models.CharField(max_length=50, blank=True, verbose_name="Sistema Operativo")
    screen_size = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, verbose_name="Tamaño Pantalla (pulgadas)")
    screen_resolution = models.CharField(max_length=50, blank=True, verbose_name="Resolución")
    ram_memory = models.CharField(max_length=20, blank=True, verbose_name="Memoria RAM")
    internal_storage = models.CharField(max_length=20, blank=True, verbose_name="Almacenamiento")
    main_camera = models.CharField(max_length=50, blank=True, verbose_name="Cámara Principal")
    front_camera = models.CharField(max_length=50, blank=True, verbose_name="Cámara Frontal")
    battery_capacity = models.CharField(max_length=20, blank=True, verbose_name="Batería (mAh)")
    connectivity = models.TextField(blank=True, verbose_name="Conectividad")
    
    # Para Computadores
    processor = models.CharField(max_length=100, blank=True, verbose_name="Procesador")
    graphics_card = models.CharField(max_length=100, blank=True, verbose_name="Tarjeta Gráfica")
    storage_type = models.CharField(max_length=50, blank=True, verbose_name="Tipo de Almacenamiento")
    storage_capacity = models.CharField(max_length=20, blank=True, verbose_name="Capacidad Almacenamiento")
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Peso (kg)")
    
    # Para Componentes
    socket_type = models.CharField(max_length=50, blank=True, verbose_name="Socket/Compatibilidad")
    power_consumption = models.CharField(max_length=20, blank=True, verbose_name="Consumo Energético")
    frequency = models.CharField(max_length=50, blank=True, verbose_name="Frecuencia")
    memory_type = models.CharField(max_length=20, blank=True, verbose_name="Tipo de Memoria")
    
    # Para Audio/Video
    display_technology = models.CharField(max_length=50, blank=True, verbose_name="Tecnología de Pantalla")
    refresh_rate = models.CharField(max_length=20, blank=True, verbose_name="Frecuencia de Refresco")
    audio_power = models.CharField(max_length=20, blank=True, verbose_name="Potencia Audio (W)")
    channels = models.CharField(max_length=20, blank=True, verbose_name="Canales")
    
    # Para Gaming
    platform_compatibility = models.CharField(max_length=100, blank=True, verbose_name="Compatibilidad Plataforma")
    genre = models.CharField(max_length=50, blank=True, verbose_name="Género")
    multiplayer = models.BooleanField(default=False, verbose_name="Multijugador")
    age_rating = models.CharField(max_length=10, blank=True, verbose_name="Clasificación Edad")
    
    # Campo flexible para características adicionales
    additional_specs = models.JSONField(default=dict, blank=True, verbose_name="Especificaciones Adicionales")
    
    def __str__(self):
        return f"Specs for {self.product.name}"

class Product(models.Model):
    """Productos electrónicos con especificaciones técnicas"""
    name = models.CharField(max_length=120, verbose_name="Nombre")
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField(blank=True, verbose_name="Descripción")
    short_description = models.CharField(max_length=200, blank=True, verbose_name="Descripción Corta")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products", verbose_name="Categoría")
    
    # Estado del producto
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    is_featured = models.BooleanField(default=False, verbose_name="Destacado")
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name="Cantidad en Stock")
    
    # Imágenes
    main_image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Imagen Principal")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_featured', 'is_active']),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0

    @property
    def brand(self):
        if hasattr(self, 'specifications') and self.specifications.brand:
            return self.specifications.brand
        return "Sin marca"

    def get_main_specs(self):
        """Retorna las especificaciones principales según la categoría"""
        if not hasattr(self, 'specifications'):
            return {}
        
        specs = self.specifications
        category_type = self.category.category_type
        
        main_specs = {}
        
        if category_type == 'celulares_tablets':
            if specs.screen_size:
                main_specs['Pantalla'] = f"{specs.screen_size}\" {specs.screen_resolution}"
            if specs.ram_memory:
                main_specs['RAM'] = specs.ram_memory
            if specs.internal_storage:
                main_specs['Almacenamiento'] = specs.internal_storage
            if specs.main_camera:
                main_specs['Cámara'] = specs.main_camera
                
        elif category_type == 'computadores':
            if specs.processor:
                main_specs['Procesador'] = specs.processor
            if specs.ram_memory:
                main_specs['RAM'] = specs.ram_memory
            if specs.storage_capacity:
                main_specs['Almacenamiento'] = f"{specs.storage_type} {specs.storage_capacity}"
            if specs.graphics_card:
                main_specs['GPU'] = specs.graphics_card
                
        elif category_type == 'componentes':
            if specs.frequency:
                main_specs['Frecuencia'] = specs.frequency
            if specs.socket_type:
                main_specs['Socket'] = specs.socket_type
            if specs.power_consumption:
                main_specs['TDP'] = specs.power_consumption
                
        elif category_type == 'audio_video':
            if specs.screen_size:
                main_specs['Tamaño'] = f"{specs.screen_size}\""
            if specs.screen_resolution:
                main_specs['Resolución'] = specs.screen_resolution
            if specs.display_technology:
                main_specs['Tecnología'] = specs.display_technology
            if specs.audio_power:
                main_specs['Potencia'] = specs.audio_power
                
        elif category_type == 'gaming':
            if specs.platform_compatibility:
                main_specs['Plataforma'] = specs.platform_compatibility
            if specs.genre:
                main_specs['Género'] = specs.genre
            if specs.age_rating:
                main_specs['Edad'] = specs.age_rating
        
        return main_specs
