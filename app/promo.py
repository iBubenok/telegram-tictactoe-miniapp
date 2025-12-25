import secrets


def generate_promo_code(length: int = 5) -> str:
    upper_bound = 10**length
    number = secrets.randbelow(upper_bound)
    return f"{number:0{length}d}"
