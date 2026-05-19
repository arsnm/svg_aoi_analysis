# geometry.py
#
# Module for geometric computations related to AOI extraction and analysis. This
# module provides functions for calculating areas, optimized bounding polygons,
# and other geometric properties of AOIs.

import re
from .parser import SVGTreeRaw, SVGTreeNodeRaw
from shapely.geometry import Polygon, MultiPolygon, Point, LineString
from shapely.affinity import scale, translate, rotate
from shapely.ops import unary_union
from svg.path import parse_path


def _parse_float(value: str | None) -> float | None:
    """
    Parses a float from a string.
    NOTE: Aggressively filters non-numeric characters (like 'px' or 'em') to
    gracefully handle typical SVG unit idiosyncrasies.
    """
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        filtered = "".join(ch for ch in value if (ch.isdigit() or ch in ".-"))
        return float(filtered) if filtered else None


def _parse_points(points: str | None) -> list[tuple[float, float]]:
    """
    Parses a string of flat coordinate values (e.g., "x1 y1 x2 y2") into a list
    of (x, y) tuples.
    """
    if not points:
        return []
    coords = []
    for token in points.replace(",", " ").split():
        value = _parse_float(token)
        if value is not None:
            coords.append(value)
    return list(zip(coords[0::2], coords[1::2]))


def _bbox_polygon(
    min_x: float, min_y: float, max_x: float, max_y: float
) -> Polygon:
    """
    Generates a rectangular Shapely Polygon safely from bounding box minimal and
    maximal coordinates.
    """
    return Polygon(
        [
            (min_x, min_y),
            (max_x, min_y),
            (max_x, max_y),
            (min_x, max_y),
        ]
    )


def _close_points(
    points: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    """
    Ensures a list of points forms a closed loop by verifying the first and last
    points match. Required for valid Polygon creation in Shapely.
    """
    if not points:
        return []
    if points[0] != points[-1]:
        return points + [points[0]]
    return points


def _polygon_from_polyline(
    points: list[tuple[float, float]], line_epsilon: float
) -> Polygon | None:
    """
    Converts a sequence of points into a Polygon.
    NOTE: If it represents exactly a 2-point line, inflates (buffers) it by
    `line_epsilon` to yield a valid 2D shape, since pure lines inherently hold
    zero area.
    """
    if len(points) >= 3:
        return Polygon(_close_points(points))
    if len(points) == 2:
        line = LineString(points)
        if line_epsilon <= 0.0:
            line_epsilon = 1e-6
        buffered = line.buffer(line_epsilon, cap_style=2, join_style=2)
        return (
            buffered if isinstance(buffered, Polygon) else buffered.convex_hull
        )
    return None


def _curve_polygon(
    center_x: float, center_y: float, radius: float, resolution: int
) -> Polygon:
    """
    Creates a circular Polygon around a center point using Shapely's spatial
    buffering mapped against a curve resolution.
    """
    return Point(center_x, center_y).buffer(radius, resolution=resolution)


def _ellipse_polygon(
    center_x: float,
    center_y: float,
    radius_x: float,
    radius_y: float,
    resolution: int,
) -> Polygon:
    """
    Creates an elliptical Polygon natively by non-uniformly scaling a circular
    base polygon constraint.
    """
    base = _curve_polygon(center_x, center_y, 1.0, resolution)
    return scale(
        base, xfact=radius_x, yfact=radius_y, origin=(center_x, center_y)
    )


def _path_to_polygon(
    d: str, resolution: int, line_epsilon: float
) -> Polygon | None:
    """
    Parses an SVG path 'd' string structural mapping into a standard Polygon.
    NOTE: Systematically flattens complex segments (like bezier curves) into
    straight approximations strictly bounded by the `resolution` factor.
    """
    path = parse_path(d)
    if not path:
        return None

    points: list[tuple[float, float]] = []
    for segment in path:
        if segment.length() == 0:
            continue
        if segment.__class__.__name__ == "Line":
            start = segment.start
            end = segment.end
            if not points:
                points.append((start.real, start.imag))
            points.append((end.real, end.imag))
        else:
            steps = max(8, resolution * 4)
            for i in range(steps + 1):
                t = i / steps
                p = segment.point(t)
                points.append((p.real, p.imag))

    if not points:
        return None
    return _polygon_from_polyline(points, line_epsilon)


def _apply_svg_transform(
    geom: Polygon | None, transform_str: str | None
) -> Polygon | None:
    """
    Parses and geometrically overlays standard SVG spatial transformations
    ('translate', 'rotate', 'scale') directly to a targeted Polygon.
    NOTE: Standard vector logic applies transform strings iteratively in
    reversed sequence (right-to-left cascade) mapped naturally into Shapely.
    """
    if not geom or not transform_str:
        return geom
    matches = list(re.finditer(r"([a-zA-Z]+)\s*\(([^)]+)\)", transform_str))
    for match in reversed(matches):
        cmd = match.group(1)
        args_str = match.group(2).replace(",", " ").split()
        args = []
        for a in args_str:
            v = _parse_float(a)
            if v is not None:
                args.append(v)

        if cmd == "translate" and len(args) >= 1:
            tx = args[0]
            ty = args[1] if len(args) > 1 else 0.0
            geom = translate(geom, xoff=tx, yoff=ty)
        elif cmd == "rotate" and len(args) >= 1:
            angle = args[0]
            cx, cy = 0.0, 0.0
            if len(args) == 3:
                cx, cy = args[1], args[2]
            geom = rotate(geom, -angle, origin=(cx, cy), use_radians=False)
        elif cmd == "scale" and len(args) >= 1:
            sx = args[0]
            sy = args[1] if len(args) > 1 else sx
            geom = scale(geom, xfact=sx, yfact=sy, origin=(0, 0))
    return geom


def _raw_bounding_from_attributes(
    node: SVGTreeNodeRaw, curve_resolution: int, line_epsilon: float
) -> Polygon | None:
    """
    Calculates the fundamental structural bounding polygon securely from a
    node's physical dimensions (implicitly sidestepping transformations).
    NOTE: Given SVG text widths demand actual active graphic pipelines to
    measure correctly, `<text>` geometries are loosely approximated scaling
    `font-size` with basic sequence length heuristics.
    """
    attrs = node.attributes
    tag = node.tag

    if tag == "rect":
        x = _parse_float(attrs.get("x")) or 0.0
        y = _parse_float(attrs.get("y")) or 0.0
        width = _parse_float(attrs.get("width"))
        height = _parse_float(attrs.get("height"))
        if width is None or height is None:
            return None
        return Polygon(
            _close_points(
                [
                    (x, y),
                    (x + width, y),
                    (x + width, y + height),
                    (x, y + height),
                ]
            )
        )

    if tag == "circle":
        cx = _parse_float(attrs.get("cx"))
        cy = _parse_float(attrs.get("cy"))
        r = _parse_float(attrs.get("r"))
        if cx is None or cy is None or r is None:
            return None
        return _curve_polygon(cx, cy, r, curve_resolution)

    if tag == "ellipse":
        cx = _parse_float(attrs.get("cx"))
        cy = _parse_float(attrs.get("cy"))
        rx = _parse_float(attrs.get("rx"))
        ry = _parse_float(attrs.get("ry"))
        if cx is None or cy is None or rx is None or ry is None:
            return None
        return _ellipse_polygon(cx, cy, rx, ry, curve_resolution)

    if tag == "line":
        x1 = _parse_float(attrs.get("x1"))
        y1 = _parse_float(attrs.get("y1"))
        x2 = _parse_float(attrs.get("x2"))
        y2 = _parse_float(attrs.get("y2"))
        if None in {x1, y1, x2, y2}:
            return None
        return _polygon_from_polyline([(x1, y1), (x2, y2)], line_epsilon)

    if tag == "polyline":
        points = _parse_points(attrs.get("points"))
        if not points:
            return None
        return _polygon_from_polyline(points, line_epsilon)

    if tag == "polygon":
        points = _parse_points(attrs.get("points"))
        if not points:
            return None
        return Polygon(_close_points(points))

    if tag == "path":
        d = attrs.get("d")
        if not d:
            return None
        return _path_to_polygon(d, curve_resolution, line_epsilon)

    if tag == "text":
        x = _parse_float(attrs.get("x")) or 0.0
        y = _parse_float(attrs.get("y")) or 0.0
        font_size = _parse_float(attrs.get("font-size")) or 12.0
        text_str = getattr(node, "text", "") or ""
        length = len(text_str) if text_str else 6
        width = font_size * 0.6 * length
        height = font_size
        return _bbox_polygon(x, y - height * 0.8, x + width, y + height * 0.2)

    if tag == "svg":
        view_box = attrs.get("viewBox")
        if view_box:
            parts = [p for p in view_box.replace(",", " ").split() if p]
            if len(parts) == 4:
                min_x, min_y, width, height = (float(p) for p in parts)
                return _bbox_polygon(
                    min_x, min_y, min_x + width, min_y + height
                )
        width = _parse_float(attrs.get("width"))
        height = _parse_float(attrs.get("height"))
        if width is None or height is None:
            return None
        return _bbox_polygon(0.0, 0.0, width, height)

    return None


def _bounding_from_attributes(
    node: SVGTreeNodeRaw, curve_resolution: int, line_epsilon: float
) -> Polygon | None:
    """
    Processes raw visual boundings dynamically scaled logically over SVG
    transformation properties ('transform' attribute).
    """
    poly = _raw_bounding_from_attributes(node, curve_resolution, line_epsilon)
    return _apply_svg_transform(poly, node.attributes.get("transform"))


class SVGTreeNodeBounded(SVGTreeNodeRaw):
    """
    A structural tree node expanding SVGTreeNodeRaw explicitly tracking
    geometric extents mapping.
    """

    def __init__(
        self,
        node: SVGTreeNodeRaw,
        bounding: Polygon | None = None,
        parent: "SVGTreeNodeBounded | None" = None,
        children: list["SVGTreeNodeBounded"] | None = None,
    ):
        """
        Initializes the node securely tracking basic element properties and
        preserving textual contexts.
        """
        super().__init__(
            tag=node.tag,
            parent=parent,
            attributes=node.attributes,
            children=children if children is not None else [],
            text=getattr(node, "text", None),
        )
        self.bounding = bounding


class SVGTreeBounded(SVGTreeRaw):
    """
    Tree structure enveloping spatially bounded analytical elements mapped
    exactly structurally.
    """

    def __init__(self, root: SVGTreeNodeBounded):
        """Initializes the bounded tree instance encapsulating the newly
        physically bound root node element."""
        super().__init__(None, root)


def assign_bounding_to_node(
    node: SVGTreeNodeRaw,
    curve_resolution: int = 16,
    line_epsilon: float = 0.0,
) -> SVGTreeNodeBounded:
    """
    Recursively evaluates dimensional boundaries outwards onto parents
    iteratively natively.  NOTE: A nested '<g>' logical group inherits its
    precise spatial mapping entirely from the mathematical merger (union or
    envelope convex_hull) of strictly all internal graphic children collectively
    overlaying.
    """
    bounded_node = SVGTreeNodeBounded(node)

    child_polygons: list[Polygon] = []
    for child in node.children:
        child_bounded = assign_bounding_to_node(
            child, curve_resolution=curve_resolution, line_epsilon=line_epsilon
        )
        child_bounded.parent = bounded_node
        bounded_node.children.append(child_bounded)
        if child_bounded.bounding is not None:
            child_polygons.append(child_bounded.bounding)

    if child_polygons:
        merged = unary_union(child_polygons)
        if isinstance(merged, Polygon):
            bounded_node.bounding = merged
        elif isinstance(merged, MultiPolygon):
            bounded_node.bounding = merged.convex_hull
        else:
            bounded_node.bounding = merged.convex_hull
        return bounded_node

    bounded_node.bounding = _bounding_from_attributes(
        node, curve_resolution=curve_resolution, line_epsilon=line_epsilon
    )
    return bounded_node


def assign_bounding_to_tree(
    svg_tree: SVGTreeRaw,
    curve_resolution: int = 16,
    line_epsilon: float = 0.0,
) -> SVGTreeBounded:
    """
    Executes structural polygon evaluation across precisely the raw hierarchy
    converting it logically to BoundedTree configuration.
    """
    bounded_root = assign_bounding_to_node(
        svg_tree.root,
        curve_resolution=curve_resolution,
        line_epsilon=line_epsilon,
    )
    return SVGTreeBounded(bounded_root)
