import asyncio
import time
import signal

import_ai_time = time.time()
from ami import AI
from ami.config import Config


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

# ------------------------------------------------------------------------------
#                       DEVELOPER INJECTIONS AND TESTING
    def sim(text_input: str):
        async def internal():
            await asyncio.sleep(1)
            ai.temp_comms.publish("ears.hotword_detected")
            await asyncio.sleep(2)
            ai.temp_comms.publish("ears.recorder_callback", text_input)

        signal.signal(signal.SIGINT, ai.stop)
#       app = ami.ai.ai.create_flask_app(ai.get_modules_part("blueprint"), ai.flask_pipe)
#       ai.flask_manager.start(app)
#       ai.ears.listen()
        ai.attn.start()
#       ai.attn.schedule(ai.process_whisperer())
        ai.attn.schedule(internal())
        ai.gui.run(ai.get_modules_part("gui"))      # The GUI must run in the main thread
        ai.stop() 

    def run_gui():
        signal.signal(signal.SIGINT, ai.stop)
        ai.attn.start()
        ai.gui.run(ai.get_modules_part("gui"))      # The GUI must run in the main thread
        ai.stop() 

#---------------- Manual Testing
    config = Config()
    config.enable_langsmith()

#   sim("remove all appointments for next tuesday")

#   ai.run()
