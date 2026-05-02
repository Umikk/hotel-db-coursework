import psycopg2

conn = psycopg2.connect(
    dbname="hotel_db",
    user="postgres",
    password="1234",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Добавляем колонку hotel_id (без DEFAULT, будет NULL)
try:
    cur.execute("ALTER TABLE guests ADD COLUMN hotel_id INT;")
    print("Колонка hotel_id добавлена")
except psycopg2.Error as e:
    print(f"Ошибка добавления колонки: {e}")

# Добавляем FK
try:
    cur.execute("""
        ALTER TABLE guests ADD CONSTRAINT fk_guests_hotel 
        FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id);
    """)
    print("FK добавлена успешно")
except psycopg2.Error as e:
    print(f"Ошибка добавления FK: {e}")

conn.commit()
conn.close()
print("Миграция завершена")
