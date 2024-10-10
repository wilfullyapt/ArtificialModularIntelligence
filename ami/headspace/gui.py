""" GUI Abstract Base Class

This module defines an abstract base class for creating GUI frames in a tkinter application.
It provides a foundation for building modular and configurable GUI components.

The GuiFrame class serves as a base for creating custom frames with standardized
initialization, rendering, and configuration loading capabilities. It also includes
error handling for invalid placements and missing configurations.

Classes:
    MissingConfigException: Custom exception for missing configuration files.
    InvalidPlacementError: Custom exception for invalid widget placements.
    GuiFrame: Abstract base class for GUI frames.

The module relies on tkinter for GUI components and uses YAML for configuration management.
"""

from pathlib import Path
from tkinter import Frame
from abc import ABC, abstractmethod
from typing import Dict

from ami.headspace.base import Primitive

class MissingConfigException(Exception):
    pass

class InvalidPlacementError(ValueError):
    pass

class GuiFrame(Frame, ABC, Primitive):
    """
    Abstract base class for creating GUI frames in a tkinter application.

    This class provides a foundation for building modular and configurable GUI components.
    It includes standardized initialization, rendering, and configuration loading capabilities,
    as well as error handling for invalid placements and missing configurations.

    Attributes:
        headspace (str): The name of the module's headspace.
        placement (dict): A dictionary containing placement information for the frame.

    Methods:
        define_render: Abstract method to define the render logic for the frame.
        render: Render the frame based on the defined placement.
        redraw: Redraw the frame by destroying all widgets and rendering again.
        load_config: Load configuration from a YAML file.
        _validate_placement: Validate the placement dictionary for widget positioning.
    """

    def __init__(self, parent, *args, **kwargs):
        """
        Initialize the GuiFrame instance.

        Args:
            parent: The parent widget.
            module_directory: The directory containing the module configuration file.
            *args: Additional arguments passed to the Frame constructor.
            **kwargs: Additional keyword arguments passed to the Frame constructor.
        """
        Frame.__init__(self, parent, *args, **kwargs)
        Primitive.__init__(self)

        self.headspace = self.__module__.split('.')[-2]

    @abstractmethod
    def define_render(self) -> None:
        """
        Define the render logic for the frame.

        This module should implemente this method to define the placement of objects in the frame.
        """
        raise NotImplementedError("Subclasses must implement the define_render method.")

    def render(self):
        """
        Render the frame based on the defined placement.

        Raises:
            InvalidPlacementError: If the placement dictionary is invalid.
        """
        self.filesystem.load_config()
        self.placement: dict = self.yaml.get("placement", {})
        self.define_render()

        try:
            placement = self._validate_placement(self.placement)
            self.place(**placement)
        except InvalidPlacementError as e:
            raise InvalidPlacementError(f"Invalid placement: {e}") from e

        self.logs.debug(f"GUI({self.headspace}).render() finished")

    def redraw(self):
        """
        Redraw the frame by destroying all widgets and rendering again.
        """
        for widget in self.winfo_children():
            widget.destroy()
        self.render()

    def _validate_placement(self, placement: Dict[str, str]) -> Dict[str, str]:
        """
        Validate the placement dictionary to ensure it can be used by self.place.
        The placement dictionary can contain either
            - 'relx', 'rely' and 'relwidth', 'relheight'
            -'x', 'y', and 'relwidth', 'relheight'.
        The keyword 'anchor' specifies the anchor point for the placement of the widget.
            - Literals are ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw', 'center'].
            - Default anchor point is 'center'.

        Args:
            placement: The placement dictionary to validate.

        Returns:
            The validated placement dictionary.

        Raises:
            InvalidPlacementError: If the placement dictionary is invalid.
        """
        valid_anchors = ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw', 'center']
        if "anchor" in placement:
            if placement["anchor"] not in valid_anchors:
                raise InvalidPlacementError(f"Invalid anchor value: {placement['anchor']}")
        else:
            placement["anchor"] = "center"

        if "x" in placement and "y" in placement:
            # Check if x and y are present
            if not isinstance(placement["x"], int) or not isinstance(placement["y"], int):
                raise InvalidPlacementError("Values for 'x' and 'y' must be integers")
            return placement

        if "relx" in placement and "rely" in placement:
            # Check if relx and rely are present
            if not isinstance(placement["relx"], float) or not isinstance(placement["rely"], float):
                raise InvalidPlacementError("Values for 'relx' and 'rely' must be floats")
            if not 0 <= float(placement["relx"]) <= 1 or not 0 <= float(placement["rely"]) <= 1:
                raise InvalidPlacementError("Value for 'relx' or 'rely' is out of bounds")
            return placement

        raise InvalidPlacementError("Must specify either absolute or relative placement")
