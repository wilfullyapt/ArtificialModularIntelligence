from datetime import datetime, timedelta
from typing import List, Dict 

from tkinter import Frame, Label, ttk

from .calendar import Calendar as CalendarTool
from ami.headspace.gui import GuiFrame

class Calendar(GuiFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.lowlight_color = '#C3C3C3'
        self.highlight_color = '#666666'

        self.config(bg='black')

    def define_render(self) -> None:
        calendar_filepath = self.filesystem / self.yaml.get("calendar_filename", "calendar.json")
        self.cal = CalendarTool(calendar_filepath)

        today = datetime.now().date()
        prev_sunday = today - timedelta(days=today.weekday() + 1)
        days = 21

        dates = self.cal[str(prev_sunday) : str(prev_sunday+timedelta(days=days-1))]
        events = self.cal.inflate_calendar(dates)

        for i, date in enumerate(events.keys()):
            date_frame = self.render_date_frame(date, events=events[date])
            date_frame.grid(row=i // 7, column=i % 7, padx=2, pady=2, sticky='nsew')
            date_frame.config(borderwidth=1, relief='flat', highlightbackground=self.highlight_color, highlightthickness=1)

    def render_date_frame(self, date, events: List[Dict]=[]):
        frame = Frame(self, width=120, height=120, bg='black')
        frame.grid_propagate(False)
        frame.columnconfigure(0, weight=1) 

        def make_event(event_dict):
            style = ttk.Style()
            style.configure('RoundedLabel.TLabel', borderradius=20, background='#E69A28', foreground='black', font=('Verdana', 8), wraplength=80)
            if event_dict['time'] == 'None':
                return ttk.Label(frame, text=event_dict['name'], style='RoundedLabel.TLabel')
            else:
                event_frame = Frame(frame, bg='#E69A28', highlightbackground="#E69A28", highlightthickness=2, highlightcolor="#E69A28")
                time_label = Label(event_frame, text=event_dict['time'], font=('Verdana', 8), bg='#E69A28', fg='black')
                name_label = Label(event_frame, text=event_dict['name'], font=('Verdana', 8), bg='#E69A28', fg='black', wraplength=50)
                time_label.grid(row=0, column=0, sticky='w')
                name_label.grid(row=0, column=1, sticky='e')
                return event_frame

        bg_color = '#BA3696' if datetime.now().strftime('%Y-%m-%d') == date else '#668A76'
        calendar_header_kwargs = { 'font' : ('Verdana', 10), 'bg' : self.highlight_color, 'fg' : 'black'}
        calendar_header_kwargs = { 'font' : ('Verdana', 10), 'bg' : bg_color, 'fg' : 'black'}

        date = datetime.strptime(date, '%Y-%m-%d')
        dom = Label(frame, text=date.day, anchor='w', **calendar_header_kwargs)
        dow = Label(frame, text=date.strftime('%a'), anchor='e', **calendar_header_kwargs)
        dow.grid(row=0, column=1,  sticky='we')
        dom.grid(row=0, column=0, sticky='we')

        row = 1
        for event in events:
            event_widget = make_event(event)
            event_widget.grid(row=row, column=0, columnspan=2, sticky='ew')
            row += 1

        return frame

