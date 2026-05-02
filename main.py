import tkinter as tk
from tkinter import ttk, messagebox
from db import *

# типизация для полей
TYPE_MAP = {
    'capacity': int,
    'price_per_day': float,
    'advance_payment': float,
}

# отображения для колонок
COLUMN_TRANSLATE = {
    'hotel_id': 'ID гостиницы',
    'name': 'Название',
    'inn': 'Звёзды',
    'stars': 'Звёзды',
    'hotel': 'Отель',
    'hotel_name': 'Отель',
    'director': 'Директор',
    'owner': 'Владелец',
    'address': 'Адрес',
    'position_id': 'ID должности',
    'position_name': 'Должность',
    'staff_id': 'ID сотрудника',
    'person_inn': 'ИНН сотрудника',
    'full_name': 'ФИО',
    'room_id': 'ID номера',
    'room_description': 'Описание номера',
    'capacity': 'Количество спальных мест',
    'price_per_day': 'Цена в день',
    'status': 'Статус',
    'guest_id': 'ID гостя',
    'passport': 'Паспорт',
    'phone': 'Телефон',
    'booking_id': 'ID брони',
    'arrival_date': 'Дата заезда',
    'departure_date': 'Дата выезда',
    'advance_payment': 'Аванс',
}

# Статусы номера: internal -> display
STATUS_MAP = {
    'free': 'Свободен',
    'occupied': 'Забронирован',
    'maintenance': 'В ремонте',
}
STATUS_MAP_REV = {v: k for k, v in STATUS_MAP.items()}


def try_cast(col, val):
    if val == '' or val is None:
        return None
    caster = TYPE_MAP.get(col)
    if caster:
        try:
            return caster(val)
        except Exception as e:
            raise ValueError(f"Неверный формат для {col}: {e}")
    return val


def set_placeholder(entry, text):
    # минимальная реализация: просто оставляем поле пустым (не критично)
    return

# ================= ЗАГРУЗКА =================
def load_data():
    table = table_var.get()

    for row in tree.get_children():
        tree.delete(row)
    # get display columns and rows (may include joined human-readable fields)
    try:
        columns, rows = get_display_data(table)
    except Exception:
        columns = get_columns(table)
        rows = get_table_data(table)

    tree["columns"] = columns

    for col in columns:
        name = COLUMN_TRANSLATE.get(col, col)
        tree.heading(col, text=name)
        tree.column(col, width=140)

    # Если таблица rooms — показываем человеко-читаемый статус
    if table == 'rooms' and rows:
        try:
            idx = columns.index('status')
            new_rows = []
            for r in rows:
                row_list = list(r)
                row_list[idx] = STATUS_MAP.get(row_list[idx], row_list[idx])
                new_rows.append(tuple(row_list))
            rows = new_rows
        except Exception:
            pass

    for row in rows:
        tree.insert("", "end", values=row)

# ================= ДОБАВЛЕНИЕ =================
def open_add():
    table = table_var.get()
    columns = get_columns(table)
    columns_no_id = columns[1:]
    # don't show person_inn field in staff forms
    if table == 'staff' and 'person_inn' in columns_no_id:
        columns_no_id.remove('person_inn')

    # hide owner and director for hotels (UI requirement)
    if table == 'hotels':
        for remove_col in ('owner', 'director'):
            if remove_col in columns_no_id:
                columns_no_id.remove(remove_col)

    win = tk.Toplevel()
    win.title("Добавить запись")

    entries = {}
    fk_maps = {}  # mapping display -> id for foreign keys

    for i, col in enumerate(columns_no_id):
        label = COLUMN_TRANSLATE.get(col, col)
        tk.Label(win, text=label).grid(row=i, column=0)

        if col.endswith("_id"):
            ref_table = col[:-3] + "s"
            try:
                ref_rows = get_table_data(ref_table)
                # assume first column is id and second is human-readable name
                options = [str(r[1]) for r in ref_rows]
                fk_map = {str(r[1]): r[0] for r in ref_rows}
            except Exception:
                options = []
                fk_map = {}

            cb = ttk.Combobox(win, values=options, state="readonly")
            cb.grid(row=i, column=1)
            entries[col] = cb
            fk_maps[col] = fk_map
        elif table == 'rooms' and col == 'status':
            opts = list(STATUS_MAP.values())
            cb = ttk.Combobox(win, values=opts, state='readonly')
            # default to 'free'
            cb.set(STATUS_MAP.get('free'))
            cb.grid(row=i, column=1)
            entries[col] = cb
        elif table == 'guests' and col == 'hotel_id':
            try:
                ref_rows = get_table_data('hotels')
                options = [str(r[1]) for r in ref_rows]
                fk_map = {str(r[1]): r[0] for r in ref_rows}
            except Exception:
                options = []
                fk_map = {}
            cb = ttk.Combobox(win, values=options, state='readonly')
            cb.grid(row=i, column=1)
            entries[col] = cb
            fk_maps[col] = fk_map
        else:
            e = tk.Entry(win)
            e.grid(row=i, column=1)
            set_placeholder(e, f"Введите {label}")
            entries[col] = e

    def save():
        values = []
        for col in columns_no_id:
            try:
                if col.endswith("_id"):
                    val = entries[col].get()
                    mapped = fk_maps.get(col, {}).get(val)
                    values.append(mapped)
                elif table == 'rooms' and col == 'status':
                    display = entries[col].get()
                    internal = STATUS_MAP_REV.get(display, display)
                    values.append(internal)
                elif table == 'guests' and col == 'hotel_id':
                    val = entries[col].get()
                    mapped = fk_maps.get(col, {}).get(val)
                    values.append(mapped)
                else:
                    raw = entries[col].get()
                    casted = try_cast(col, raw)
                    values.append(casted)
            except ValueError as e:
                messagebox.showerror('Ошибка', str(e))
                return

        insert_row(table, columns_no_id, values)
        load_data()  # автообновление
        win.destroy()

    ttk.Button(win, text="Сохранить", command=save).grid(row=len(columns_no_id), columnspan=2)
    win.grab_set()
    center_window(win)

# ================= УДАЛЕНИЕ =================
def delete_selected():
    table = table_var.get()
    columns = get_columns(table)

    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Ошибка", "Выберите запись")
        return

    item = tree.item(selected[0])
    row_id = item["values"][0]

    try:
        delete_row(table, columns[0], row_id)
    except ValueError as e:
        # если удаление заблокировано из-за связанных записей — предложим каскадное удаление для hotels
        if table == 'hotels':
            msg = str(e) + '\n\nУдалить гостиницу и все связанные записи (номера, брони, сотрудники)?'
            if messagebox.askyesno('Удаление с зависимостями', msg):
                try:
                    cascade_delete_hotel(row_id)
                except Exception as e2:
                    messagebox.showerror('Ошибка', f'Каскадное удаление не удалось: {e2}')
                    return
                load_data()
                return
            else:
                messagebox.showinfo('Отмена', 'Удаление отменено')
                return
        else:
            messagebox.showerror('Ошибка удаления', str(e))
            return
    except Exception as e:
        messagebox.showerror('Ошибка', f'Не удалось удалить запись: {e}')
        return

    load_data()


# ================= РЕДАКТИРОВАНИЕ =================
def open_edit():
    table = table_var.get()
    columns = get_columns(table)

    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Ошибка", "Выберите запись")
        return

    item = tree.item(selected[0])
    display_values = item["values"]

    row_id = display_values[0]
    # получаем реальные колонки и данные из БД по id — это гарантирует корректное соответствие полей
    row_db = get_row(table, columns[0], row_id)
    columns_no_id = columns[1:]

    if table == 'staff' and 'person_inn' in columns_no_id:
        columns_no_id.remove('person_inn')

    # hide owner and director for hotels in edit form
    if table == 'hotels':
        for remove_col in ('owner', 'director'):
            if remove_col in columns_no_id:
                columns_no_id.remove(remove_col)

    win = tk.Toplevel()
    win.title("Редактировать")

    entries = {}
    fk_maps = {}  # for mapping displayed name -> id

    for i, col in enumerate(columns_no_id):
        label = COLUMN_TRANSLATE.get(col, col)
        tk.Label(win, text=label).grid(row=i, column=0)

        if col.endswith("_id"):
            ref_table = col[:-3] + "s"
            try:
                ref_rows = get_table_data(ref_table)
                options = [str(r[1]) for r in ref_rows]
                fk_map = {str(r[1]): r[0] for r in ref_rows}
                id_to_name = {r[0]: str(r[1]) for r in ref_rows}
            except Exception:
                options = []
                fk_map = {}
                id_to_name = {}

            cb = ttk.Combobox(win, values=options, state="readonly")
            # set current value from DB row using column index
            try:
                db_index = columns.index(col)
                current_id = row_db[db_index]
                display = id_to_name.get(current_id)
                if display:
                    cb.set(display)
            except Exception:
                pass
            cb.grid(row=i, column=1)
            entries[col] = cb
            fk_maps[col] = fk_map
        elif table == 'rooms' and col == 'status':
            opts = list(STATUS_MAP.values())
            cb = ttk.Combobox(win, values=opts, state='readonly')
            try:
                db_index = columns.index(col)
                existing_value = row_db[db_index]
                cb.set(STATUS_MAP.get(existing_value, existing_value))
            except Exception:
                cb.set(STATUS_MAP.get('free'))
            cb.grid(row=i, column=1)
            entries[col] = cb
        elif table == 'guests' and col == 'hotel_id':
            try:
                ref_rows = get_table_data('hotels')
                options = [str(r[1]) for r in ref_rows]
                fk_map = {str(r[1]): r[0] for r in ref_rows}
                id_to_name = {r[0]: str(r[1]) for r in ref_rows}
            except Exception:
                options = []
                fk_map = {}
                id_to_name = {}
            cb = ttk.Combobox(win, values=options, state='readonly')
            try:
                db_index = columns.index(col)
                current_id = row_db[db_index]
                display = id_to_name.get(current_id)
                if display:
                    cb.set(display)
            except Exception:
                pass
            cb.grid(row=i, column=1)
            entries[col] = cb
            fk_maps[col] = fk_map
        else:
            e = tk.Entry(win)
            try:
                db_index = columns.index(col)
                existing_value = row_db[db_index]
            except Exception:
                existing_value = ''
            e.insert(0, '' if existing_value is None else str(existing_value))
            e.grid(row=i, column=1)
            entries[col] = e

    def save():
        new_values = []
        for col in columns_no_id:
            try:
                if col.endswith("_id"):
                    val = entries[col].get()
                    mapped = fk_maps.get(col, {}).get(val)
                    new_values.append(mapped)
                elif table == 'rooms' and col == 'status':
                    display = entries[col].get()
                    internal = STATUS_MAP_REV.get(display, display)
                    new_values.append(internal)
                elif table == 'guests' and col == 'hotel_id':
                    val = entries[col].get()
                    mapped = fk_maps.get(col, {}).get(val)
                    new_values.append(mapped)
                else:
                    raw = entries[col].get()
                    casted = try_cast(col, raw)
                    new_values.append(casted)
            except ValueError as e:
                messagebox.showerror('Ошибка', str(e))
                return

        update_row(table, columns_no_id, new_values, columns[0], row_id)
        load_data()
        win.destroy()

    ttk.Button(win, text="Сохранить", command=save).grid(row=len(columns_no_id), columnspan=2)
    win.grab_set()
    center_window(win)

# ================= UI =================
root = tk.Tk()
root.title("База данных гостиницы")
root.geometry("1000x600")

# стиль для современного вида
style = ttk.Style()
try:
    style.theme_use('clam')
except Exception:
    pass
style.configure('Treeview', rowheight=24, font=('Segoe UI', 10))
style.configure('TButton', padding=6)
style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))
style.configure('TButton', font=('Segoe UI', 10))
# selection color
style.map('Treeview', background=[('selected', '#b3d4fc')], foreground=[('selected', 'black')])

def center_window(win):
    win.transient(root)
    win.update_idletasks()
    try:
        rw = root.winfo_width()
        rh = root.winfo_height()
        rx = root.winfo_rootx()
        ry = root.winfo_rooty()
        ww = win.winfo_width()
        wh = win.winfo_height()
        x = rx + (rw - ww) // 2
        y = ry + (rh - wh) // 2
        win.geometry(f'+{x}+{y}')
    except Exception:
        pass

table_var = tk.StringVar(value="hotels")

combo = ttk.Combobox(root, textvariable=table_var, values=[
    "hotels", "rooms", "guests", "staff", "positions", "bookings"
])
combo.pack(pady=5)

tree = ttk.Treeview(root, show="headings")
tree.pack(fill=tk.BOTH, expand=True)

frame = tk.Frame(root)
frame.pack(pady=10)
# toolbar и кнопки создаются внизу файла, после определения всех окон и функций

# автозагрузка
load_data()


def open_reports():
    win = tk.Toplevel()
    win.title('Отчёты')
    win.geometry('700x400')

    ttk.Label(win, text='Выберите отчёт:').pack(pady=6)
    report_var = tk.StringVar(value='free_rooms')
    reports = {'free_rooms': 'Свободные номера', 'staff_by_position': 'Сотрудники по должностям'}
    cb = ttk.Combobox(win, values=list(reports.values()), state='readonly')
    cb.current(0)
    cb.pack(pady=4)

    tree_r = ttk.Treeview(win, show='headings')
    tree_r.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

    def show_report():
        sel = cb.get()
        if sel == reports['free_rooms']:
            rows = get_free_rooms()
            tree_r.delete(*tree_r.get_children())
            tree_r['columns'] = ('room_id', 'room_description', 'capacity', 'price_per_day')
            for c in tree_r['columns']:
                tree_r.heading(c, text=c)
            for r in rows:
                tree_r.insert('', 'end', values=r)
        else:
            rows = get_staff_count_by_position()
            tree_r.delete(*tree_r.get_children())
            tree_r['columns'] = ('position_name', 'count')
            for c in tree_r['columns']:
                tree_r.heading(c, text=c)
            for r in rows:
                tree_r.insert('', 'end', values=r)

    ttk.Button(win, text='Показать', command=show_report).pack(pady=4)
    win.grab_set()
    center_window(win)


def open_one_to_many():
    win = tk.Toplevel()
    win.title('1:М форма — гостиницы и номера')
    win.geometry('900x500')

    left = ttk.Treeview(win, show='headings')
    right = ttk.Treeview(win, show='headings')
    left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=6)
    right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=6, pady=6)

    # load hotels (human-readable)
    try:
        cols_h, hotels = get_display_data('hotels')
        left['columns'] = cols_h
        for c in cols_h:
            left.heading(c, text=COLUMN_TRANSLATE.get(c, c))
            left.column(c, width=140)
        for h in hotels:
            left.insert('', 'end', values=h)
    except Exception:
        hotels = get_table_data('hotels')
        if hotels:
            left['columns'] = tuple([f'col{i}' for i in range(len(hotels[0]))])
            for i in range(len(hotels[0])):
                left.heading(f'col{i}', text=f'c{i}')
            for h in hotels:
                left.insert('', 'end', values=h)

    def on_select(event):
        sel = left.selection()
        if not sel:
            return
        item = left.item(sel[0])
        hotel_id = item['values'][0]
        right.delete(*right.get_children())
        try:
            cols_r, rooms = get_rooms_by_hotel_display(hotel_id)
            right['columns'] = cols_r
            for c in cols_r:
                right.heading(c, text=COLUMN_TRANSLATE.get(c, c))
                right.column(c, width=140)
            for r in rooms:
                right.insert('', 'end', values=r)
        except Exception:
            rooms = get_rows_by_fk('rooms', 'hotel_id', hotel_id)
            if rooms:
                right['columns'] = tuple([f'col{i}' for i in range(len(rooms[0]))])
                for i in range(len(rooms[0])):
                    right.heading(f'col{i}', text=f'c{i}')
                for r in rooms:
                    right.insert('', 'end', values=r)

    left.bind('<<TreeviewSelect>>', on_select)
    win.grab_set()
    center_window(win)

# --- RoundedButton и панель кнопок (создаём после определения окон) ---
class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=110, height=30, radius=10, bg='#f0f0f0', fg='black'):
        super().__init__(parent, width=width, height=height, highlightthickness=0, bg=parent.cget('bg'))
        self._width = width
        self._height = height
        self._radius = radius
        self._bg = bg
        self._fg = fg
        self.command = command

        # draw rounded rectangle
        r = radius
        w = width
        h = height
        self.create_arc(0, 0, r*2, r*2, start=90, extent=90, fill=bg, outline=bg)
        self.create_arc(w-r*2, 0, w, r*2, start=0, extent=90, fill=bg, outline=bg)
        self.create_arc(0, h-r*2, r*2, h, start=180, extent=90, fill=bg, outline=bg)
        self.create_arc(w-r*2, h-r*2, w, h, start=270, extent=90, fill=bg, outline=bg)
        self.create_rectangle(r, 0, w-r, h, fill=bg, outline=bg)
        self.create_rectangle(0, r, w, h-r, fill=bg, outline=bg)
        self.text_id = self.create_text(w//2, h//2, text=text, fill=fg, font=('Segoe UI', 10))

        self.bind('<Button-1>', self._on_click)
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)

    def _on_click(self, event):
        if self.command:
            self.command()

    def _on_enter(self, event):
        self.itemconfig(self.text_id, fill='blue')

    def _on_leave(self, event):
        self.itemconfig(self.text_id, fill=self._fg)


# toolbar buttons (rounded)
btns = [
    ('🟢 Загрузить', load_data),
    ('➕ Добавить', open_add),
    ('🗑 Удалить', delete_selected),
    ('✏️ Изменить', open_edit),
    ('🔄 Обновить', load_data),
    ('🧩 1:М форма', open_one_to_many),
    ('📊 Отчёты', open_reports),
]

for i, (t, cmd) in enumerate(btns):
    rb = RoundedButton(frame, text=t, command=cmd)
    rb.grid(row=0, column=i, padx=6)

root.mainloop()