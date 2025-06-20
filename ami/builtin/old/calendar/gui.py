import datetime
from typing import List, Dict

from tkinter import Frame, Label, ttk, Canvas

from ami.headspace.core.calendar.cal_config import CalendarConfig
from ami.headspace.core.calendar.common import DateRange, Event
from ami.headspace.core.calendar.google_sync import GoogleAuth

from .json_calendar import JsonCalendar
from ami.headspace.gui import GuiFrame

class Calendar(GuiFrame):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.g_sync = GoogleAuth(self.filesystem.path)
        self.cal_config = CalendarConfig()

        #TODO delete these two lines
        calendar_filepath = self.filesystem / self.yaml.get("calendar_filename", "calendar.json")
        self.cal = JsonCalendar(calendar_filepath)

        self.lowlight_color = '#C3C3C3'
        self.highlight_color = '#666666'

        self.config(bg='black')

    @property
    def color_scheme(self):
        return self.cal_config.color_scheme

    def create_legend(self):
        legend_frame = Frame(self, bg='black')
        legend_frame.grid(row=0, column=0, columnspan=7, sticky='ew', padx=2, pady=2)

        legend = { 'Local': self.cal_config.color_scheme.default, **self.g_sync.user_colors }
        for i, (source, color) in enumerate(legend.items()):
            Canvas(legend_frame, width=20, height=20, bg=color, highlightthickness=0).grid(row=0, column=i*2, padx=(5, 2))
            Label(
                legend_frame,
                text=source,
                bg='black',
                fg=color,
                font=(self.cal_config.font, self.cal_config.font_size+2)
            ).grid(row=0, column=i*2+1, padx=(0, 10), sticky='w')

    def define_render(self) -> None:
        calendar_filepath = self.filesystem / self.yaml.get("calendar_filename", "calendar.json")
        self.cal = JsonCalendar(calendar_filepath)

        today = datetime.datetime.now().date()
        prev_sunday = today - datetime.timedelta(days=today.weekday() + 1)
        prev_sunday_dt = datetime.datetime.combine(prev_sunday, datetime.datetime.min.time())

        days = self.cal_config.days

        dates = self.cal[str(prev_sunday) : str(prev_sunday+datetime.timedelta(days=days-1))]
        events = self.cal.inflate_calendar_events(dates)

        if self.cal_config.g_synced:
            if self.g_sync.is_valid():
                self.logs.debug("Google Sync enabled!")
                gevents = self.g_sync.get_events(date_range=DateRange.from_start(prev_sunday_dt, days=days, timezone=self.cal_config.tz))

                for event in gevents:
                    if str(event.date) in events:
                        events[str(event.date)].append(event)

            else:
                self.logs.warn("Config for Calendar has google sync enabled but the sync check failed!")

        self.create_legend()

        if self.cal_config.mode == 'week':

            for i, date in enumerate(events.keys()):
                date_frame = self.render_date_frame(date, events=events[date])
                date_frame.grid(row=(i // 7) + 1, column=i % 7, padx=2, pady=2, sticky='nsew')
                date_frame.config(borderwidth=1, relief='flat', highlightbackground=self.color_scheme.background, highlightthickness=1)

        elif self.cal_config.mode == 'day':
            self.logs.error("Calendar Mode Days has not been imolemented. Please use Week mode.")
        else:
            self.logs.error(f"Calendar config setting cannot be determinded Literal['week', 'day'] = {self.cal_config.mode}")

    def render_date_frame(self, date, events: List[Event]=[]):
#       frame = Frame(self, width=self.cal_config.width, height=self.cal_config.height, bg='black')
        frame = Frame(self, width=self.cal_config.width, height=self.cal_config.height, bg=self.cal_config.color_scheme.background)
        frame.grid_propagate(False)
        frame.columnconfigure(0, weight=1) 

        def make_event(e):
            if e.time is None:
                return Label(
                    frame,
                    text=e.name,
                    font=(self.cal_config.font, self.cal_config.font_size),
                    bg=e.color,
                    fg='black',
                    wraplength=110,
                    bd=1,
                    relief='solid',
                    padx=2,
                    pady=1,
                    highlightthickness=1,
                    highlightbackground='black'
                )
            else:
                print(f"{e.time} - {type(e.time)}")
                time = e.time.strftime("%I:%M %p").lstrip("0").lower()
                event_frame = Frame(frame, bg=e.color)
                name_label = Label(
                    event_frame,
                    text=e.name,
                    font=(self.cal_config.font, self.cal_config.font_size, 'bold'),
                    bg=e.color,
                    fg='black',
                    wraplength=110,
                    anchor='w'
                )
                time_label = Label(
                    event_frame,
                    text=time,
                    font=(self.cal_config.font, self.cal_config.font_size),
                    bg=e.color,
                    fg='black',
                    anchor='w'
                )
                name_label.pack(fill='x', expand=True)
                time_label.pack(fill='x', expand=True)
                return event_frame

        bg_color = self.color_scheme.active if datetime.datetime.now().strftime('%Y-%m-%d') == date else self.color_scheme.inactive
        calendar_header_kwargs = {
            'font' : (self.cal_config.font, self.cal_config.font_size+2, 'bold'),
            'bg' : bg_color,
            'fg' : 'black',
            'pady': 1
        }

        date = datetime.datetime.strptime(date, '%Y-%m-%d')
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

