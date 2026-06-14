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
        Processes an SVG stimulus file and returns the defined generic JSON format
        and a simplified SVG representation.
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

        # 5. 
        #  Generation
        return {
            "json": json.dumps(filtered_data, indent=4),
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

            # Determine type and family from Semantic label
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
                "text": text_val
            }

            extracted_data.append(aoi_entry)

            for child in node.children:
                traverse(child, current_id)

        traverse(root_node, None)
        return extracted_data
    
    def _filter_to_visible(self, extracted_data: list[dict]) -> list[dict]:
        KEEP_TAGS = {'path', 'circle', 'rect', 'line', 'polygon', 
                    'polyline', 'ellipse', 'text', 'foreignObject',
                    'div', 'span'}
        
        filtered = []
        for item in extracted_data:
            tag = item['tag']
            label = item['aoi_label']
            
            # Always drop pure container labels
            # Always drop pure container labels — but never drop text elements
            if label in ('data-container', 'unknown'):
                if tag == 'text':
                    filtered.append(item)
                continue
                
            # Keep only non-g tags — these are actual visible elements
            if tag != 'g':
                filtered.append(item)
        
        return filtered
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
            # Using nodes dictionary to form the tree
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
            
            # Start tag: group wrapping this AOI entirely
            elements.append(f'{indent}<g id="{group_id}" data-type="{aoi["aoi_type"]}" data-original-tag="{aoi["tag"]}">')
            
            bbox = aoi["bbox"]
            if bbox:
                b_min_x, b_min_y, b_max_x, b_max_y = bbox
                width = b_max_x - b_min_x
                height = b_max_y - b_min_y
                
                # Draw the bounding box visualization
                elements.append(f'{indent}    <rect x="{b_min_x}" y="{b_min_y}" width="{width}" height="{height}" fill="none" stroke="red" stroke-width="1" />')
                
                # Draw text context
                text_desc = f"{aoi['aoi_label']} ({aoi['aoi_type']})"
                if aoi["text"]:
                    safe_text = aoi["text"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
                    text_desc += f' | "{safe_text}"'
                    
                elements.append(f'{indent}    <text x="{b_min_x}" y="{b_min_y - 2}" font-size="10" fill="blue" font-family="sans-serif">{text_desc}</text>')
                
            # Process strictly nested children inner
            for child in children:
                elements.extend(build_svg_nodes(child, indent_level + 1))
                
            # Close this group
            elements.append(f'{indent}</g>')
            
            return elements

        svg_elements = []
        for root in roots:
            svg_elements.extend(build_svg_nodes(root, 1))

        # Handle case where no valid bboxes were found
        if min_x == float('inf'):
            min_x, min_y, max_x, max_y = 0, 0, 800, 600
        else:
            # Add padding
            padding = 20
            min_x -= padding
            min_y -= padding
            max_x += padding
            max_y += padding
            
        vb_width = max_x - min_x
        vb_height = max_y - min_y
        
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

        json_path = output_dir / f"{svg_path.stem}.json"
        svg_out_path = output_dir / f"{svg_path.stem}_simplified.svg"

        json_path.write_text(results["json"], encoding="utf-8")
        svg_out_path.write_text(results["simplified_svg"], encoding="utf-8")

        print(f"JSON saved to:         {json_path}")
        print(f"Simplified SVG saved to: {svg_out_path}")
