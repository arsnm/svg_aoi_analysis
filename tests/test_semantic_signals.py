# tests/test_semantic_signals.py
#
# Unit tests for all signal functions and the tree traversal in semantic.py.
# Run with: python -m pytest src/test_semantic_signals.py -v

import pytest
from unittest.mock import MagicMock
from src.semantic import (
    signal_aria_label, signal_id_keyword, signal_position,
    signal_repetition, signal_context, signal_color,
    combine_signals, pick_label, assign_semantic_to_node,
    assign_semantic_to_tree, SVGTreeNodeSemantic
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_node(tag="g", node_id="", css_class="", aria_label="",
              data_name="", bbox=None):
    node = MagicMock()
    node.tag = tag
    node.attributes = {
        "id": node_id, "class": css_class,
        "aria-label": aria_label, "data-name": data_name,
        "fill": "", "stroke": ""
    }
    node.bbox = bbox
    return node

def make_bounded_node(tag="g", node_id="", aria_label="",
                      bbox=None, children=None, parent=None):
    node = MagicMock()
    node.tag = tag
    node.attributes = {
        "id": node_id, "class": "",
        "aria-label": aria_label, "data-name": "",
        "fill": "", "stroke": ""
    }
    node.text = ""
    node.children = children or []
    node.parent = parent
    if bbox:
        bounding = MagicMock()
        bounding.bounds = bbox
        node.bounding = bounding
    else:
        node.bounding = None
    return node

def make_bounded_tree(root):
    tree = MagicMock()
    tree.root = root
    return tree


# ── Signal 1: aria-label ──────────────────────────────────────────────────────

def test_aria_dot():
    assert signal_aria_label(make_node(aria_label="dot")).get("data-mark", 0) >= 0.9

def test_aria_rule():
    assert signal_aria_label(make_node(aria_label="rule")).get("data-mark", 0) >= 0.9

def test_aria_y_grid():
    assert signal_aria_label(make_node(aria_label="y-grid")).get("grid", 0) >= 0.7

def test_aria_y_axis_tick():
    assert signal_aria_label(make_node(aria_label="y-axis tick")).get("axis-tick", 0) >= 0.7

def test_aria_empty():
    assert signal_aria_label(make_node(aria_label="")) == {}


# ── Signal 2: ID / class keywords ────────────────────────────────────────────

def test_id_legend_container():
    assert signal_id_keyword(make_node(node_id="legend-container")).get("legend", 0) >= 0.9

def test_id_data_groups():
    assert signal_id_keyword(make_node(node_id="data-groups")).get("data-container", 0) >= 0.9

def test_id_axis():
    assert signal_id_keyword(make_node(node_id="reference-axis-xAxis")).get("axis", 0) >= 0.9

def test_id_swatch():
    assert signal_id_keyword(make_node(css_class="plot-swatch")).get("legend-item", 0) >= 0.9

def test_id_no_match():
    assert signal_id_keyword(make_node(node_id="random-xyz")) == {}


# ── Signal 3: position ────────────────────────────────────────────────────────

def test_position_left_edge():
    node = make_node(bbox=[10, 200, 50, 400])
    assert signal_position(node, [0, 0, 1000, 800]).get("axis", 0) > 0

def test_position_center():
    node = make_node(bbox=[400, 300, 600, 500])
    assert signal_position(node, [0, 0, 1000, 800]).get("data-mark", 0) > 0

def test_position_no_bbox():
    assert signal_position(make_node(bbox=None), [0, 0, 1000, 800]) == {}


# ── Signal 4: repetition ──────────────────────────────────────────────────────

def test_repetition_many_circles():
    node = make_node(tag="circle", bbox=[100, 100, 110, 110])
    siblings = [make_node(tag="circle", bbox=[i*50, i*50, i*50+10, i*50+10]) for i in range(5)]
    assert signal_repetition(node, siblings).get("data-mark", 0) >= 0.6

def test_repetition_too_few():
    node = make_node(tag="circle", bbox=[100, 100, 110, 110])
    siblings = [make_node(tag="circle", bbox=[200, 200, 210, 210])]
    assert signal_repetition(node, siblings) == {}


# ── Signal 5: context ─────────────────────────────────────────────────────────

def test_context_legend_text():
    assert signal_context(make_node(tag="text"), "legend").get("legend-title", 0) > 0

def test_context_legend_item_rect():
    assert signal_context(make_node(tag="rect"), "legend-item").get("legend-item-symbol", 0) >= 0.7

def test_context_no_parent():
    assert signal_context(make_node(tag="text"), None) == {}


# ── Signal 6: color ───────────────────────────────────────────────────────────

def test_color_neutral_stroke_suggests_axis():
    node = make_node(tag="line")
    node.attributes["fill"] = "none"
    node.attributes["stroke"] = "#999"
    assert signal_color(node).get("axis", 0) > 0 or signal_color(node).get("grid", 0) > 0

def test_color_saturated_fill_suggests_data():
    node = make_node(tag="circle")
    node.attributes["fill"] = "green"
    node.attributes["stroke"] = ""
    assert signal_color(node).get("data-mark", 0) >= 0.5

def test_color_purple_fill_suggests_data():
    node = make_node(tag="path")
    node.attributes["fill"] = "purple"
    node.attributes["stroke"] = ""
    assert signal_color(node).get("data-mark", 0) >= 0.5

def test_color_currentcolor_not_data():
    node = make_node(tag="path")
    node.attributes["fill"] = "currentColor"
    node.attributes["stroke"] = ""
    assert signal_color(node).get("data-mark", 0) == 0

def test_color_empty_returns_nothing():
    node = make_node(tag="g")
    node.attributes["fill"] = ""
    node.attributes["stroke"] = ""
    assert signal_color(node) == {}

def test_color_saturated_in_legend_not_data():
    node = make_node(tag="rect")
    node.attributes["fill"] = "green"
    node.attributes["stroke"] = ""
    scores = signal_color(node, parent_label="legend-item")
    assert scores.get("data-mark", 0) == 0
    assert scores.get("legend-item-symbol", 0) >= 0.5

def test_color_swatch_class_not_data():
    node = make_node(tag="rect", css_class="plot-swatch")
    node.attributes["fill"] = "purple"
    node.attributes["stroke"] = ""
    scores = signal_color(node, parent_label=None)
    assert scores.get("data-mark", 0) == 0
    assert scores.get("legend-item-symbol", 0) >= 0.5

def test_color_dark_grey_hex_is_neutral():
    node = make_node(tag="line")
    node.attributes["fill"] = "none"
    node.attributes["stroke"] = "#444444"
    assert signal_color(node).get("data-mark", 0) == 0

def test_color_bright_hex_is_saturated():
    node = make_node(tag="circle")
    node.attributes["fill"] = "#e63946"
    node.attributes["stroke"] = ""
    assert signal_color(node).get("data-mark", 0) >= 0.5


# ── Combiner ──────────────────────────────────────────────────────────────────

def test_pick_highest():
    assert pick_label({"data-mark": 0.9, "axis": 0.3}) == "data-mark"

def test_pick_below_threshold():
    assert pick_label({"data-mark": 0.1}) == "unknown"

def test_foreignobject_is_legend():
    assert assign_semantic_to_node(make_node(tag="foreignObject")) == "legend"


# ── assign_semantic_to_tree ───────────────────────────────────────────────────

def test_tree_returns_root():
    root = make_bounded_node(tag="svg", bbox=[0, 0, 1000, 800])
    assert hasattr(assign_semantic_to_tree(make_bounded_tree(root)), "root")

def test_root_gets_label():
    root = make_bounded_node(tag="svg", node_id="data-groups", bbox=[0, 0, 1000, 800])
    assert assign_semantic_to_tree(make_bounded_tree(root)).root.semantic_label != ""

def test_child_receives_parent_context():
    child = make_bounded_node(tag="g", node_id="legend-item")
    parent = make_bounded_node(tag="g", node_id="legend-container",
                               bbox=[800, 100, 1000, 600], children=[child])
    child.parent = parent
    result = assign_semantic_to_tree(make_bounded_tree(parent))
    assert result.root.semantic_label == "legend"
    assert result.root.children[0].semantic_label == "legend-item"

def test_foreignobject_in_tree_is_legend():
    child = make_bounded_node(tag="foreignObject")
    parent = make_bounded_node(tag="svg", bbox=[0, 0, 1000, 800], children=[child])
    child.parent = parent
    result = assign_semantic_to_tree(make_bounded_tree(parent))
    assert result.root.children[0].semantic_label == "legend"

def test_semantic_node_exposes_tag():
    root = make_bounded_node(tag="svg", bbox=[0, 0, 1000, 800])
    assert assign_semantic_to_tree(make_bounded_tree(root)).root.tag == "svg"

def test_semantic_node_exposes_bbox():
    root = make_bounded_node(tag="svg", bbox=[0, 0, 1000, 800])
    assert assign_semantic_to_tree(make_bounded_tree(root)).root.bbox == [0, 0, 1000, 800]

def test_semantic_node_no_bbox_returns_none():
    root = make_bounded_node(tag="svg", bbox=None)
    assert assign_semantic_to_tree(make_bounded_tree(root)).root.bbox is None