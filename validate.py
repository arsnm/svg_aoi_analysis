import json
from collections import Counter
from pathlib import Path

CHARTS = {
    'A-a-1': {
        'type': 'geomap',
        'must_find': ['Redwood Hills', 'Silverdale', 'Northgate', 'Golden Hills', 'Woodridge', 'Clearwater',
                      'IRONCLIFF', 'MANSFIELD', 'SILVERBROOK', 'CEDARLAND', 'STORMHAVEN', 'REGION'],
        'expect_axis': 0,
        'expect_marks_min': 10,
    },
    'A-b-1': {
        'type': 'treemap',
        'must_find': ['SUNHAVEN', 'STONEFELL', 'HIGHMOOR', 'RAVENLAND', 'FROSTVALE',
                      'Eastwood', 'Freshwater', 'Greenridge', 'Northwood', 'Silverhill',
                      'Silverwood', 'Westbrook', 'Westwood', 'Darkwood', 'Thornfield'],
        'expect_axis': 0,
        'expect_marks_min': 5,
    },
    'B-a-1': {
        'type': 'lollipop',
        'must_find': ['FOOD ITEM', 'NUTRITIONAL VALUE (g/100g)',
                      'FOOD ITEM GROUP', 'TYPES OF NUTRIENTS',
                      'dishes', 'sandwiches', 'Protein', 'Carbohydrate', 'Fat',
                      '#167', '#190', '#216', '#298', '#300'],
        'expect_axis': 1,
        'expect_marks_min': 5,
    },
    'B-b-1': {
        'type': 'scatter',
        'must_find': ['MATH SCORE AT BEGINING OF HIGHSCHOOL (on a 20-point scale)',
                      'MATH SCORE AT END OF HIGHSCHOO (on a 20-point scale)',
                      'STUDENT ENROLLED', 'IN COLLEGE AFTER', 'GRADUATION',
                      'No', 'Yes'],
        'expect_axis': 35,
        'expect_marks_min': 5,
    },
    'C-a-1': {
        'type': 'choropleth',
        'must_find': ['Dekam', 'Kolos', 'Luna', 'Mumat', 'Samor', 'Sulad',
                      'FLOOD RISK INDEX', '1 - Very low', '7 - Very high'],
        'expect_axis': 0,
        'expect_marks_min': 5,
    },
    'C-b-1': {
        'type': 'calendar heatmap',
        'must_find': ['DAYS', 'SUMMER', 'Jun', 'Jul', 'Aug',
                      'RELATIVE', 'HUMIDITY (%)', '0%', '100%'],
        'expect_axis': 15,
        'expect_marks_min': 10,
    },
    'D-a-1': {
        'type': 'star map',
        'must_find': ['Arun', 'Belaris', 'Caelos', 'Cendara', 'Ciryne', 'Corvane',
                      'Daryn', 'Delvar', 'Eryndor', 'Kelune', 'Kelyth', 'Lunaris',
                      'Mareth', 'Nareth', 'Nerath', 'Orsian', 'Tarvos', 'Thyssar',
                      'Tirros', 'Vaelun', 'Varion', 'Velis', 'Volmar',
                      'Line 1', 'Line 2', 'Line 3', 'Line 4'],
        'expect_axis': 5,
        'expect_marks_min': 10,
    },
    'D-b-1': {
        'type': 'knowledge graph',
        'must_find': ['Blorp', 'Creature', 'Druma', 'Elgok', 'Glom', 'Plant',
                      'Slink', 'Snarg', 'Truz', 'Zint',
                      'eats', 'is a type of', 'poisons', 'LINK TYPE'],
        'expect_axis': 0,
        'expect_marks_min': 5,
    },
    'Ba1Plot': {
        'type': 'lollipop (Observable Plot)',
        'must_find': ['NUTRITIONAL VALUE (g/100g)', 'FOOD ITEM', '0', '35'],
        'expect_axis': 40,
        'expect_marks_min': 5,
    },
    'Ba2Plot': {
        'type': 'lollipop large (Observable Plot)',
        'must_find': ['0', '10', '100'],
        'expect_axis': 60,
        'expect_marks_min': 5,
    },
    'Bb1Plot': {
        'type': 'scatter (Observable Plot)',
        'must_find': ['MATH SCORE AT THE BEGINNING OF HIGHSCHOOL (on a 20-point scale)',
                      'MATH SCORE AT THE END OF HIGHSCHOOL (on a 20-point scale)'],
        'expect_axis': 40,
        'expect_marks_min': 5,
    },
    'Bb2Plot': {
        'type': 'scatter large (Observable Plot)',
        'must_find': ['MATH SCORE AT THE BEGINNING OF HIGHSCHOOL (on a 20-point scale)',
                      'MATH SCORE AT THE END OF HIGHSCHOOL (on a 20-point scale)'],
        'expect_axis': 40,
        'expect_marks_min': 5,
    },
}

all_pass = True

for chart_id, spec in CHARTS.items():
    path = Path(f'data/output/{chart_id}.json')
    if not path.exists():
        print(f'\n=== {chart_id} ({spec["type"]}) === NOT RUN YET')
        all_pass = False
        continue

    with open(path) as f:
        data = json.load(f)

    texts = {item['text'].strip() for item in data if item['text']}
    counts = Counter(item['aoi_label'] for item in data)
    unknown = counts.get('unknown', 0)
    axis = counts.get('axis', 0)
    marks = counts.get('data-mark', 0)

    missing = [t for t in spec['must_find'] if t not in texts]
    axis_ok = axis <= spec['expect_axis'] + 2
    marks_ok = marks >= spec['expect_marks_min']
    unknown_ok = unknown == 0

    status = 'PASS' if (not missing and axis_ok and marks_ok and unknown_ok) else 'FAIL'
    if status == 'FAIL':
        all_pass = False

    print(f'\n=== {chart_id} ({spec["type"]}) === {status}')
    if missing:
        print(f'  MISSING TEXT: {missing}')
    else:
        print(f'  All {len(spec["must_find"])} expected texts found')
    print(f'  data-mark: {marks} (min {spec["expect_marks_min"]}) {"OK" if marks_ok else "TOO LOW"}')
    print(f'  axis: {axis} (expect ~{spec["expect_axis"]}) {"OK" if axis_ok else "HIGH"}')
    print(f'  unknown: {unknown} {"OK" if unknown_ok else "BAD"}')
    print(f'  all labels: { {k: v for k, v in sorted(counts.items())} }')

print(f'\n{"ALL CHARTS PASSED" if all_pass else "SOME CHARTS FAILED"}')


