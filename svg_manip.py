from svgpathtools import svg2paths
import pandas as pd
from PIL import Image
import os
from game_details import Units

RESOURCE_DIR = os.path.join(os.path.dirname(__file__), 'resources')
SVG_MAP = os.path.join(RESOURCE_DIR, 'GoodSVG.svg')
RESULT_MAP = os.path.join(RESOURCE_DIR, 'result.png')
MAP_PATH = os.path.join(RESOURCE_DIR, 'map.png')
UNIT_PATH = os.path.join(RESOURCE_DIR, 'units')


def box_coords_from_paths():
    paths, attributes = svg2paths(SVG_MAP)
    box_coords = []
    for path in paths:
        xmin, xmax, ymin, ymax = path.bbox()
        shape_min_height = 27  # approx 1/2 expected tile size
        if ymin < shape_min_height:
            continue
        x_center = xmin + (xmax - xmin) / 2
        y_center = ymin + (ymax - ymin) / 2
        coords = {
            'tl': (xmin, ymin),
            'tr': (xmax, ymin),
            'bl': (xmax, ymin),
            'br': (xmax, ymax),
            'ctr': (x_center, y_center)
        }
        box_coords.append(coords)
    return box_coords


# def confine_coords_to_map(coords, map_boxes):
def add_row_col(coords):
    # Create rows by 50 pixel segments
    approx_shape_height = 50
    approx_shape_width = 50
    num_bins_x = round(coords['tl'].str[0].max() / approx_shape_width)
    num_bins_y = round(coords['br'].str[1].max() / approx_shape_height)
    bins_x = [i * 50 for i in range(num_bins_x)]
    bins_y = [i * 50 for i in range(num_bins_y)]
    bin_labels_x = [i + 1 for i in range(len(bins_x) - 1)]
    bin_labels_y = [i + 1 for i in range(len(bins_y) - 1)]

    coords['row'] = pd.cut(coords['tl'].str[0], bins=bins_x, labels=bin_labels_x)
    coords['col'] = pd.cut(coords['tl'].str[1], bins=bins_y, labels=bin_labels_y)
    return coords


def embed_image(base_image, embed_image, coordinates):
    if not isinstance(coordinates, tuple):
        print('Baad coords: {}'.format(coordinates))
    embed_position = (round(coordinates[0]) - embed_image.width // 2, round(coordinates[1]) - embed_image.height // 2)
    base_image.paste(embed_image, embed_position, embed_image)
    return base_image


def place_units(coordinates, base_img_pth, unit_path):
    def get_ctr_by_row_col(coords, row_col):
        coords = coords[(coords['row'] == row_col[0]) & (coords['col'] == row_col[1])]
        return coords['ctr'].min()

    def flip_image(image, direction):
        map = {
            'n': 0,
            'nw': 45,
            'w': 90,
            'sw': 135,
            's': 180,
            'se': 225,
            'e': 270,
            'ne': 315
        }
        image = image.rotate(map[direction.lower()])
        return image

    units = Units()
    map = Image.open(base_img_pth)
    for unit in units.list(active=True).to_dict('records'):
        row_col = (round(unit['end_pos_x']),round(unit['end_pos_y']))
        orientation = unit['end_orientation']
        coords = get_ctr_by_row_col(coordinates, row_col)
        if 'unit' in unit['unit_name'].lower():
            unit_img = 'ra.png'

        elif 'bug' in unit['unit_name'].lower():
            unit_img = 'bug.png'

        elif 'other' in unit['unit_name'].lower():
            unit_img = 'i.png'

        else:
            print('Error')

        embedding_image = Image.open(os.path.join(unit_path, unit_img))
        embedding_image = flip_image(embedding_image, orientation)
        map = embed_image(map, embedding_image, coords)

    map.save(RESULT_MAP)


coords = box_coords_from_paths()
coord_df = pd.DataFrame(coords)
coord_df = add_row_col(coord_df)

# TODO: Create this as a class. Units should be added to the map and then once complete the output should be generated
# TODO: This will work in conjunction with the data stored in the db/json/etc.


place_units(coord_df, MAP_PATH, UNIT_PATH)

## Step 4: Return map via the bot on demand
## Step 5: create Matrix/DF/Table reflecting/controlling the position in the UI
## Step 6: Allow user to modify df/matrix/table
