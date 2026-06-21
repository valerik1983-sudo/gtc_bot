# check_symptoms.py
from database import get_all_products_from_db

products = get_all_products_from_db()
for product in products:
    if product['symptoms']:
        print(f"Товар: {product['name']}")
        print(f"Симптомы: {product['symptoms']}")
        print("---")
        