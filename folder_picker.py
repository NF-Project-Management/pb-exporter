# folder_picker.py
import tkinter as tk
from tkinter import filedialog
import sys

def pick():
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askdirectory()
    print(path)

if __name__ == "__main__":
    pick()
