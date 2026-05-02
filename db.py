import psycopg2

def get_connection():
    return psycopg2.connect(
        dbname="hotel_db",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432"
    )

# получить колонки таблицы
def get_columns(table):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, (table,))
    cols = [row[0] for row in cur.fetchall()]
    conn.close()
    return cols

# получить данные
def get_table_data(table):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table}")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_row(table, id_column, row_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table} WHERE {id_column} = %s", (row_id,))
    row = cur.fetchone()
    conn.close()
    return row


def get_display_data(table):
    """
    Возвращает кортеж (columns, rows) для отображения в UI.
    Для связанных таблиц возвращаем человекочитаемые поля (JOIN).
    """
    conn = get_connection()
    cur = conn.cursor()

    # special case for hotels: hide director/owner and prefer `stars` column if exists
    if table == 'hotels':
        try:
            cols = get_columns('hotels')
            if 'stars' in cols:
                cur.execute("""
                    SELECT hotel_id, name, stars, address
                    FROM hotels
                    ORDER BY hotel_id
                """)
                rows = cur.fetchall()
                conn.close()
                columns = ['hotel_id', 'name', 'stars', 'address']
                return columns, rows
            else:
                # fallback: show inn in place of stars, but hide director/owner
                cur.execute("""
                    SELECT hotel_id, name, inn, address
                    FROM hotels
                    ORDER BY hotel_id
                """)
                rows = cur.fetchall()
                conn.close()
                columns = ['hotel_id', 'name', 'inn', 'address']
                return columns, rows
        except Exception:
            conn.close()
            cols = get_columns(table)
            rows = get_table_data(table)
            return cols, rows

    if table == 'staff':
        cur.execute("""
            SELECT s.staff_id, h.name as hotel_name, s.full_name, p.position_name
            FROM staff s
            LEFT JOIN hotels h ON s.hotel_id = h.hotel_id
            LEFT JOIN positions p ON s.position_id = p.position_id
            ORDER BY s.staff_id
        """)
        rows = cur.fetchall()
        conn.close()
        columns = ['staff_id', 'hotel_name', 'full_name', 'position_name']
        return columns, rows

    if table == 'rooms':
        cur.execute("""
            SELECT r.room_id, h.name as hotel_name, r.room_description, r.capacity, r.price_per_day, r.status
            FROM rooms r
            LEFT JOIN hotels h ON r.hotel_id = h.hotel_id
            ORDER BY r.room_id
        """)
        rows = cur.fetchall()
        conn.close()
        columns = ['room_id', 'hotel_name', 'room_description', 'capacity', 'price_per_day', 'status']
        return columns, rows

    if table == 'bookings':
        cur.execute("""
            SELECT b.booking_id, g.full_name as guest, h.name as hotel, r.capacity as capacity, b.arrival_date, b.departure_date, b.advance_payment
            FROM bookings b
            LEFT JOIN guests g ON b.guest_id = g.guest_id
            LEFT JOIN rooms r ON b.room_id = r.room_id
            LEFT JOIN hotels h ON r.hotel_id = h.hotel_id
            ORDER BY b.booking_id
        """)
        rows = cur.fetchall()
        conn.close()
        columns = ['booking_id', 'guest', 'hotel', 'capacity', 'arrival_date', 'departure_date', 'advance_payment']
        return columns, rows

    if table == 'guests':
        # показать отель из FK (без capacity)
        cur.execute("""
            SELECT g.guest_id, g.full_name, g.passport, g.phone, h.name as hotel
            FROM guests g
            LEFT JOIN hotels h ON g.hotel_id = h.hotel_id
            ORDER BY g.guest_id
        """)
        rows = cur.fetchall()
        conn.close()
        columns = ['guest_id', 'full_name', 'passport', 'phone', 'hotel']
        return columns, rows

    if table == 'bookings':
        cur.execute("""
            SELECT b.booking_id, g.full_name as guest, r.room_id as room, b.arrival_date, b.departure_date, b.advance_payment
            FROM bookings b
            LEFT JOIN guests g ON b.guest_id = g.guest_id
            LEFT JOIN rooms r ON b.room_id = r.room_id
            ORDER BY b.booking_id
        """)
        rows = cur.fetchall()
        conn.close()
        columns = ['booking_id', 'guest', 'room', 'arrival_date', 'departure_date', 'advance_payment']
        return columns, rows

    # default
    conn.close()
    cols = get_columns(table)
    rows = get_table_data(table)
    return cols, rows


def get_rooms_by_hotel_display(hotel_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.capacity, r.room_description, r.price_per_day, r.status
        FROM rooms r
        WHERE r.hotel_id = %s
        ORDER BY r.room_id
    """, (hotel_id,))
    rows = cur.fetchall()
    conn.close()
    columns = ['capacity', 'room_description', 'price_per_day', 'status']
    return columns, rows

# добавить запись
def insert_row(table, columns, values):
    conn = get_connection()
    cur = conn.cursor()

    cols = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(values))

    cur.execute(
        f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
        values
    )

    conn.commit()
    conn.close()

# удалить
def delete_row(table, id_column, row_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Найдём внешние ключи, ссылающиеся на эту таблицу
        cur.execute("""
            SELECT tc.table_schema, tc.table_name, kcu.column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' AND ccu.table_name = %s;
        """, (table,))
        refs = cur.fetchall()

        blocking = []
        for schema, ref_table, ref_column in refs:
            # посчитаем, есть ли строки в ссылающихся таблицах
            try:
                cur.execute(f"SELECT COUNT(*) FROM {ref_table} WHERE {ref_column} = %s", (row_id,))
                cnt = cur.fetchone()[0]
            except Exception:
                cnt = 0
            if cnt:
                blocking.append((ref_table, ref_column, cnt))

        if blocking:
            parts = [f"{t} ({c})" for (t, col, c) in blocking]
            raise ValueError("Нельзя удалить запись — есть связанные записи в таблицах: " + ", ".join(parts))

        cur.execute(f"DELETE FROM {table} WHERE {id_column} = %s", (row_id,))
        conn.commit()
    finally:
        conn.close()

# обновить
def update_row(table, columns, values, id_column, row_id):
    conn = get_connection()
    cur = conn.cursor()

    set_clause = ", ".join([f"{col}=%s" for col in columns])

    cur.execute(
        f"UPDATE {table} SET {set_clause} WHERE {id_column}=%s",
        values + [row_id]
    )

    conn.commit()
    conn.close()


# --- отчёты / вспомогательные запросы ---
def get_free_rooms():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT room_id, room_description, capacity, price_per_day FROM rooms WHERE status = 'free'")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_staff_count_by_position():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.position_name, COUNT(s.staff_id) as cnt
        FROM positions p
        LEFT JOIN staff s ON p.position_id = s.position_id
        GROUP BY p.position_name
        ORDER BY cnt DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_rows_by_fk(table, fk_column, fk_value):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table} WHERE {fk_column} = %s", (fk_value,))
    rows = cur.fetchall()
    conn.close()
    return rows


def cascade_delete_hotel(hotel_id):
    """Удалить гостиницу и все зависимые записи (bookings -> rooms, staff)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # удалить бронирования для номеров этой гостиницы
        cur.execute("""
            DELETE FROM bookings WHERE room_id IN (
                SELECT room_id FROM rooms WHERE hotel_id = %s
            )
        """, (hotel_id,))

        # удалить номера
        cur.execute("DELETE FROM rooms WHERE hotel_id = %s", (hotel_id,))

        # удалить сотрудников
        cur.execute("DELETE FROM staff WHERE hotel_id = %s", (hotel_id,))

        # удалить сам отель
        cur.execute("DELETE FROM hotels WHERE hotel_id = %s", (hotel_id,))

        conn.commit()
    finally:
        conn.close()