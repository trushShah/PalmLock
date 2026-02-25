import tkinter as tk


class StatusPanel:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.config(bg="black")
        self.root.attributes("-transparentcolor", "black")
        self.root.geometry("130x40+0+0")

        self.canvas = tk.Canvas(
            self.root,
            width=130,
            height=40,
            bg="black",
            highlightthickness=0
        )
        self.canvas.pack()

        self.state = "MONITORING"
        self.update_ui()

    def update_state(self, new_state):
        self.state = new_state
        self.update_ui()

    def draw_dot(self, x, color, active):
        if active:
            self.canvas.create_oval(x-12, 10, x+12, 34, fill=color, outline="")
        else:
            self.canvas.create_oval(x-12, 10, x+12, 34, fill="#2a2a2a", outline="")

    def update_ui(self):
        self.canvas.delete("all")
        positions = [30, 65, 100]
        self.draw_dot(positions[0], "#ff3b3b", self.state == "MONITORING")
        self.draw_dot(positions[1], "#ffd000", self.state == "HAND")
        self.draw_dot(positions[2], "#00ff88", self.state == "STABLE")
        self.root.update()

    def close(self):
        if self.root:
            self.root.destroy()