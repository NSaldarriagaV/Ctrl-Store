# ctrlstore/apps/payment/services.py
from datetime import datetime
from django.core.exceptions import ValidationError

def luhn_check(number: str) -> bool:
    digits = [int(d) for d in number if d.isdigit()]
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0

def detect_brand(number: str) -> str:
    n = number
    if n.startswith("4"):
        return "visa"
    if (len(n) >= 2 and n[:2] in {"51","52","53","54","55"}) or (len(n) >= 4 and 2221 <= int(n[:4]) <= 2720):
        return "mastercard"
    if n.startswith("34") or n.startswith("37"):
        return "amex"
    if n.startswith("6011") or n.startswith("65"):
        return "discover"
    return "card"

def validate_card_number(number: str) -> None:
    if not number.isdigit():
        raise ValidationError("El número de tarjeta debe contener solo dígitos.")
    if not (13 <= len(number) <= 19):
        raise ValidationError("El número de tarjeta debe tener entre 13 y 19 dígitos.")
    if not luhn_check(number):
        raise ValidationError("Número de tarjeta inválido (Luhn).")

def validate_expiry(month: int, year: int) -> None:
    # Acepta YY o YYYY
    if year < 100:
        year += 2000
    if not (2000 <= year <= 2100):
        raise ValidationError("Año de expiración inválido.")
    if not (1 <= month <= 12):
        raise ValidationError("Mes de expiración inválido.")
    now = datetime.utcnow()
    if (year, month) < (now.year, now.month):
        raise ValidationError("La tarjeta está expirada.")

def validate_cvv(cvv: str, brand: str) -> None:
    if not cvv.isdigit():
        raise ValidationError("CVV inválido.")
    if brand == "amex":
        if len(cvv) != 4:
            raise ValidationError("CVV debe tener 4 dígitos para Amex.")
    else:
        if len(cvv) != 3:
            raise ValidationError("CVV debe tener 3 dígitos.")

# --- Simulación de autorización ---
class AuthResult:
    def __init__(self, ok: bool, auth_code: str | None = None, error_code: str | None = None, msg: str | None = None):
        self.ok = ok
        self.auth_code = auth_code
        self.error_code = error_code
        self.msg = msg

def simulate_authorize(number: str, amount: float | int, currency: str = "COP") -> AuthResult:
    last4 = number[-4:]
    # Reglas que NO chocan con tarjetas de prueba estándar
    if number.endswith("0005"):
        return AuthResult(False, error_code="insufficient_funds", msg="Fondos insuficientes.")
    if number.endswith("3333"):
        return AuthResult(False, error_code="do_not_honor", msg="Transacción rechazada por el emisor.")
    if number.endswith("6666"):
        return AuthResult(False, error_code="suspected_fraud", msg="Transacción sospechosa.")
    return AuthResult(True, auth_code=f"A{last4}OK")