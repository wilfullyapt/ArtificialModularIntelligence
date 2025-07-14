# tests/test_path.py
import sys
from pprint import pprint

def test_sys_path():
    pprint(sys.path)
    import PyQt6.QtWidgets
    import pydantic
    print("Imports successful")

if __name__ == '__main__':
    test_sys_path()
