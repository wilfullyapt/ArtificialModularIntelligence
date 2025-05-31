import re
import hashlib
import pickle
from functools import reduce
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field

from ami.headspace.base import SharedTool
from ami.headspace.filesystem import Filesystem

INDENT = 2
indent = lambda line, indent : f"{''.join([' ']*indent)}{line}"

@dataclass
class YAMLNode:
    """
    Represents a node in a YAML structure.

    Attributes:
        key (Optional[str]): The key of the YAML node.
        value (Any): The value of the YAML node.
        children (List['YAMLNode']): List of child nodes.
        indent (int): The indentation level of the node.
        line_number (int): The line number of the node in the YAML file.
        node_type (Any): The type of the node (e.g., str, list, dict).
    """
    key: Optional[str] = None
    value: Any = None
    children: List['YAMLNode'] = field(default_factory=list)
    indent: int = 0
    line_number: int = 0
    node_type: Any = None
    def __post_init__(self):
        if isinstance(self.value, str):
            self.value = self._convert_value(self.value)

    @staticmethod
    def _convert_value(value: str) -> Any:
        """
        Converts a string value to an appropriate Python type.

        Args:
            value (str): The string value to convert.

        Returns:
            Any: The converted value (bool, None, float, int, or str).
        """
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        elif value.lower() == 'none':
            return None
        elif '.' in value:
            try:
                return float(value)
            except ValueError:
                return value
        else:
            try:
                return int(value)
            except ValueError:
                return value

    def __contains__(self, key: str) -> bool:
        """
        Checks if a key exists in the node's children.

        Args:
            key (str): The key to search for.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        return any(child.key == key for child in self.children)

    def __getitem__(self, value: str):
        """
        Retrieves a child node by its key.

        Args:
            value (str): The key of the child node to retrieve.

        Returns:
            YAMLNode: The child node with the specified key.

        Raises:
            KeyError: If the key is not found in the YAML structure.
        """
        for child in self.children:
            if child.key == value:
                return child
        raise KeyError(f"Key '{value}' not found in YAML structure")

    def get(self, value: str):
        """
        Retrieves the value of a child node by its key.

        Args:
            value (str): The key of the child node to retrieve.

        Returns:
            Any: The value of the child node, which can be a string, list, or dictionary.

        Raises:
            KeyError: If the key is not found in the YAML structure.
        """
        for child in self.children:
            if child.key == value:
                if child.node_type is str:
                    return child.value
                elif child.node_type is list:
                    return [ list_child.value for list_child in child.children ]
                elif child.node_type is dict:
                    return child
        raise KeyError(f"Key '{value}' not found in YAML structure")

    def update(self, keys: List[str], value: Any, lineno: int):
        """
        Updates the value of a node or its children. Comments left out for verbose troubleshooting.

        Args:
            keys (List[str]): The list of keys to navigate the YAML structure.
            value (Any): The new value to set.
            lineno (int): The line number of the update.

        Raises:
            NotImplemented: If the update is not implemented for list element node updates.
        """
        bool_check = lambda x: str(x).lower() if isinstance(x, bool) else x
        converter = lambda x : x if not isinstance(x, str) else self._convert_value(x)
        if self.node_type is None and self.key is None:
            raise NotImplemented("YAMLNode.update is not implemented for list element node updates.")

#       print(f" -:- {self.key}: {keys}: {value}")
        value = bool_check(converter(value))
        if self.children:
            for child in self.children:
                if self.node_type is list:
                    if child.line_number == lineno and child.value != value:
#                       print(f"<Node({self.key}, lineno[{child.line_number}, {lineno}])> value updated. {child.value}->{value}")
                        child.value = value
                elif self.node_type is dict:
                    if child.key == keys[0]:
                        child.update(keys[1:], value, lineno)

        elif self.line_number == lineno and not any(keys):
            value = converter(value)
            if self.value != value:
#               print(f"<Node({self.key}, lineno[{self.line_number}, {lineno}])> value updated. {self.value}->{value}")
                self.value = value

#       else: print(f" --- {keys}: {value}: {lineno}")

    def in_order(self):
        """ Returns the value of the node in order. """
        if self.children:
            for child in self.children:
                return child.in_order()
        else:
            return self.value

    def as_item(self):
        """ Matching tuple yield function for PerfectYAML. """
        if self.children:
            return [ ( child.line_number, child.key, child.as_item()) for child in self.children ]
        else:
            return str(self.value)

def parse_key(value: str) -> Tuple[Union[int, None], List[str]]:
    """ Extract stuff """
    number_match = re.search(r'\((\d+)\)$', value)
    number = int(number_match.group(1)) if number_match else None
    clean_key = re.sub(r'\(\d+\)$', '', value)

    key_parts = [part for part in clean_key.split('.')]
    return (number, key_parts)

class PerfectYAML:
    """
    Represents a YAML file and provides methods for parsing, updating, and saving YAML content.

    Attributes:
        filepath (Path): The path to the YAML file.
        lines (List[str]): The lines of the YAML file.
        line_count (int): The total number of lines in the YAML file.
        root (YAMLNode): The root node of the YAML structure.
    """
    def __init__(self, yaml_filepath: Path):
        """
        Initialize the PerfectYAML object.

        Args:
            yaml_filepath (Path): The path to the YAML file.

        This method:
        1. Reads the YAML file and stores its contents.
        2. Initializes attributes for comments and blank lines.
        3. Parses the YAML structure.
        4. Sets the initial state of the object.
        """
        self.filepath = yaml_filepath

        with open(yaml_filepath, 'r') as file:
            self.lines = [line.rstrip() for line in file.readlines()]

        self.line_count = len(self.lines)
        self._comments = []
        self._blanks = []

        self.root = YAMLNode()
        self._parse()

        self._state = self.state

    def __repr__(self):
            """ Return a string containing the object's class name, file path, and memory address. """
            return f"<PerfectYaml[{self.filepath.parent.name}/{self.filepath.name}] object at {hex(id(self))}>"

    def __contains__(self, key: str) -> bool:
        """
        Check if a key exists in the root of the YAML structure.

        Args:
            key (str): The key to check for.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        return key in self.root

    def __getitem__(self, value: str) -> YAMLNode:
        """
        Access a child node using square bracket notation.

        Args:
            value (str): The key of the child node to retrieve.

        Returns:
            YAMLNode: The child node with the specified key.

        Raises:
            KeyError: If the key is not found in the YAML structure.
        """
        return self.root[value]

    @property
    def state(self):
        """ Get the current state of the PerfectYAML object. """
        thing1 = None
        if hasattr(self, '_state'):
            thing1 = self._state
            del self._state

        thing2 = hashlib.md5(pickle.dumps(self)).hexdigest()
        if thing1 is not None:
            self._state = thing2
        return thing2

    def get(self, value: str) -> YAMLNode:
        """
        Retrieve a child node by its key.

        Args:
            value (str): The key of the child node to retrieve.

        Returns:
            YAMLNode: The child node with the specified key.

        Raises:
            ValueError: If the key is not found in the YAML structure.
        """
        try:
            return self.root[value]
        except KeyError:
            raise ValueError(f"Key '{value}' not found in YAML structure")

    def update(self, key: str, value: str):
        """
        Update the value of a node or its children in the YAML structure.

        Args:
            key (str): The key path to the node to be updated.
            value (str): The new value to set.

        This method parses the key, finds the corresponding node, and updates its value.
        """
        lineno, keys = parse_key(key)
        if keys[0] in self:
            passed_keys = [None if k == 'None' else k for k in keys[1:]]
            self[keys[0]].update(passed_keys, value, lineno)

    def as_items(self):
        """
        Yields tuples of (lineno, key, value) recursively for the yaml file.
        The iteration through these values is in line order.
        Examples:
            str:  #, key, value
            dict: #, key, [(#, key, value), (#, key, value), [(#, key, value)]] *recursively*
            list: #, key, [(#, None, value), (#, None, Value)]
        """
        for child in self.root.children:
            yield child.line_number, child.key, child.as_item()

    def get_comment(self, idx):
        """
        Retrieve a comment for a given line number.

        Args:
            idx (int): The line number to get the comment for.

        Returns:
            str: The comment for the given line number, or None if no comment exists.
        """
        for comment in self._comments:
            if comment[0] == idx:
                return comment[-1]
        return None

    def in_order(self) -> List[str]:
        """
        Get a list of keys in the order they appear in the YAML file.

        Returns:
            List[str]: A list of keys sorted by their line numbers in the YAML file.
        """
        order = [(child.key, child.line_number) for child in self.root.children]
        sorted_order = sorted(order, key=lambda x: x[1])
        return [item[0] for item in sorted_order]

    def _parse(self):
        stack = [self.root]
        current_indent = 0

        for line_number, line in enumerate(self.lines, start=1):
            stripped = line.strip()

            if stripped.startswith('#'):
                self._comments.append((line_number, line))
                continue

            if not stripped:
                self._blanks.append(line_number)
                continue

            indent = len(line) - len(line.lstrip())
            if indent > current_indent:
                stack.append(stack[-1].children[-1])
            elif indent < current_indent:
                while indent < current_indent:
                    stack.pop()
                    current_indent = stack[-1].indent

            current_indent = indent

            if ':' in stripped:
                key, value = stripped.split(':', 1)
                key = key.strip()
                value = value.strip()
                if value:
                    node = YAMLNode(key=key, value=value, indent=indent, line_number=line_number, node_type=str)
                else:
                    node = YAMLNode(key=key, indent=indent, line_number=line_number, node_type=dict)
                stack[-1].children.append(node)
            elif stripped.startswith('-'):
                stack[-1].node_type = list
                value = stripped[1:].strip()
                node = YAMLNode(value=value, indent=indent, line_number=line_number)
                stack[-1].children.append(node)

    def to_dict(self):
        def node_to_dict(node: YAMLNode) -> dict:

            if node.node_type is dict:
                return { node.key: reduce(lambda x, y: {**x, **y}, [ node_to_dict(child) for child in node.children ]) }

            if node.node_type is list:
                return { node.key: [ child.value for child in node.children ] }

            if node.node_type is str:
                return { node.key: node.value }

        yaml_dict = {}
        for child in self.root.children:
            child_as_dict = node_to_dict(child)
            if child_as_dict:
                yaml_dict.update(child_as_dict)

        return yaml_dict

    def to_yaml(self) -> List[str]:
        def make_line_from_node(node):
            if node.value is not None:
                if node.key:
                    if isinstance(node.value, bool):
                        return (node.line_number, indent(f"{node.key}: {str(node.value).lower()}", node.indent))
                    else:
                        return (node.line_number, indent(f"{node.key}: {node.value}", node.indent))
                else:
                    return (node.line_number, indent(f"- {node.value}", node.indent))
            else:
                return (node.line_number, indent(f"{node.key}:", node.indent))

        def extract_lines(node: YAMLNode):
            result = [ make_line_from_node(node) ]
            if node.children:
                for child in node.children:
                    result.extend(extract_lines(child))
            return result

        yaml_lines = [''] * self.line_count

        for comment in self._comments:
            yaml_lines[comment[0]-1] = comment[-1]

        for item in self.in_order():
            node = self.get(item)
            lines = extract_lines(node)
            for line in lines:
                yaml_lines[line[0]-1] = line[-1]

        for blank in self._blanks:
            if yaml_lines[blank-1] != '':
                print(f"Missing Blank Line on {blank-1}!")

        return yaml_lines

    def save(self):
        """ Save the current YAML content back to the file. """
        if self._state != self.state:
            yaml_lines = self.to_yaml()
            with open(self.filepath, 'w') as file:
                for line in yaml_lines:
                    file.write(line + '\n')
            self._state = self.state

class Utils(SharedTool):
    """
        Utils include the following functionality:
        - Config editor: Modify YAML files without sacrificing their human-readibility
        - Self Updating: Allow the project to self `git pull` and restart with troubleshooting
        - Alarms?
        - Reminders?
        - ???
    """

    def __init__(self):
        local_config_path = Path(__file__).parent / "config.yaml"

        self.pyaml = PerfectYAML(local_config_path)

        self.filesystem = Filesystem("markdown")


