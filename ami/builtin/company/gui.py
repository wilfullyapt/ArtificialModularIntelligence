import time
from typing import Any

from PyQt6.QtGui import QFont
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QLabel, QGridLayout, QWidget

from ami.headspace import BaseWidget

from .settings import CopmanyDefaultSettings

class CompanyAGIGUI(BaseWidget):
    """ The DateTime builtin Headspace GUI for the AMI project """
    settings_class = CopmanyDefaultSettings
    main_view = False

    def company_analysis_widget(self) -> QWidget:
        wid = QWidget()
        return wid

    def company_analysis_markdown(self) -> str:
        return "# Test\n- this\n- is\n- test\n## sub\n1. one\n2. two"

