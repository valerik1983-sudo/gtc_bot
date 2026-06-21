from database import add_office_city, get_office_cities

def add_city():
    city = input("Введите название города: ").strip().title()
    add_office_city(city)
    print(f"✅ Город '{city}' добавлен!")
    
    print("\nТекущий список городов:")
    for c in get_office_cities():
        print(f"  • {c}")

if __name__ == "__main__":
    add_city()