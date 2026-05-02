import psycopg2

conn = psycopg2.connect(
    dbname="hotel_db",
    user="postgres",
    password="1234",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Проверим структуру таблицы guests
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'guests'
    ORDER BY ordinal_position;
""")
print("Текущая структура guests:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Попытаемся добавить FK если колонка есть
try:
    cur.execute("""
        ALTER TABLE guests ADD CONSTRAINT fk_guests_hotel 
        FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id);
    """)
    print("\nFK добавлена успешно")
except psycopg2.Error as e:
    print(f"\nОшибка при добавлении FK: {e}")

conn.commit()
conn.close()
