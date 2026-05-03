# geometry.py
#
# Module for geometric computations related to AOI extraction and analysis. This
# odule provides functions for calculating areas, optimized bounding polygons,
# and other goemetric properties of AOIs.

from .parser import SVGTreeRaw, SVGTreeNodeRaw
from shapely.geometry import Polygon

class SVGTreeNodeBounded(SVGTreeNodeRaw):
    def __init__(self, node: SVGTreeNodeRaw, bounding: Polygon | None = None):
        super().__init__( tag=node.tag,
            parent=node.parent,
            attributes=node.attributes,
            children=node.children,
        )
        self.bounding = bounding


class SVGTreeBounded(SVGTreeRaw):
    def __init__(self, root: SVGTreeNodeBounded):
        super().__init__(None, root)


def assign_bounding_to_node(node: SVGTreeNodeRaw) -> SVGTreeNodeBounded:
    # TODO
    return


def assign_bounding_to_tree(svg_tree: SVGTreeRaw) -> SVGTreeBounded:
    # TODO
    return
