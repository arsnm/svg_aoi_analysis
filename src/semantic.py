# semantic.py
#
# Module for assigning semantic meaning to SVG structural elements.  Works as
# the third stage in the pipeline (after parsing and bounding).  Interprets node
# ids, attributes, and relationships to assign roles like 'axis', 'legend',
# 'data', 'grid', etc.

from .parser import SVGTreeRaw, SVGTreeNodeRaw
from .geometry import SVGTreeBounded, SVGTreeNodeBounded
from shapely.geometry import Polygon


class SVGTreeNodeSemantic(SVGTreeNodeBounded):
    """
    A node extending bounded elements wrapping analytical role labels defining
    chart-space meaning.
    """

    def __init__(
        self,
        node: SVGTreeNodeRaw,
        bounding: Polygon | None = None,
        semantic_label: str = "unknown",
        parent: "SVGTreeNodeSemantic | None" = None,
        children: list["SVGTreeNodeSemantic"] | None = None,
    ):
        """
        Initializes the semantic node persisting bounded geometry while
        explicitly injecting recognized classifications.
        """
        super().__init__(
            node=node,
            bounding=bounding,
            parent=parent,
            children=children if children is not None else [],
        )
        self.semantic_label = semantic_label

    def _build_str(self, level=0, verbose=False) -> str:
        """
        Synthesizes a visual representation highlighting purely the logical
        layout tree containing tagged semantics iteratively.
        """
        indent = "  " * level
        if verbose:
            res = f"{indent}NODE({self.tag}, semantic={self.semantic_label}, attrs={self.attributes})"
        else:
            res = f"{indent}NODE({self.tag}, semantic={self.semantic_label})"

        for child in self.children:
            res += f"\n{child._build_str(level + 1, verbose)}"
        return res


class SVGTreeSemantic(SVGTreeRaw):
    """
    Structural encapsulation holding contextual evaluated nodes naturally
    mapping semantic spaces.
    """

    def __init__(self, root: SVGTreeNodeSemantic):
        """Bootstraps the hierarchical semantic container pointing initially
        towards the primary assigned logical origin."""
        super().__init__(None, root)


def assign_semantic_to_node(
    node: SVGTreeNodeBounded,
    parent_semantic_context: str = "unknown",
) -> SVGTreeNodeSemantic:
    """
    Crawls attribute footprints parsing semantic properties mapping labels
    sequentially down.
    NOTE: Relies massively on cascades! If `<text>` lacks identifiers,
    traversing inwards structurally from an 'axis' inherently guarantees tagging
    precisely as an 'axis-text'.
    """
    label = "unknown"
    node_id = node.attributes.get("id", "")
    data_name = node.attributes.get("data-name", "")
    aria_label = node.attributes.get("aria-label", "")
    css_class = node.attributes.get("class", "")
    tag = node.tag

    # Base identifier combinations (extended to include aria labels and classes for broader compatibility)
    identifier = f"{node_id} {data_name} {aria_label} {css_class}".lower()

    current_context = parent_semantic_context

    if "axis" in identifier:
        if "label" in identifier:
            label = "axis-label"
            current_context = "axis-label"
        elif "title" in identifier:
            label = "axis-title"
            current_context = "axis-title"
        elif "tick" in identifier:
            label = "axis-tick"
            current_context = "axis-tick"
        else:
            label = "axis"
            current_context = "axis"

    elif "legend" in identifier or "swatch" in identifier:
        if "title" in identifier:
            label = "legend-title"
            current_context = "legend-title"
        elif "item" in identifier or "swatch" in identifier:
            label = "legend-item"
            current_context = "legend-item"
        else:
            label = "legend"
            current_context = "legend"

    elif "grid" in identifier:
        label = "grid"
        current_context = "grid"

    elif "data" in identifier or "dot" in identifier or "rule" in identifier or "mark" in identifier or current_context == "data-groups":
        if "container" in identifier or "group" in identifier:
            label = "data-groups"
            current_context = "data-groups"
        elif current_context == "data-groups" and tag == "g":
            # Individual data group
            label = "data-group"
            current_context = "data-group"
        else:
            label = "data-element"
            current_context = "data-group"

    else:
        # Contextual inheritance
        if parent_semantic_context != "unknown":
            if tag == "text":
                label = f"{parent_semantic_context}-text"
            elif tag in [
                "rect",
                "circle",
                "ellipse",
                "polygon",
                "polyline",
                "path",
                "line",
            ]:
                label = f"{parent_semantic_context}-shape"
            else:
                label = f"{parent_semantic_context}-group"
                current_context = label
        else:
            if tag == "text":
                label = "text"
            elif tag in [
                "rect",
                "circle",
                "ellipse",
                "polygon",
                "polyline",
                "path",
                "line",
            ]:
                label = "shape"
            elif tag == "g":
                label = "group"
            elif tag == "svg":
                label = "svg-root"
                current_context = "svg-root"

    # Important: Recreate the node with the original raw properties and the
    # newly computed bounding box
    semantic_node = SVGTreeNodeSemantic(
        node=node,
        bounding=node.bounding,
        semantic_label=label,
    )

    # Process children recursively
    for child in node.children:
        child_semantic = assign_semantic_to_node(
            child,  # Need to make sure it's SVGTreeNodeBounded
            parent_semantic_context=current_context,
        )
        child_semantic.parent = semantic_node
        semantic_node.children.append(child_semantic)

    return semantic_node


def assign_semantic_to_tree(svg_tree: SVGTreeBounded) -> SVGTreeSemantic:
    """
    Automates generating logical evaluation converting structural Bounded
    hierarchies smoothly interpreting chart structures completely.
    """
    semantic_root = assign_semantic_to_node(svg_tree.root)
    return SVGTreeSemantic(semantic_root)
