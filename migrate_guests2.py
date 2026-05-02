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
    # Убираем DEFAULT и устанавливаем NULL
    cur.execute("UPDATE guests SET hotel_id = NULL WHERE hotel_id = 1;")
    print("Обновили NULL значения")
    
    # Добавляем FK
    cur.execute("""
        ALTER TABLE guests ADD CONSTRAINT fk_guests_hotel 
        FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id);
    """)
    print("FK добавлена успешно")
except psycopg2.Error as e:
    if "already exists" in str(e):
        print("FK уже существует")
    else:
        print(f"Ошибка: {e}")

conn.commit()
conn.close()
print("Миграция завершена успешно")
