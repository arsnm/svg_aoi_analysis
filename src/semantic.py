# semantic.py
#
# Module for assigning semantic labels to nodes in the bounded SVG tree.
# Uses multi-signal detection: six independent signals each produce a
# confidence score, scores are summed, and the highest label wins.

import colorsys
from typing import Dict, List, Optional


LABELS = [
    "data-mark",
    "data-node",
    "data-link",
    "data-label",
    "data-group",
    "data-container",
    "axis",
    "axis-tick",
    "axis-label",
    "axis-title",
    "grid",
    "legend",
    "legend-title",
    "legend-item",
    "legend-item-symbol",
    "legend-item-label",
    "unknown"
]


# Signal 1: aria-label
# Observable Plot SVGs annotate every mark group with an aria-label attribute.
# This is the primary signal for Observable Plot SVGs.
# Confidence: 0.95 exact, 0.70 partial.

ARIA_LABEL_MAP = {
    "dot":               "data-mark",
    "rule":              "data-mark",
    "line":              "data-mark",
    "bar":               "data-mark",
    "cell":              "data-mark",
    "area":              "data-mark",
    "tick":              "data-mark",
    "x-axis":            "axis",
    "y-axis":            "axis",
    "x-axis tick":       "axis-tick",
    "y-axis tick":       "axis-tick",
    "x-axis tick label": "axis-label",
    "y-axis tick label": "axis-label",
    "x-axis label":      "axis-title",
    "y-axis label":      "axis-title",
    "x-grid":            "grid",
    "y-grid":            "grid",
    "legend":            "legend",
    "color legend":      "legend",
}

def signal_aria_label(node) -> Dict[str, float]:
    """Returns confidence scores based on the node's aria-label attribute."""
    aria = node.attributes.get("aria-label", "").strip().lower()
    if not aria:
        return {}

    scores = {}
    if aria in ARIA_LABEL_MAP:
        scores[ARIA_LABEL_MAP[aria]] = 0.95
        return scores

    for key, label in ARIA_LABEL_MAP.items():
        if key in aria or aria in key:
            scores[label] = max(scores.get(label, 0), 0.7)

    return scores


# Signal 2: ID / class / data-name keywords
# Hand-crafted SVGs use meaningful element ids and classes.
# This is the primary signal for hand-crafted SVGs.
# Confidence: 0.90 for any keyword match.

ID_KEYWORD_MAP = {
    "reference-axis":    "axis",
    "axisline":          "axis",
    "axisticks":         "axis-tick",
    "axis-tick":         "axis-tick",
    "axis-label":        "axis-label",
    "axis-title":        "axis-title",
    "tick-":             "axis-tick",
    "reference-grid":    "grid",
    "main-grid":         "grid",
    "grid":              "grid",
    "data-groups":       "data-container",
    "data-group":        "data-group",
    "data-points":       "data-group",
    "data-element":      "data-mark",
    "data-area":         "data-mark",
    "sub-regions":       "data-mark",
    "region-":           "data-mark",
    "area-":             "data-mark",
    "cell-":             "data-mark",
    "dot":               "data-mark",
    "rule":              "data-mark",
    "line-":             "data-link",
    "link-":             "data-link",
    "links":             "data-link",
    "node-":             "data-node",
    "nodes":             "data-node",
    "circle-":           "data-node",
    "all-stars":         "data-node",
    "label-text":        "data-label",
    "label-container":   "data-label",
    "area-label":        "data-label",
    "node-label":        "data-label",
    "legend-container":  "legend",
    "legend-color":      "legend",
    "legend-shape":      "legend",
    "legend-title":      "legend-title",
    "legend-item":       "legend-item",
    "legend-color-item": "legend-item",
    "legend-shape-item": "legend-item",
    "swatch":            "legend-item",
    "colorbins":         "legend",
}

def signal_id_keyword(node) -> Dict[str, float]:
    """Returns confidence scores based on id, class, and data-name keywords."""
    node_id   = node.attributes.get("id", "").lower()
    css_class = node.attributes.get("class", "").lower()
    data_name = node.attributes.get("data-name", "").lower()
    identifier = f"{node_id} {css_class} {data_name}".strip()

    if not identifier:
        return {}

    scores = {}
    for keyword, label in ID_KEYWORD_MAP.items():
        if keyword in identifier:
            scores[label] = max(scores.get(label, 0), 0.9)

    return scores


# Signal 3: structural position
# Elements near the left/bottom edge are likely axes. Near the right edge,
# likely legend. In the center, likely data.
# Confidence: 0.40 axis, 0.30 legend, 0.30 data-mark.

def signal_position(node, svg_bbox) -> Dict[str, float]:
    """Returns confidence scores based on the node's position on the canvas."""
    bbox = _get_bbox(node)
    if not bbox or not svg_bbox:
        return {}

    x1, y1, x2, y2 = bbox
    sx1, sy1, sx2, sy2 = svg_bbox
    svg_w = sx2 - sx1
    svg_h = sy2 - sy1

    if svg_w == 0 or svg_h == 0:
        return {}

    cx = ((x1 + x2) / 2 - sx1) / svg_w
    cy = ((y1 + y2) / 2 - sy1) / svg_h

    scores = {}
    near_left   = cx < 0.15
    near_right  = cx > 0.85
    near_bottom = cy > 0.85

    if near_left or near_bottom:
        scores["axis"] = 0.4
    if near_right:
        scores["legend"] = 0.3
    if not (near_left or near_right or near_bottom):
        scores["data-mark"] = 0.3

    return scores


# Signal 4: tag + repetition
# Data marks almost always repeat — many siblings of the same tag and
# similar size strongly suggests a data mark.
# Confidence: 0.60 when 3+ same-size siblings are found.

def signal_repetition(node, siblings: List) -> Dict[str, float]:
    """Returns confidence scores based on repeated siblings of same tag and size."""
    if not siblings or len(siblings) < 3:
        return {}

    same_tag = [s for s in siblings if s.tag == node.tag]
    if len(same_tag) < 3:
        return {}

    bbox = _get_bbox(node)
    if not bbox:
        return {}

    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    similar_size = [
        s for s in same_tag
        if _get_bbox(s) and
        abs((_get_bbox(s)[2] - _get_bbox(s)[0]) - w) < 5 and
        abs((_get_bbox(s)[3] - _get_bbox(s)[1]) - h) < 5
    ]

    scores = {}
    if len(similar_size) >= 3 and node.tag in ("circle", "rect", "path", "line"):
        scores["data-mark"] = 0.6

    return scores


# Signal 5: context inheritance
# A node's parent label provides useful context when its own attributes
# are not informative enough.
# Confidence: 0.50 - 0.70 depending on the parent-child combination.

def signal_context(node, parent_label: Optional[str]) -> Dict[str, float]:
    """Returns confidence scores based on the parent node's semantic label."""
    if not parent_label or parent_label == "unknown":
        return {}

    tag = node.tag
    scores = {}

    if parent_label == "legend":
        if tag == "text":
            scores["legend-title"] = 0.5
        elif tag == "g":
            scores["legend-item"] = 0.5
        else:
            scores["legend-item-symbol"] = 0.4

    elif parent_label == "legend-item":
        if tag == "text":
            scores["legend-item-label"] = 0.7
        elif tag in ("rect", "circle", "path", "line"):
            scores["legend-item-symbol"] = 0.7
        else:
            scores["legend-item"] = 0.4

    elif parent_label in ("axis", "axis-tick"):
        if tag == "text":
            scores["axis-label"] = 0.6
        elif tag in ("line", "path"):
            scores["axis-tick"] = 0.6

    elif parent_label == "data-group":
        if tag == "text":
            scores["data-label"] = 0.6
        elif tag == "circle":
            scores["data-node"] = 0.5
        elif tag in ("line", "path"):
            scores["data-link"] = 0.5
        else:
            scores["data-mark"] = 0.5

    elif parent_label == "data-container":
        scores["data-group"] = 0.5

    return scores


# Signal 6: fill / stroke color
# Neutral greys (low HSL saturation) suggest structural elements.
# Saturated colors suggest data marks, unless inside a legend context
# where they suggest legend-item-symbol instead.
# Confidence: 0.50 saturated fill, 0.40 saturated stroke,
#             0.35 neutral stroke, 0.30 neutral fill.

def _is_neutral_color(color: str) -> bool:
    """
    Returns True if the color is neutral/structural.
    Uses HSL saturation for hex colors (below 15% = grey).
    Named keywords and grey words are always neutral.
    """
    if not color:
        return False
    color = color.strip().lower()

    if color in ("none", "currentcolor", "inherit", "transparent"):
        return True

    if color in ("black", "white", "gray", "grey", "silver",
                 "darkgray", "darkgrey", "lightgray", "lightgrey"):
        return True

    if len(color) == 4 and color.startswith("#"):
        color = "#" + color[1]*2 + color[2]*2 + color[3]*2

    if len(color) == 7 and color.startswith("#"):
        try:
            r = int(color[1:3], 16) / 255
            g = int(color[3:5], 16) / 255
            b = int(color[5:7], 16) / 255
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            return s < 0.15
        except ValueError:
            return False

    return False

def _is_saturated_color(color: str) -> bool:
    """Returns True if the color is saturated (not neutral, not empty)."""
    if not color:
        return False
    color = color.strip().lower()
    if color in ("", "none", "inherit", "transparent", "currentcolor"):
        return False
    return not _is_neutral_color(color)

def signal_color(node, parent_label: Optional[str] = None) -> Dict[str, float]:
    """
    Returns confidence scores based on fill and stroke color.
    Saturated colors inside a legend context score for legend-item-symbol
    instead of data-mark to avoid misclassifying swatches.
    """
    fill   = node.attributes.get("fill",   "").strip().lower()
    stroke = node.attributes.get("stroke", "").strip().lower()

    node_id   = node.attributes.get("id",    "").lower()
    css_class = node.attributes.get("class", "").lower()
    in_legend = (
        (parent_label and "legend" in parent_label) or
        any(kw in f"{node_id} {css_class}" for kw in ("swatch", "legend"))
    )

    scores = {}

    if _is_neutral_color(fill):
        scores["axis"] = max(scores.get("axis", 0), 0.3)
        scores["grid"] = max(scores.get("grid", 0), 0.3)
    elif _is_saturated_color(fill):
        if in_legend:
            scores["legend-item-symbol"] = max(scores.get("legend-item-symbol", 0), 0.5)
        else:
            scores["data-mark"] = max(scores.get("data-mark", 0), 0.5)

    if _is_neutral_color(stroke):
        scores["axis"] = max(scores.get("axis", 0), 0.35)
        scores["grid"] = max(scores.get("grid", 0), 0.35)
    elif _is_saturated_color(stroke):
        if in_legend:
            scores["legend-item-symbol"] = max(scores.get("legend-item-symbol", 0), 0.4)
        else:
            scores["data-mark"] = max(scores.get("data-mark", 0), 0.4)

    return scores


def combine_signals(*signal_dicts) -> Dict[str, float]:
    """Merges confidence score dicts from all signals by summing their values."""
    combined = {}
    for d in signal_dicts:
        for label, score in d.items():
            combined[label] = combined.get(label, 0) + score
    return combined


def pick_label(scores: Dict[str, float], threshold: float = 0.3) -> str:
    """Returns the label with the highest score, or 'unknown' if below threshold."""
    if not scores:
        return "unknown"
    best = max(scores, key=scores.get)
    return best if scores[best] >= threshold else "unknown"


def assign_semantic_to_node(
    node,
    parent_label: Optional[str] = None,
    siblings: Optional[List] = None,
    svg_bbox: Optional[List[float]] = None
) -> str:
    """
    Assigns a semantic label to a single SVG tree node by running all six
    signals, combining their scores, and returning the highest label.
    """
    if node.tag == "foreignObject":
        return "legend"

    s1 = signal_aria_label(node)
    s2 = signal_id_keyword(node)
    s3 = signal_position(node, svg_bbox)
    s4 = signal_repetition(node, siblings or [])
    s5 = signal_context(node, parent_label)
    s6 = signal_color(node, parent_label=parent_label)

    combined = combine_signals(s1, s2, s3, s4, s5, s6)
    return pick_label(combined)


def _get_bbox(node):
    """
    Extracts a [x1, y1, x2, y2] list from a node.
    Handles both SVGTreeNodeBounded (.bounding) and SVGTreeNodeSemantic (.bbox).
    """
    bbox = getattr(node, "bbox", None)
    if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
        return list(bbox)
    bounding = getattr(node, "bounding", None)
    if bounding is not None:
        try:
            bounds = list(bounding.bounds)
            if len(bounds) == 4:
                return bounds
        except (AttributeError, TypeError):
            pass
    return None


class SVGTreeNodeSemantic:
    """
    Wraps a SVGTreeNodeBounded node and adds a semantic_label field.
    Exposes the same interface expected by pipeline._extract_data.
    """

    def __init__(self, bounded_node):
        self._node          = bounded_node
        self.semantic_label = "unknown"
        self.children       = []

    @property
    def tag(self):
        return self._node.tag

    @property
    def attributes(self):
        return self._node.attributes

    @property
    def text(self):
        return self._node.text

    @property
    def bounding(self):
        return self._node.bounding

    @property
    def bbox(self):
        if self._node.bounding is None:
            return None
        return list(self._node.bounding.bounds)


class SVGTreeSemantic:
    """Container holding the root of the semantically labelled SVG tree."""

    def __init__(self, root: SVGTreeNodeSemantic):
        self.root = root


def assign_semantic_to_tree(bounded_tree) -> SVGTreeSemantic:
    """
    Traverses the bounded tree top-down and assigns a semantic label to
    every node, passing parent label, siblings, and svg bbox as context.
    """
    svg_bbox = _get_bbox(bounded_tree.root)

    def wrap_node(bounded_node, parent_label=None):
        semantic_node = SVGTreeNodeSemantic(bounded_node)

        parent   = getattr(bounded_node, "parent", None)
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