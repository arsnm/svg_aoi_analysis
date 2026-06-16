# pipeline.py
#
# Module for tying together the parsing, geometry, and semantic steps into a
# unified extraction pipeline. Provides the functionality to run an SVG file
# through all steps and output the resulting AOI representation as JSON.

import json
from pathlib import Path

from .parser import SVGTreeRaw
from .geometry import assign_bounding_to_tree
from .semantic import assign_semantic_to_tree, SVGTreeNodeSemantic
from .utils import normalize_path

class AOIPipeline:
    """
    The main pipeline combining parsing, bounding, and semantic assignment.
    """
    def __init__(self, curve_resolution: int = 16, line_epsilon: float = 0.0):
        self.curve_resolution = curve_resolution
        self.line_epsilon = line_epsilon

    def process_svg(self, svg_path: str | Path) -> dict[str, str]:
        """
        Processes an SVG stimulus file and returns the defined generic JSON format,
        a hierarchy JSON, and a simplified SVG representation.
        """
        svg_path = normalize_path(str(svg_path))
        stimulus_id = svg_path.stem

        # 1. Parsing and Cleaning
        raw_tree = SVGTreeRaw(svg_path)
        raw_tree.clean_tree()

        # 2. Geometric Bounding
        bounded_tree = assign_bounding_to_tree(
            raw_tree,
            curve_resolution=self.curve_resolution,
            line_epsilon=self.line_epsilon
        )

        # 3. Semantic Assignment
        semantic_tree = assign_semantic_to_tree(bounded_tree)

        # 4. Data Extraction
        extracted_data = self._extract_data(semantic_tree.root, stimulus_id)
        filtered_data = self._filter_to_visible(extracted_data)
        filtered_data = self._link_categories(filtered_data, extracted_data)

        # 5. Build id → category map for hierarchy annotation
        id_to_category = {
            item['aoi_id']: item['category']
            for item in filtered_data
            if item.get('category')
        }

        # 6. Build hierarchy
        hierarchy = self._build_hierarchy(filtered_data, extracted_data)

        # 7. Generate simplified SVG
        return {
            "json": json.dumps(filtered_data, indent=4),
            "hierarchy": json.dumps(hierarchy, indent=4),
            "simplified_svg": self._generate_simplified_svg(extracted_data, svg_path)
        }

    def _extract_data(self, root_node: SVGTreeNodeSemantic, stimulus_id: str) -> list[dict]:
        extracted_data = []
        node_id_counter = 1

        def traverse(node: SVGTreeNodeSemantic, parent_id: str | None):
            nonlocal node_id_counter

            current_id = f"aoi_{node_id_counter}"
            node_id_counter += 1

            bbox = None
            if node.bounding is not None:
                bbox = list(node.bounding.bounds)

            semantics = node.semantic_label.split('-')
            if len(semantics) > 1:
                family = semantics[0]
                aoi_type = "-".join(semantics[1:])
            else:
                family = semantics[0]
                aoi_type = semantics[0]

            text_val = getattr(node, "text", "")
            if text_val is None:
                text_val = ""
            else:
                text_val = text_val.strip()

            aoi_entry = {
                "stimulus_id": stimulus_id,
                "aoi_id": current_id,
                "aoi_label": node.semantic_label,
                "aoi_type": aoi_type,
                "family": family,
                "tag": node.tag,
                "parent_id": parent_id,
                "bbox": bbox,
                "text": text_val,
                "fill": node.attributes.get("fill", "").strip().lower(),
                "d": node.attributes.get("d", "")
            }

            extracted_data.append(aoi_entry)

            for child in node.children:
                traverse(child, current_id)

        traverse(root_node, None)
        return extracted_data

    def _normalize_color(self, color: str):
        """Convert any CSS color string to an (r,g,b) tuple for comparison."""
        if not color:
            return None
        color = color.strip().lower()
        if color in ('none', 'inherit', 'transparent', 'currentcolor', ''):
            return None
        if len(color) == 4 and color.startswith('#'):
            color = '#' + color[1]*2 + color[2]*2 + color[3]*2
        if len(color) == 7 and color.startswith('#'):
            try:
                return (int(color[1:3], 16),
                        int(color[3:5], 16),
                        int(color[5:7], 16))
            except ValueError:
                return None
        return None

    def _shape_signature(self, item: dict) -> tuple:
        """
        Builds a signature describing an element's visual shape,
        used to match data-marks to legend symbols when color alone
        isn't distinctive.
        """
        tag = item["tag"]
        fill = self._normalize_color(item["fill"])

        bbox = item["bbox"]
        aspect = None
        if bbox:
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            if h > 0:
                aspect = round(w / h, 1)

        complexity = None
        if tag == "path":
            d = item.get("d", "")
            complexity = round(len(d.split()) / 5) * 5

        return (tag, fill, aspect, complexity)

    def _link_categories(self, filtered_data: list[dict], all_data: list[dict]) -> list[dict]:
        """
        Builds one category map per legend group (identified by legend-title),
        then matches each data-mark against all groups, returning a dict of
        {legend_title: category_name} per element.
        """
        legend_groups = {}
        current_title = "default"
        current_symbols = []
        current_labels = []

        for item in all_data:
            label = item["aoi_label"]
            if label == "legend-title" and item["text"]:
                if current_symbols or current_labels:
                    legend_groups[current_title] = {
                        "symbols": current_symbols,
                        "labels": current_labels
                    }
                current_title = item["text"]
                current_symbols = []
                current_labels = []
            elif label == "legend-item-symbol":
                current_symbols.append(item)
            elif label == "legend-item-label" and item["text"]:
                current_labels.append(item["text"])

        if current_symbols or current_labels:
            legend_groups[current_title] = {
                "symbols": current_symbols,
                "labels": current_labels
            }

        group_signatures = {}
        for title, group in legend_groups.items():
            sig_map = {}
            symbols = group["symbols"]
            labels = group["labels"]
            for i, sym in enumerate(symbols):
                if i < len(labels):
                    sig = self._shape_signature(sym)
                    sig_map[sig] = labels[i]
            group_signatures[title] = sig_map

        for item in filtered_data:
            if item["aoi_label"] in ("data-mark", "data-node"):
                sig = self._shape_signature(item)
                categories = {}

                for title, sig_map in group_signatures.items():
                    category = None

                    # 1. Full signature match
                    category = sig_map.get(sig)

                    # 2. Color only match
                    if category is None and sig[1] is not None:
                        for leg_sig, name in sig_map.items():
                            if leg_sig[1] == sig[1]:
                                category = name
                                break

                    # 3. Tag + aspect match
                    if category is None and sig[0] and sig[2]:
                        for leg_sig, name in sig_map.items():
                            if leg_sig[0] == sig[0] and leg_sig[2] == sig[2]:
                                category = name
                                break

                    if category is not None:
                        categories[title] = category

                item["category"] = categories if categories else None
            else:
                item["category"] = None

        return filtered_data

    def _filter_to_visible(self, extracted_data: list[dict]) -> list[dict]:
        filtered = []
        for item in extracted_data:
            tag = item['tag']
            label = item['aoi_label']

            # Drop container and unknown labels — but never drop text elements
            if label in ('data-container', 'unknown'):
                if tag == 'text':
                    filtered.append(item)
                continue

            # Keep non-g tags (actual visible elements)
            # Also keep g tags labeled as data-link (route groups)
            if tag != 'g':
                filtered.append(item)
            elif label == 'data-link':
                filtered.append(item)

        return filtered

    def _build_hierarchy(self, filtered_data: list[dict], all_data: list[dict]) -> dict:
        """
        Builds a clean human-readable hierarchy from the flat filtered AOI list.
        Structure:
        - data-container: data-marks and data-labels numbered sequentially
        - legend: grouped by legend title, items numbered sequentially
        - axis: axis labels and ticks numbered sequentially
        - grid: grid lines numbered sequentially
        """
        result = {"stimulus_id": filtered_data[0]["stimulus_id"] if filtered_data else ""}

        counters = {}
        def next_key(label):
            counters[label] = counters.get(label, 0) + 1
            return f"{label}-{counters[label]}"

        # Data container
        data_section = {}
        for item in filtered_data:
            label = item["aoi_label"]
            if label in ("data-mark", "data-node", "data-link"):
                key = next_key("data-mark")
                entry = {"bbox": item["bbox"]}
                if item.get("fill") and item["fill"] not in ("none", ""):
                    entry["fill"] = item["fill"]
                if item.get("category"):
                    entry["category"] = item["category"]
                if item.get("text"):
                    entry["text"] = item["text"]
                data_section[key] = entry
            elif label == "data-label":
                if item.get("text"):
                    key = next_key("data-label")
                    data_section[key] = {
                        "text": item["text"],
                        "bbox": item["bbox"]
                    }
        if data_section:
            result["data-container"] = data_section

        # Legend
        legend_groups = {}
        current_title = "default"
        current_symbols = []
        current_labels = []
        for item in all_data:
            lbl = item["aoi_label"]
            if lbl == "legend-title" and item["text"]:
                if current_symbols or current_labels:
                    legend_groups[current_title] = {
                        "symbols": current_symbols,
                        "labels": current_labels
                    }
                current_title = item["text"]
                current_symbols = []
                current_labels = []
            elif lbl == "legend-item-symbol":
                current_symbols.append(item)
            elif lbl == "legend-item-label" and item["text"]:
                current_labels.append(item["text"])
        if current_symbols or current_labels:
            legend_groups[current_title] = {
                "symbols": current_symbols,
                "labels": current_labels
            }

        legend_section = {}
        for title, group in legend_groups.items():
            group_entries = {}
            symbols = group["symbols"]
            labels = group["labels"]
            for i, sym in enumerate(symbols):
                entry = {}
                if i < len(labels):
                    entry["text"] = labels[i]
                if sym.get("fill") and sym["fill"] not in ("none", ""):
                    entry["fill"] = sym["fill"]
                group_entries[f"legend-item-{i+1}"] = entry
            legend_section[title] = group_entries
        if legend_section:
            result["legend"] = legend_section

        # Axis 
        axis_section = {}
        axis_counters = {}
        def next_axis_key(sublabel):
            axis_counters[sublabel] = axis_counters.get(sublabel, 0) + 1
            return f"{sublabel}-{axis_counters[sublabel]}"
        for item in filtered_data:
            label = item["aoi_label"]
            if label in ("axis", "axis-title", "axis-label", "axis-tick"):
                key = next_axis_key(label)
                entry = {}
                if item.get("text"):
                    entry["text"] = item["text"]
                if item.get("bbox"):
                    entry["bbox"] = item["bbox"]
                axis_section[key] = entry
        if axis_section:
            result["axis"] = axis_section

        #  Grid
        grid_section = {}
        grid_counter = 0
        for item in filtered_data:
            if item["aoi_label"] == "grid":
                grid_counter += 1
                grid_section[f"grid-{grid_counter}"] = {"bbox": item["bbox"]}
        if grid_section:
            result["grid"] = grid_section

        return result

    def _generate_simplified_svg(self, extracted_data: list[dict], svg_path: Path = None) -> str:
        """
        Generates a simplified SVG showing the bounding boxes, preserving the hierarchy.
        """
        min_x, min_y, max_x, max_y = float('inf'), float('inf'), float('-inf'), float('-inf')

        nodes = {}
        roots = []

        for aoi in extracted_data:
            nodes[aoi['aoi_id']] = {'data': aoi, 'children': []}
            bbox = aoi["bbox"]
            if bbox:
                min_x = min(min_x, bbox[0])
                min_y = min(min_y, bbox[1])
                max_x = max(max_x, bbox[2])
                max_y = max(max_y, bbox[3])

        for aoi in extracted_data:
            parent_id = aoi['parent_id']
            current_node = nodes[aoi['aoi_id']]
            if parent_id is None:
                roots.append(current_node)
            else:
                nodes[parent_id]['children'].append(current_node)

        def build_svg_nodes(node_item, indent_level) -> list[str]:
            indent = "    " * indent_level
            aoi = node_item['data']
            children = node_item['children']

            elements = []
            group_id = f"{aoi['aoi_id']}_{aoi['aoi_label']}"

            elements.append(f'{indent}<g id="{group_id}" data-type="{aoi["aoi_type"]}" data-original-tag="{aoi["tag"]}">')

            bbox = aoi["bbox"]
            if bbox:
                b_min_x, b_min_y, b_max_x, b_max_y = bbox
                width = b_max_x - b_min_x
                height = b_max_y - b_min_y

                elements.append(f'{indent}    <rect x="{b_min_x}" y="{b_min_y}" width="{width}" height="{height}" fill="none" stroke="red" stroke-width="1" />')

                text_desc = f"{aoi['aoi_label']} ({aoi['aoi_type']})"
                if aoi["text"]:
                    safe_text = aoi["text"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
                    text_desc += f' | "{safe_text}"'

                elements.append(f'{indent}    <text x="{b_min_x}" y="{b_min_y - 2}" font-size="10" fill="blue" font-family="sans-serif">{text_desc}</text>')

            for child in children:
                elements.extend(build_svg_nodes(child, indent_level + 1))

            elements.append(f'{indent}</g>')
            return elements

        svg_elements = []
        for root in roots:
            svg_elements.extend(build_svg_nodes(root, 1))

        if min_x == float('inf'):
            min_x, min_y, max_x, max_y = 0, 0, 800, 600
        else:
            padding = 20
            min_x -= padding
            min_y -= padding
            max_x += padding
            max_y += padding

        vb_width = max_x - min_x
        vb_height = max_y - min_y

        if svg_path:
            svg_header = (
                f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'viewBox="{min_x} {min_y} {vb_width} {vb_height}">\n'
                f'    <image href="{svg_path}" '
                f'x="{min_x}" y="{min_y}" '
                f'width="{vb_width}" height="{vb_height}" '
                f'preserveAspectRatio="xMidYMid meet" />'
            )
        else:
            svg_header = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x} {min_y} {vb_width} {vb_height}">'

        svg_footer = '</svg>'
        return "\n".join([svg_header] + svg_elements + [svg_footer])


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        svg_path = Path(sys.argv[1])
        pipeline = AOIPipeline()
        results = pipeline.process_svg(svg_path)

        output_dir = svg_path.parent.parent / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        json_path = output_dir /f"{svg_path.stem}.json"
        svg_out_path = output_dir / f"{svg_path.stem}_simplified.svg"
        hierarchy_path = output_dir / f"{svg_path.stem}_hierarchy.json"

        json_path.write_text(results["json"], encoding="utf-8")
        svg_out_path.write_text(results["simplified_svg"], encoding="utf-8")
        hierarchy_path.write_text(results["hierarchy"], encoding="utf-8")

        print(f"JSON saved to:           {json_path}")
        print(f"Simplified SVG saved to: {svg_out_path}")
        print(f"Hierarchy JSON saved to: {hierarchy_path}")