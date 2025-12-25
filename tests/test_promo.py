from app.promo import generate_promo_code


def test_promo_code_length_and_digits():
    for _ in range(20):
        code = generate_promo_code()
        assert len(code) == 5
        assert code.isdigit()
