
from gunicorn.config import argparse

from ami.ai.ai import AI

def get_args():
    parser = argparse.ArgumentParser(description="Artificia lModular Intelligence")

    parser.add_argument(
        '--ai',
        '-a',
        action='store_true',
        default=False,
        help='Just instance the AI'
    )

    return parser.parse_args()

def run_ai_no_process_loop():
    global ai
    ai = AI()
    print(dir(ai))

def run_backend():
    print("No backend yet")

if __name__ == '__main__':

    args = get_args()

    if args.ai:
        run_ai_no_process_loop()

    print(" --- DEV SCRIPT ---")

