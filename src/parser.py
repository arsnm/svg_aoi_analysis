# parser.py
#
# Module for parsing SVG files in order to then perform AOI extraction and
# analysis. This module provides functions for reading SVG files, extracting the
# relevant elements and preparing the data for further processing.

from xml.etree import ElementTree as ET
from pathlib import Path


class SVGTreeNodeRaw:
    """
    A class representing a raw node in the SVG tree structure.
    Here, "raw" means that the node contains all the information from the SVG
    file, it'll then be processed to extract the relevant information for AOI
    extraction.
    Attributes:
        tag (str): the tag name of the SVG element.
        attributes (dict): a dictionary of the element's attributes and their values.
        children (list): a list of child nodes representing the nested structure
        of the SVG elements.
    """

    def __init__(self,
        tag: str,
        parent: SVGTreeNodeRaw | None = None,
        attributes: dict | None = None,
        children: list[SVGTreeNodeRaw] | None = None,
        text: str | None = None,):
        """Initializes raw SVG tree nodes preserving unmapped native elements gracefully."""
        self.id = id(self)
        self.tag = tag
        self.parent = parent  # allow for faster backtracking when needed
        # (is None for the root node).
        self.attributes = attributes if attributes is not None else {}
        self.children = children if children is not None else []
        self.text = text

    def __repr__(self):
        """Generates a base string representation displaying tree cascade visually."""
        return self._build_str()

    def __eq__(self, other):
        """Evaluates pure identity equality asserting precisely memory instance comparisons intuitively."""
        if not isinstance(other, SVGTreeNodeRaw):
            return NotImplemented
        return self.id == other.id

    def _build_str(self, level=0, verbose=False) -> str:
        """Constructs recursive indent-level layout strings sequentially outputting the layout block context logic."""
        indent = "  " * level
        if verbose:
            res = f"{indent}NODE({self.tag}, attrs={self.attributes})"
        else:
            res = f"{indent}NODE({self.tag})"

        for child in self.children:
            res += f"\n{child._build_str(level + 1, verbose)}"
        return res


class SVGTreeRaw:
    """
    A class representing the tree structure of an SVG file.
    Here, "raw" means that the tree contains the raw nodes, see SVGTreeNodeRaw
    for more details.
    Attributes:
        root (SVGTreeNodeRaw): The root node of the SVG tree, containing the tag,
        atrributes, and children of the SVG elements.
    """

    def __init__(
        self, svg_file: Path | None = None, root: SVGTreeNodeRaw | None = None
    ):
        """Initializes the SVGTreeRaw object by parsing the provided SVG file or using
        a given root node.
        Args:
            svg_file (Path | None): The path to the SVG file to be parsed. If None,
            the tree will be initialized using the provided root node.
            root (SVGTreeNodeRaw | None): A pre-constructed root node for the SVG
            tree. If None, the tree will be initialized by parsing the provided
            SVG file.
        Raises:
            ValueError: If neither svg_file nor root is provided, or if the root
            element of the SVG file is not 'svg'.
        Warnings:
            If both svg_file and root are provided, the svg_file will be parsed and
            the root node will be ignored. It is recommended to provide only one of
            the arguments to avoid confusion.
        """
        if svg_file is not None:
            tree = ET.parse(svg_file)
            _root = tree.getroot()
            tag = _root.tag.split("}")[-1]
            if tag != "svg":
                raise ValueError(f"Expected root element to be 'svg', but got '{tag}'")
            self.root = SVGTreeRaw._build_svg_tree_rec(_root)
        elif root is not None:
            self.root = root
        else:
            raise ValueError(
                "Either svg_file or root must be provided to initialize SVGTreeRaw."
            )

    def __repr__(self):
        """Yields visual encapsulation wrapper directly identifying its core origin."""
        return f"SVGTree({self.root})"

    @staticmethod
    def _build_svg_tree_rec(
        element: ET.Element, parent: SVGTreeNodeRaw | None = None
    ) -> SVGTreeNodeRaw:
        """
        Static method that recursively builds a tree structure from the given
        SVG element.
        Args:
            element (xml.etree.ElementTree.Element): The SVG element to be parsed.
        Returns:
            A tree structure representing the SVG elements and their relationships.
        """
        tag = element.tag.split("}")[-1]  # Remove namespace if present
        text_content = "".join(element.itertext()).strip() if tag == "text" else element.text
        node = SVGTreeNodeRaw(tag=tag, parent=parent, attributes=element.attrib, text=text_content)

        for child in element:
            node.children.append(SVGTreeRaw._build_svg_tree_rec(child, parent=node))

        return node

    def _iterate_nodes(self, node: SVGTreeNodeRaw | None = None):
        """
        A generator function that iterates through all nodes in the SVG tree.
        Args:
            node (SVGTreeNode | None): The current node being processed. If None,
            the iteration starts from the root node.
        Yields:
            Each node in the SVG tree, allowing for traversal and processing of
            the tree structure.
        """
        if node is None:
            node = self.root
        yield node
        for child in node.children:
            yield from self._iterate_nodes(child)

    def clean_non_visual_tags(self):
        """
        Removes all nodes from the SVG tree that are not visual elements (e.g.,
        <def>, <metadata>, etc.). This is done to simplify the tree structure
        and focus on the elements relevant for AOI extraction.
        """
        for node in self._iterate_nodes():
            if node.tag in {
                "defs",
                "metadata",
                "title",
                "desc",
                "style",
                "script",
                "clipPath",
                "mask",
                "pattern",
                "marker",
                "filter",
                "linearGradient",
                "radialGradient",
            }:
                node.children.clear()  # Remove all children of non-visual tags
                if node.parent is not None:  # Never occurs for the root node,
                    # just here for safety
                    node.parent.children.remove(node)

    def clean_misc_tags(self):
        """
        Removes some tags that are we don't plan to consider for
        AOI extraction at first, to prototype and simplify the tree
        structure.
        NOTE: This might be removed later on when we want to consider more
        complex SVG/AOI structures.
        """
        for node in self._iterate_nodes():
            if node.tag in {
                "tspan",
            }:
                node.children.clear()  # Remove all children of these tags
                if node.parent is not None:  # Never occurs for the root node,
                    # just here for safety
                    node.parent.children.remove(node)

    def clean_empty_groups(self):
        """
        Removes all empty <g> nodes from the SVG tree. This is done to further
        simplify the tree structure and focus on the elements relevant for AOI
        extraction.
        """
        for node in self._iterate_nodes():
            if node.tag == "g" and not node.children:
                if node.parent is not None:  # Never occurs for the root node, just
                    # here for safety
                    node.parent.children.remove(node)

    def clean_tree(self):
        """
        Cleans the SVG tree by removing non-visual tags and empty groups. This
        method is a convenience function that combines the cleaning steps to
        prepare the tree for AOI extraction.
        """
        self.clean_non_visual_tags()
        self.clean_misc_tags()
        self.clean_empty_groups()


if __name__ == "__main__":
    from .utils import normalize_path

    svg_path = normalize_path("../data/svg/B-a-1.svg")
    svg_tree = SVGTreeRaw(svg_path)
    svg_tree.clean_tree()
    print(svg_tree)
