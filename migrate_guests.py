import psycopg2

conn = psycopg2.connect(
    dbname="hotel_db",
    user="postgres",
    password="1234",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

try:
    # Добавляем колонку hotel_id, если её нет
    cur.execute("""
        ALTER TABLE guests ADD COLUMN hotel_id INT DEFAULT 1;
    """)
    print("Колонка hotel_id добавлена")
except psycopg2.Error as e:
    if "already exists" in str(e):
        print("Колонка hotel_id уже существует")
    else:
        print(f"Ошибка: {e}")

try:
    # Добавляем FK, если его нет
    cur.execute("""
        ALTER TABLE guests ADD CONSTRAINT fk_guests_hotel 
        FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id);
    """)
    print("FK добавлена")
except psycopg2.Error as e:
    if "already exists" in str(e):
        print("FK уже существует")
    else:
        print(f"Ошибка FK: {e}")

conn.commit()
conn.close()
print("Миграция завершена")
