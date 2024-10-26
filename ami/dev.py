import asyncio
from functools import partial
import time
import signal
from pathlib import Path
from pprint import pprint as pp
from datetime import datetime, timedelta

from ami.flask.manager import create_flask_app
from ami.headspace.core.calendar.cal_config import CalendarConfig
from ami.headspace.core.calendar.google_sync import DateRange

import_ai_time = time.time()
from ami import AI
from ami.config import Config

# ------------------------------------------------------------------------------
#                       DEVELOPER INJECTIONS AND TESTING
def sim(text_input: str):
    async def internal():
        await asyncio.sleep(1)
        ai.temp_comms.publish("ears.hotword_detected")
        await asyncio.sleep(2)
        ai.temp_comms.publish("ears.recorder_callback", text_input)

    signal.signal(signal.SIGINT, ai.stop)
#   app = ami.ai.ai.create_flask_app(ai.get_modules_part("blueprint"), ai.flask_pipe)
#   ai.flask_manager.start(app)
#   ai.ears.listen()
    ai.attn.start()
#   ai.attn.schedule(ai.process_whisperer())
    ai.attn.schedule(internal())
    ai.gui.run(ai.get_modules_part("gui"))      # The GUI must run in the main thread
    ai.stop()

def run_gui():
    signal.signal(signal.SIGINT, ai.stop)
    ai.attn.start()
    ai.gui.run(ai.get_modules_part("gui"))      # The GUI must run in the main thread
    ai.stop()

def run_server(ai):
    ai.attn.start()
    ai.attn.schedule(ai.process_whisperer())
    app = create_flask_app(ai.get_modules_part("blueprint"), ai.flask_pipe)
    ai.flask_manager.start(app)

def restart_server(ai):
    ai.flask_manager.stop()
    print(" -- SLEEPER, YOU ARE -- ")
    time.sleep(1)
    print(" -- SLEEPER, YOU ARE NOT -- ")
    run_server(ai)

if __name__ == '__main__':
    f = __file__

# ------------------------------------------------------------------------------
#                       INITIALIZE AI
    instance_ai_time = time.time()
    ai = AI()
    end_time = time.time()

    time_to_import = instance_ai_time - import_ai_time
    time_to_instance = end_time - instance_ai_time
    print("\n\033[91m -::->> Builder mode activated.\033[0m")
    print(f"\033[91m  -:- Import time: {time_to_import:.2f} seconds.\033[0m")
    print(f"\033[91m  -:- Instance time: {time_to_instance:.2f} seconds.\033[0m", end="\n\n")

    runserver = partial(run_server, ai)
    restartserver = partial(restart_server, ai)

#---------------- Manual Testing
    config = Config()
    config.enable_langsmith()

#   sim("remove all appointments for next tuesday")

#   ai.run()

#   help(ai.brain["calendar"].__class__)


#---------------- #TODO Self Testing. DELETE ME.

    today = datetime.now().date()
    prev_sunday = today - timedelta(days=today.weekday() + 1)
    prev_sunday_dt = datetime.combine(prev_sunday, datetime.min.time())

    cal_config = CalendarConfig()
    days = cal_config.days
    dr = DateRange.from_start(prev_sunday_dt, days=days, timezone=cal_config.tz)

    auth = ai.brain['calendar'].auth

    gevents = auth.get_events(date_range=dr)

    cal = ai.get_modules_part('gui')[-1](ai.gui)
    dates = cal.cal[str(prev_sunday) : str(prev_sunday+timedelta(days=days-1))]
    events = cal.cal.inflate_calendar_events(dates)

