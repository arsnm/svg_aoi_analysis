# semantic.py
#
# Semantic labeling for SVG AOI extraction.
#
# Strategy (priority order, first match wins):
#   1. Tag special cases  (svg, foreignObject always have known labels)
#   2. Attribute scan     (check ALL attributes for semantic values)
#   3. Parent inheritance (child takes parent label with specific rules)
#   4. Sibling context    (many same-tag same-size siblings = data-mark)
#   5. Conservative tag   (last resort: tag + position, very restricted)
#
# No confidence scores, no threshold tuning, no signal combining.
# Each step only runs if the previous step produced nothing.

import colorsys
from typing import Optional, List, Dict


LABELS = [
    "data-mark", "data-node", "data-link", "data-label",
    "data-group", "data-container",
    "axis", "axis-tick", "axis-label", "axis-title",
    "grid",
    "legend", "legend-title", "legend-item",
    "legend-item-symbol", "legend-item-label",
    "unknown"
]

# Keyword map
# Maps any substring found in any attribute value to a label.
# Keys are lowercase substrings. Longer/more specific keys take priority.
# This map is checked against the VALUE of every non-geometric attribute,
# regardless of what the attribute is called.

KEYWORD_MAP = {
    # Axis
    "x-axis tick label": "axis-label",
    "y-axis tick label": "axis-label",
    "x-axis tick":       "axis-tick",
    "y-axis tick":       "axis-tick",
    "x-axis label":      "axis-title",
    "y-axis label":      "axis-title",
    "axis-title":        "axis-title",
    "axis-label":        "axis-label",
    "axis-tick":         "axis-tick",
    "axistick":          "axis-tick",
    "axisline":          "axis",
    "x-axis":            "axis",
    "y-axis":            "axis",
    "reference-axis":    "axis",
    "axis":              "axis",
    "data-container":    "data-container",
    "colorbins-container": "legend",
    "xaxis":             "axis",
    "yaxis":             "axis",

    # Grid
    "x-grid":            "grid",
    "y-grid":            "grid",
    "reference-grid":    "grid",
    "main-grid":         "grid",
    "grid":              "grid",

    # Legend
    "color legend":           "legend",
    "legend-container":       "legend",
    "legend-color":           "legend",
    "legend-shape":           "legend",
    "colorbins-legend":       "legend",
    "color-legend-container": "legend",
    "legend-title":           "legend-title",
    "legend-color-item":      "legend-item",
    "legend-shape-item":      "legend-item",
    "legend-item":            "legend-item",
    "swatch":                 "legend-item",
    "colorbin":               "legend-item-symbol",
    "legend":                 "legend",

    # Data marks
    "data-area-container":  "data-mark",
    "sub-regions":          "data-mark",
    "all-stars":            "data-node",
    "data-element":         "data-mark",
    "data-points":          "data-group",
    "data-groups":          "data-container",
    "data-group":           "data-group",
    "data-area":            "data-mark",
    "region-":              "data-mark",
    "area-":                "data-mark",
    "cell-":                "data-mark",
    "dot":                  "data-mark",
    "rule":                 "data-mark",
    "bar":                  "data-mark",
    "cell":                 "data-mark",
    "tick":                 "data-mark",

    # Links / nodes
    "line-":                "data-link",
    "link-":                "data-link",
    "links":                "data-link",
    "node-":                "data-node",
    "nodes":                "data-node",
    "circle-":              "data-node",

    # Labels
    "label-background":     "data-label",
    "label-container":      "data-label",
    "label-text":           "data-label",
    "label-bg":             "data-label",
    "star-label":           "data-label",
    "area-label":           "data-label",
    "node-label":           "data-label",
    "node-labels":          "data-label",
}

# Geometric / style attributes we never check for semantic meaning
_SKIP_ATTRS = {
    'x', 'y', 'x1', 'y1', 'x2', 'y2', 'cx', 'cy', 'r', 'rx', 'ry',
    'width', 'height', 'd', 'transform', 'points', 'viewBox', 'viewbox',
    'fill', 'stroke', 'stroke-width', 'stroke-dasharray', 'stroke-linecap',
    'stroke-linejoin', 'stroke-opacity', 'fill-opacity', 'opacity',
    'font-size', 'font-family', 'font-weight', 'font-variant', 'font-style',
    'text-anchor', 'dominant-baseline', 'alignment-baseline',
    'clip-path', 'clip-rule', 'mask', 'filter', 'style',
    'xmlns', 'xmlns:xlink', 'xlink:href', 'href', 'preserveAspectRatio',
    'isolation', 'tabindex', 'focusable', 'aria-hidden',
}


def _match_keyword(value: str) -> Optional[str]:
    """
    Check a single string against KEYWORD_MAP.
    Tries exact match first, then substring match (longer keys first).
    Returns a label or None.
    """
    v = value.strip().lower()
    if not v or len(v) > 120:
        return None

    # Exact match
    if v in KEYWORD_MAP:
        return KEYWORD_MAP[v]

    # Substring match: longer keys checked first (more specific wins)
    for key in sorted(KEYWORD_MAP, key=len, reverse=True):
        if key in v:
            return KEYWORD_MAP[key]

    return None


def step1_tag_special(node) -> Optional[str]:
    """
    Step 1: Certain tags always have a known label regardless of attributes.
    """
    tag = node.tag
    if tag == 'svg':
        return 'data-container'
    if tag == 'foreignObject':
        return 'legend'
    return None


def step2_attribute_scan(node) -> Optional[str]:
    """
    Step 2: Scan ALL attributes for semantic values.
    Checks the value of every non-geometric attribute against KEYWORD_MAP.
    Attribute name does not matter only the value.
    Priority: aria-label > id > data-name > class > everything else.
    """
    attrs = node.attributes

    # Check high-priority attributes first
    priority_attrs = ['aria-label', 'id', 'data-name', 'class',
                      'data-type', 'data-role', 'role', 'title',
                      'data-category', 'data-mark', 'data-chart-element']

    for attr in priority_attrs:
        val = attrs.get(attr, '')
        if val:
            label = _match_keyword(val)
            if label:
                return label

    # Then scan all remaining attributes
    for attr, val in attrs.items():
        if attr in priority_attrs:
            continue
        if attr in _SKIP_ATTRS:
            continue
        if not val or not isinstance(val, str):
            continue
        label = _match_keyword(val)
        if label:
            return label

    return None


def step3_parent_inheritance(node, parent_label: Optional[str]) -> Optional[str]:
    """
    Step 3: Inherit label from parent using specific rules.
    Only fires when parent label is known and specific child patterns apply.
    """
    if parent_label is None:
        return None

    tag = node.tag

    # Axis family: differentiate by child tag
    if parent_label == 'axis-title':
        if tag == 'text':
            return 'axis-title'
        return None
    if parent_label in ('axis', 'axis-tick', 'axis-label', 'axis-title'):
        if tag == 'text':
            return 'axis-label'
        if tag in ('line', 'path'):
            return 'axis-tick'
        if tag == 'g':
            return 'axis'
        return None 

    # Grid family
    if parent_label == 'grid':
        if tag in ('line', 'path', 'rect'):
            return 'grid'
        return None

    # Legend family
    if parent_label == 'legend':
        if tag == 'text':
            return 'legend-title'
        if tag in ('g', 'rect', 'circle', 'path', 'line'):
            return 'legend-item'
        return None

    if parent_label == 'legend-title':
        if tag == 'text':
            return 'legend-title'
        return None

    if parent_label == 'legend-item':
        if tag in ('rect', 'circle', 'path', 'line', 'polygon', 'svg'):
            return 'legend-item-symbol'
        if tag == 'text':
            return 'legend-item-label'
        if tag == 'g':
            return 'legend-item'
        return None

    if parent_label == 'legend-item-label':
        if tag == 'text':
            return 'legend-item-label'
        return None

    if parent_label == 'legend-item-symbol':
        if tag in ('rect', 'circle', 'path', 'polygon'):
            return 'legend-item-symbol'
        return None

    # Data label family
    if parent_label == 'data-label':
        if tag == 'text':
            return 'data-label'
        if tag == 'rect':
            return 'data-label'  # background rect of a label
        return None

    # Data container / group : children are marks
    if parent_label in ('data-container', 'data-group'):
        if tag in ('path', 'circle', 'rect', 'line', 'polygon',
                   'polyline', 'ellipse'):
            return 'data-mark'
        return None

    # Data mark group : children are also marks
    if parent_label == 'data-mark':
        if tag in ('path', 'circle', 'rect', 'line', 'polygon',
                   'polyline', 'ellipse'):
            return 'data-mark'
        return None

    # Data node : children stay as nodes
    if parent_label == 'data-node':
        if tag in ('circle', 'rect', 'path', 'ellipse'):
            return 'data-node'
        return None

    # Data link : children stay as links
    if parent_label == 'data-link':
        if tag in ('line', 'path', 'polyline'):
            return 'data-link'
        return None

    return None


def step4_sibling_context(node, siblings: List) -> Optional[str]:
    """
    Step 4: Many siblings of same tag and similar size = data-mark.
    Only fires for shape tags, not text or g.
    Requires 4+ similar siblings to reduce false positives.
    """
    if not siblings or len(siblings) < 4:
        return None

    if node.tag not in ('circle', 'rect', 'path', 'line',
                        'polygon', 'polyline', 'ellipse'):
        return None

    same_tag = [s for s in siblings if s.tag == node.tag]
    if len(same_tag) < 4:
        return None

    bbox = _get_bbox(node)
    if not bbox:
        return None

    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    if w < 2 or h < 2:
        return None

    similar = [
        s for s in same_tag
        if _get_bbox(s) and
        abs((_get_bbox(s)[2] - _get_bbox(s)[0]) - w) < 10 and
        abs((_get_bbox(s)[3] - _get_bbox(s)[1]) - h) < 10
    ]

    if len(similar) >= 4:
        return 'data-mark'

    return None


def step5_conservative_tag(node, svg_bbox) -> Optional[str]:
    """
    Step 5: Last resort. Very conservative rules based on tag only.
    Only returns a label when we are very confident.
    """
    tag = node.tag

    # Text elements are always some kind of label
    if tag == 'text':
        return 'data-label'

    # Check if element has a saturated fill :strong signal for data mark
    fill = node.attributes.get('fill', '').strip().lower()
    if fill and fill not in ('none', 'currentcolor', 'inherit', 'transparent', 'white', '#fff', '#ffffff'):
        if _is_saturated(fill):
            return 'data-mark'

    # Check canvas coverage for containers
    bbox = _get_bbox(node)
    if bbox and svg_bbox:
        sw = svg_bbox[2] - svg_bbox[0]
        sh = svg_bbox[3] - svg_bbox[1]
        if sw > 0 and sh > 0:
            nw = bbox[2] - bbox[0]
            nh = bbox[3] - bbox[1]
            coverage = (nw * nh) / (sw * sh)
            if coverage > 0.70:
                return 'data-container'

    return None


# Color helper 

def _is_saturated(color: str) -> bool:
    """Returns True if color has meaningful saturation (not grey/white/black)."""
    color = color.strip().lower()
    if color in ('none', 'currentcolor', 'inherit', 'transparent',
                 'black', 'white', 'gray', 'grey', 'silver',
                 '#000', '#000000', '#fff', '#ffffff'):
        return False
    if len(color) == 4 and color.startswith('#'):
        color = '#' + color[1]*2 + color[2]*2 + color[3]*2
    if len(color) == 7 and color.startswith('#'):
        try:
            r = int(color[1:3], 16) / 255
            g = int(color[3:5], 16) / 255
            b = int(color[5:7], 16) / 255
            _, _, s = colorsys.rgb_to_hls(r, g, b)
            return s > 0.15
        except ValueError:
            pass
    # Named colors that are not grey are saturated
    return True


# Main assignment 

def assign_semantic_to_node(
    node,
    parent_label: Optional[str] = None,
    siblings: Optional[List] = None,
    svg_bbox: Optional[List[float]] = None
) -> str:
    """
    Assigns a semantic label to a single SVG node.
    Runs five steps in priority order, returns on first match.
    """
    # Step 1: tag special cases
    label = step1_tag_special(node)
    if label:
        return label

    # Step 2: scan all attributes for semantic values
    label = step2_attribute_scan(node)
    if label:
        return label

    # Step 3: inherit from parent
    label = step3_parent_inheritance(node, parent_label)
    if label:
        return label

    # Step 4: sibling repetition
    label = step4_sibling_context(node, siblings or [])
    if label:
        return label

    # Step 5: conservative tag-based fallback
    label = step5_conservative_tag(node, svg_bbox)
    if label:
        return label

    return 'unknown'


# Tree traversal 

def _get_bbox(node):
    bbox = getattr(node, 'bbox', None)
    if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
        return list(bbox)
    bounding = getattr(node, 'bounding', None)
    if bounding is not None:
        try:
            bounds = list(bounding.bounds)
            if len(bounds) == 4:
                return bounds
        except (AttributeError, TypeError):
            pass
    return None


class SVGTreeNodeSemantic:
    def __init__(self, bounded_node):
        self._node = bounded_node
        self.semantic_label = 'unknown'
        self.children = []

    @property
    def tag(self): return self._node.tag
    @property
    def attributes(self): return self._node.attributes
    @property
    def text(self): return self._node.text
    @property
    def bounding(self): return self._node.bounding
    @property
    def bbox(self):
        if self._node.bounding is None:
            return None
        return list(self._node.bounding.bounds)


class SVGTreeSemantic:
    def __init__(self, root: SVGTreeNodeSemantic):
        self.root = root


def assign_semantic_to_tree(bounded_tree) -> SVGTreeSemantic:
    svg_bbox = _get_bbox(bounded_tree.root)

    def wrap_node(bounded_node, parent_label=None):
        semantic_node = SVGTreeNodeSemantic(bounded_node)
        parent = getattr(bounded_node, 'parent', None)
        siblings = parent.children if parent else []

        semantic_node.semantic_label = assign_semantic_to_node(
            bounded_node,
            parent_label=parent_label,
            siblings=siblings,
            svg_bbox=svg_bbox
        )

        for child in bounded_node.children:
            semantic_node.children.append(
                wrap_node(child, parent_label=semantic_node.semantic_label)
            )

        return semantic_node

    return SVGTreeSemantic(wrap_node(bounded_tree.root))