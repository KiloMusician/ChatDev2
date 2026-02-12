'''
Class representing the main window of the application.
'''
import tkinter as tk
from tkinter import Label
class MainWindow:
    def __init__(self, root):
        self.root = root
        self.create_window()
    def create_window(self):
        self.root.title("Hello World App")
        self.root.geometry("300x200")
        self.add_label()
    def add_label(self):
        label = Label(self.root, text="Hello, World!", font=("Arial", 16))
        label.pack(pady=20)