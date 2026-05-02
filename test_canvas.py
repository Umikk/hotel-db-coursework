import tkinter as tk

root = tk.Tk()
canvas = tk.Canvas(root, width=300, height=200)
canvas.pack()

r = 20
w = 110
h = 60

canvas.create_arc(0, 0, r*2, r*2, start=90, extent=90, fill='grey', outline='grey')
canvas.create_arc(w-r*2, 0, w, r*2, start=0, extent=90, fill='grey', outline='grey')
canvas.create_arc(0, h-r*2, r*2, h, start=180, extent=90, fill='grey', outline='grey')
canvas.create_arc(w-r*2, h-r*2, w, h, start=270, extent=90, fill='grey', outline='grey')

canvas.create_rectangle(r, 0, w-r, h, fill='red', outline='red')
canvas.create_rectangle(0, r, w, h-r, fill='blue', outline='blue')

print('OK')
root.destroy()
