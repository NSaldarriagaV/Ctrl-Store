from django.shortcuts import render

def checkout(request):
    """
    Vista de checkout básica.
    Más adelante aquí convertiremos el carrito en una orden.
    """
    return render(request, "order/checkout.html")
