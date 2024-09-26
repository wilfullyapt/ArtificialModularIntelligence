""" GUI for AMI """

from tkinter import Tk, Frame, Label
from tkinter.ttk import Style, Progressbar
from pathlib import Path
from typing import Any, Callable, Generator, List

from PIL import ImageTk, Image

from ami.base import Base

class TimeoutBar(Progressbar):
    """ 
    Represents a progress bar with a countdown timer.

    This class extends the Progressbar widget from tkinter.ttk and provides
additional functionality for displaying a countdown timer with a callback
    function that is executed when the timer expires.

    Attributes:
        interval (int): The interval in milliseconds at which the progress bar
            is updated.
        callback (Callable or None): The function to be called when the timer
            expires. If None, no function is called.
    """

    def __init__(self, parent, width=100, interval=50):
        """ 
        Represents a progress bar with a countdown timer.

        This class extends the Progressbar widget from tkinter.ttk and provides
        additional functionality for displaying a countdown timer with a callback
        function that is executed when the timer expires.

        Args:
            parent (tkinter.Widget): The parent widget for the progress bar.
            width (int, optional): The width of the progress bar in pixels. Defaults to 100.
            interval (int, optional): The interval in milliseconds at which the progress bar
                is updated. Defaults to 50.

        Attributes:
            interval (int): The interval in milliseconds at which the progress bar
                is updated.
            callback (Callable or None): The function to be called when the timer
                expires. If None, no function is called.
        """
        super().__init__(parent, mode='determinate', length=width-4)
        self.interval = interval
        self.callback = None

        style = Style()
        style.theme_use('default')
        style.layout('Horizontal.Progressbar',
                     [('Horizontal.Progressbar.trough',
                       {'children': [('Horizontal.Progressbar.pbar',
                                      {'side': 'right', 'sticky': 'ns'})],
                        'sticky': 'nswe'}),
                      ('Horizontal.Progressbar.label', {'sticky': ''})])
        style.configure('Horizontal.Progressbar',
                        thickness=10,
                        troughcolor='red',
                        foreground='black',
                        background='black',
                        borderwidth=0)
        style.map('Horizontal.Progressbar',
               background=[('disabled', 'black'), ('active', 'black')],
               foreground=[('disabled', 'black'), ('active', 'red')])

        self.configure(style='Horizontal.Progressbar')

    def start_timeout(self, countdown, callback=None):
        """ 
        Start a countdown timer with a specified duration and an optional callback function.

        Args:
            countdown (int): The duration of the countdown timer in seconds.
            callback (Callable, optional): The function to be called when the timer expires.
                If not provided, no function will be called.
        """
        self.callback = callback
        self['maximum'] = countdown*1000
        self.update_progress(countdown*1000)

    def update_progress(self, current_progress):
        """ 
        Update the progress bar with the current progress value.

        Args:
            current_progress (int): The current progress value to be displayed on the progress bar.
        """
        self['value'] = current_progress
        current_progress -= self.interval
        if current_progress >= 0:
            self.after(self.interval, self.update_progress, current_progress)
        else:
            self.reset()

    def reset(self):
        """ 
        Reset the progress bar to its initial state.

        This method is called when the countdown timer expires or when the progress bar needs to be
        reset to its initial state. If a callback function was provided when starting the countdown
        timer, it is called after resetting the progress bar.
        """
        if isinstance(self.callback, Callable):
            self.after(0, self.callback)
        else:
            self['value'] = self['maximum']

class AIDialogWindow(Frame):
    """
    A graphical user interface (GUI) window for displaying a dialog between a human and an AI.

    This class creates a popup window that displays the conversation between a human and an AI.
    It provides methods for rendering the window, displaying messages from the human and AI,
    and handling visual elements such as images.

    Attributes:
        parent (tk.Tk): The root window or parent widget.
        width (int): Width of the popup window in pixels.
        height (int): Height of the popup window in pixels.
        timeout_bar (TimeoutBar): The timeout bar that countdowns til the popup closes.
        target (tk.Label): Changes the target for text rendering in conjunction with the AI class.
    """

    def __init__(self, parent, width: int=500, height: int=700) -> None:
        """
        Initialize the AIDialogWindow.

        Args:
            parent (tk.Tk): The root window or parent widget.
            width (int): Width of the popup window in pixels. Defaults to 500.
            height (int): Height of the popup window in pixels. Defaults to 700.
        """
        super().__init__(parent)
        self.parent = parent
        self._popup: Frame | None = None
        self.timeout_bar: TimeoutBar | None = None

        self.target: Label | None = None
        self._loading_status = 0
        self._loading_spinner = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
        self._loading_message = "Loading ..."
        self._loading_flag = False

        self.load_interval = 150
        self.border_color = '#666666'
        self.text_size = 14
        self.width = width
        self.height = height

    @property
    def loading_message(self):
        """ 
        Returns the current loading message with a spinning animation.

        The loading message is a string that displays a spinning animation and a custom message.
        The animation cycles through a set of characters, and the message can be customized by
        setting the `loading_message` attribute.

        Returns:
            str: The current loading message with the spinning animation.
        """
        self._loading_status += 1
        if self._loading_status not in range(len(self._loading_spinner)):
            self._loading_status = 0

        return f"{self._loading_spinner[self._loading_status]} {self._loading_message}"

    @loading_message.setter
    def loading_message(self, message):
        """ 
        Sets the loading message to be displayed on the progress bar.

        Args:
            message (str): The message to be displayed during the loading process.
        """
        self._loading_message = message

    def _set_loading_message(self, message):
        """ 
        Sets the loading message to be displayed on the progress bar.

        Args:
            message (str): The message to be displayed during the loading process.
        """
        self.loading_message = message

    def set_loading_message(self, message:str):
        """ 
        Sets the loading message to be displayed on the progress bar.

        Args:
            message (str): The message to be displayed during the loading process.
        """
        self._after(0, self._set_loading_message, message)

    def generat_role_label(self, role: str) -> Label:
        """ 
        Generate a label displaying the given role.

        Args:
            role (str): The role to be displayed on the label.

        Returns:
            Label: A tkinter Label widget displaying the role.
        """
        role = role.upper()
        if role == 'AI':
            color = 'blue'
        elif role == 'HUMAN':
            color = 'green'
        else:
            color = 'red'
        return Label(self._popup,
                        text=role.upper(),
                        bg='black',
                        fg=color,
                        font=('Arial', self.text_size, 'bold'),
                        anchor='ne',
                        padx=8,
                        justify='right')

    def generat_text_label(self, parent=None):
        """
        Generate a text label widget.

        Args:
            parent (tkinter.Widget, optional): The parent widget for the text label.
            If not provided, the label will be created as a child of the popup window.

        Returns:
            tkinter.Label: A tkinter Label widget displaying text.
        """
        if parent is None:
            parent = self._popup
        return Label(parent,
                        text=" ... ",
                        bg="black",
                        fg="white",
                        font=("Arial", self.text_size),
                        wraplength=300,
                        justify="left")

    def load_target(self):
        """
        Update the target label with the current loading message and schedule the next update.

        This method updates the text of the target label with the current loading message.
        It then schedules the next update to occur after the specified load interval by
        calling itself recursively using the `after` method of the target label.

        The method only performs the update if both the target label and the loading flag
        are set. If either of these conditions is not met, the method does nothing.
        """
        if self.target and self._loading_flag:
            self.target.config(text=self.loading_message)
            self.target.after(self.load_interval, self.load_target)

    def init_listening(self):
        """ Render the popup and put the feedback on the screen """
        self.render()
        self.focus = "HUMAN"
        human_label = self.generat_role_label(self.focus)
        text_label = self.generat_text_label()
        row = self._popup.grid_size()[-1]
        human_label.grid(row=row, column=0, sticky="ne")
        text_label.grid(row=row, column=1, sticky="nw")

        self.target = text_label
        self.loading_message = "Listening ..."
        self._loading_flag = True
        self.load_target()

    def human_message(self, text: str):
        """
        Print the Human message to the AI on screen, return if the popup isn't on screen.

        Args:
            text (str): What the human said to the AI
        """
        if self._popup is None:
            return

        if self.focus == "HUMAN" and self.target:
            self._loading_flag = False
            self.target.config(text=text)
        else:
            print("Human message just fucked up")
        self.ai_message()

    def ai_message(self):
        """ Initialize the AI message, return if the popup isn't on screen """
        if self._popup is None:
            return

        self.focus = "AI"
        ai_label = self.generat_role_label(self.focus)
        text_label = self.generat_text_label()
        row = self._popup.grid_size()[-1]
        ai_label.grid(row=row, column=0, sticky="ne")
        text_label.grid(row=row, column=1, sticky="nw")

        self.target = text_label
        self.loading_message = "Thinking ..."
        self._loading_flag = True
        self.load_target()

    def ai_dialog(self, dialog):
        """
        Display the AI's response in the dialog window.

        Args:
            dialog (Dialog): An instance of the Dialog class containing the AI's response
                             and other relevant information.
        """
        if self._popup is None:
            return
        self._loading_flag = False
        payload = dialog.convo[-1][-1]
        if isinstance(payload, str):
            self.target.config(text=payload)
        if isinstance(payload, Callable):
            self.target.config(text=payload())
        elif isinstance(payload, Generator):
            self.target.config(text="")
            for chunk in payload:
                self.target.config(text=self.target.cget('text') + chunk)
                self.target.update()
        dialog.convo[-1] = ('AI', self.target.cget('text'))

        if isinstance(dialog.visual, str):
            dialog.visual = Path(dialog.visual)

        if isinstance(dialog.visual, Path):
            if dialog.visual.is_file():
                # Load the image from the file path
                image = Image.open(dialog.visual)
                image = image.resize((150, 150), Image.Resampling.LANCZOS)
                pic = ImageTk.PhotoImage(image)

                label_grid_info = self.target.grid_info()
                text = self.target.cget("text")
                sub_frame = Frame(self._popup, padx=0, pady=0)
                sub_frame.grid(row=label_grid_info["row"], column=label_grid_info["column"])

                self.target.grid_remove()
                self.target = self.generat_text_label(sub_frame)
                self.target.config(text=text)
                self.target.grid(row=0, column=0)

                image_label = Label(sub_frame, image=pic, padx=10, pady=10, bg='black', fg='black')
                image_label.image = pic
                image_label.grid(row=1, column=0)

        self.parent.redraw(dialog.headspace)
        self.timeout_bar.start_timeout(dialog.timeout, callback=self._close)

    def set_human_message(self, message:str):
        """ Hand off method for outside access to self.human_message via the tkinter Queue """
        self._after(0, self.human_message, message)

    def set_ai_response(self, dialog):
        """ Hand off method for outside access to self.ai_dialog via the tkinter Queue """
        self._after(0, self.ai_dialog, dialog)

    def _after(self, *args, **kwargs) -> None:
        """ Inner `after` function to the AIDialog specific to the popup """
        if self._popup is not None:
            self._popup.after(*args, **kwargs)

    def render(self) -> None:
        """ Create and display the popup """
        if self._popup is not None:
            return

        self._popup = Frame(self.parent)
        self._popup.config(width=self.width,
                    height=self.height,
                    bg='black',
                    borderwidth=1,
                    relief='flat',
                    highlightbackground=self.border_color,
                    highlightthickness=1)
        self._popup.grid_propagate(False)

        self._popup.place(relx=0.5, rely=0.5, anchor='center')
        self._popup.lift()

        self.timeout_bar = TimeoutBar(self._popup, width=self.width)
        self.timeout_bar.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        self.timeout_bar.rowconfigure(0, weight=0)
        self.timeout_bar.reset()

    def _close(self):
        """ Close the popup """
        if self._popup is None:
            return
        self._popup.destroy()
        self._popup = None
        self.parent.temp_comms.publish("gui.interaction_finished")

    def close(self):
        """ Public facing close method """
        self._after(0, self._close)

class GUI(Tk, Base):
    """
    The GUI defines the visual interface with the AI.
    Allows drawing of abstract child tk.Frame and reloading of the same.


    Attributes:
        popup (AIDialogWindow): This is the popup window for visual indication with the AI.
    """
    def __init__(self, temp_comms, *args, **kwargs):
        """ Initialize the GUI """
        Tk.__init__(self, *args, **kwargs)
        Base.__init__(self)

        self.temp_comms = temp_comms
        self.popup = AIDialogWindow(self)

        self.title('Artificial Modular Intelligence')
        self.config(background='black')
        self.attributes('-fullscreen', True)
        self.withdraw()

    def create_popup(self):
        """ Start the popup interaction """
        self.after(0, self.popup.init_listening)

    async def human_input(self, message):
        """ Send a human message to the popup """
        self.popup.human_message(message)

    def redraw(self, headspace: str):
        """ Redraw a child headspace given only the headspace name for the child Frame """
        for child in self.winfo_children():
            if hasattr(child, 'headspace'):
                if child.headspace.capitalize() == headspace.capitalize():
                    child.redraw()

    def reload_child(self, child_name: str):
        """ Reload a child headspace given only the headspace name for the child Frame """
        for child in self.winfo_children():
            if hasattr(child, 'headspace') and child.headspace == child_name:
                self.after(0, child.redraw)
                self.logs.info(f"GUI.realod_child({child_name})")
            else:
                self.logs.warn(f"Failed to realod_child({child_name})")

    def instance_children(self, children: List[Any]):
        """ Create and render a list of children on the GUI

            Args:
                children (List[child_of 'AMI.headspace.GUI']): List of uninstanced objects based on
                                                               Headspace GUI objects.
        """
        for child in children:
            c = child(self)
            c.render()
            self.logs.info(f"GUI child({c}) rendered!")

    def run(self, children: List[Any]):
        """ Load the children objects on the GUI and run.

            Args:
                children (List[child_of 'AMI.headspace.GUI']): see instance_children
        """
        self.instance_children(children)
        self.deiconify()
        self.logs.info("GUI running!")
        self.mainloop()

    def stop(self):
        """ Stop the GUI """
        self.withdraw()
        self.quit()
        self.logs.info("GUI stopped!")
