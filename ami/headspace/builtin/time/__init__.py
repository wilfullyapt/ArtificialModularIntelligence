"""
__init__.py

This file should not change
Import predefined file for the Headspace

"""

from .gui import Time

def get_gui():
    return Time

__version__ = "0.1.0"


prompt = "This is a long winded prompt with {variables} embbed in it."
