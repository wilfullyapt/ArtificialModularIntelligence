"""Public AMI headspace template — copy, rename id, implement tools."""

from .headspace import DemoHeadspace as Headspace

EXAMPLES = [
    "Say hello with the demo headspace",
    "Echo a short message through demo tools",
]

__version__ = "0.1.0"

__all__ = ["Headspace", "EXAMPLES", "__version__"]
