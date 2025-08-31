from django.contrib import admin
from .models import Category, Product, ProductSpecification

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "category_type", "parent", "is_active")
    list_filter = ("category_type", "parent", "is_active")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_active",)

class ProductSpecificationInline(admin.StackedInline):
    model = ProductSpecification
    extra = 0
    fieldsets = (
        ('Información General', {
            'fields': ('brand', 'model')
        }),
        ('Pantalla y Display', {
            'fields': ('screen_size', 'screen_resolution', 'display_technology', 'refresh_rate'),
            'classes': ('collapse',)
        }),
        ('Rendimiento', {
            'fields': ('processor', 'ram_memory', 'graphics_card', 'operating_system'),
            'classes': ('collapse',)
        }),
        ('Almacenamiento', {
            'fields': ('internal_storage', 'storage_type', 'storage_capacity'),
            'classes': ('collapse',)
        }),
        ('Cámara y Batería', {
            'fields': ('main_camera', 'front_camera', 'battery_capacity'),
            'classes': ('collapse',)
        }),
        ('Conectividad y Audio', {
            'fields': ('connectivity', 'audio_power', 'channels'),
            'classes': ('collapse',)
        }),
        ('Especificaciones Técnicas', {
            'fields': ('socket_type', 'power_consumption', 'frequency', 'memory_type', 'weight'),
            'classes': ('collapse',)
        }),
        ('Gaming', {
            'fields': ('platform_compatibility', 'genre', 'multiplayer', 'age_rating'),
            'classes': ('collapse',)
        }),
        ('Adicionales', {
            'fields': ('additional_specs',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "brand", "category", "is_active", "is_featured", "stock_quantity", "created_at")
    list_filter = ("category", "is_active", "is_featured", "category__category_type")
    search_fields = ("name", "specifications__brand", "specifications__model")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_active", "is_featured", "stock_quantity")
    inlines = [ProductSpecificationInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'slug', 'category', 'price')
        }),
        ('Descripción', {
            'fields': ('short_description', 'description')
        }),
        ('Estado y Stock', {
            'fields': ('is_active', 'is_featured', 'stock_quantity')
        }),
        ('Imagen', {
            'fields': ('main_image',)
        }),
    )
    
    def brand(self, obj):
        return obj.brand
    brand.short_description = "Marca"

@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ("product", "brand", "model", "processor", "ram_memory")
    list_filter = ("brand", "operating_system", "product__category")
    search_fields = ("product__name", "brand", "model", "processor")
