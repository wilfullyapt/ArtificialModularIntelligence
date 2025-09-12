"""
__init__.py for a AMI Headspace Plugin

The standard convention is to define the import to one of the three runtimes,
[ 'GUI', 'Headspace', 'Blueprint' ]

Secondarily there shoule be a List of examples prompts so AI understands the context to route to this Headspace
"""

# Lazy imports to avoid GUI and circular dependencies in headless environments
def __getattr__(name):
    """Lazy import components on demand"""
    if name == "Headspace":
        try:
            from .headspace import CorespaceHeadspace as Headspace
            return Headspace
        except ImportError:
            return None
    elif name == "Blueprint":
        from .blueprint import CorespaceBlueprint as Blueprint
        return Blueprint
    elif name == "GUI":
        from .gui import CorespaceGUI as GUI
        return GUI
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


EXAMPLES = [
    "Set a timer for 5 minutes",
    "What's today's date?",
    "Set a reminder for this thursday to <do something>",
    "Set a reoccurring reminder to <do something>. Every three months starting tomorrow.",
    "Can you tell me about ...",
    "Can you explain to me ...",
    "Perform an update",
]

__version__ = "0.1.0"

__all__ = [
    "Blueprint", 
    "GUI",
    "Headspace",
    "EXAMPLES",
]
