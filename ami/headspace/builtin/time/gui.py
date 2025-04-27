import time
from pathlib import Path
from tkinter import Label

from ami.headspace.gui import GuiFrame

class Time(GuiFrame):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.config(bg='black')

        font: str = self.yaml.get("font", "Arial")
        highlight_color: str = self.yaml.get("highlight_color", "#C3C3C3")
        lowlight_color: str = self.yaml.get("lowlight_color", "#666666")

        self.date_label = Label(self, font=(font, 26), fg=highlight_color, bg='black')
        self.time_label = Label(self, font=(font, 28), fg=highlight_color, bg='black')
        self.seconds_label = Label(self, font=(font, 18), fg=lowlight_color, bg='black')
        self.am_pm_label = Label(self, font=(font, 24), fg=lowlight_color, bg='black')

    def update_time(self):
        self.date_label.config(text=time.strftime('%A %B %d, %Y'))
        self.time_label.config(text=time.strftime('%I:%M'))
        self.seconds_label.config(text=time.strftime(':%S'))
        self.am_pm_label.config(text=time.strftime('%p'))
        self.after(1000, self.update_time)

    def define_render(self):
        self.date_label.grid(row=0, column=0, columnspan=3)
        self.time_label.grid(row=1, column=0, sticky='e', padx=(0, 5))
        self.seconds_label.grid(row=1, column=1, sticky='nw', padx=(0, 5))
        self.am_pm_label.grid(row=1, column=2, sticky='w', padx=(0, 15))

        self.update_time()
