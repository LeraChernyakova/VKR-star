from tkinter import Tk
from src.GUI.gui import AstrometryApp

if __name__ == "__main__":
    root = Tk()
    root.geometry("400x300")
    app = AstrometryApp(root)
    root.mainloop()