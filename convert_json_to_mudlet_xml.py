import glob
import json
import os
from argparse import ArgumentParser
from rom import dir_to_direction
from lxml import etree

parser = ArgumentParser(description="Process a directory of .json files and outputs them to mudlet's xml map format.")
parser.add_argument('-i', '--input', required=True, help='Directory to search for .json files to parse')
parser.add_argument('-o', '--output', required=True, help='Output file for map xml')


def dict_to_element(d, name):
    element = etree.Element(name)
    for k, v in d.items():
        element.attrib[k] = str(v)

    return element


if __name__ == "__main__":
    args = parser.parse_args()

    map = etree.Element("map")
    areas = etree.SubElement(map, "areas")
    rooms = etree.SubElement(map, "rooms")
    environments = etree.SubElement(map, "environments")

    # Parse all the json files in the input directory
    area_files = glob.glob(os.path.join(args.input, '*.json'))
    if len(area_files) == 0:
        print(f"Could find any *.json files in directory '{args.input}'")
        exit(1)

    # We need to assigned ids to each area, keep track
    current_area_id = 1
    for file in area_files:
        with open(file, "rt") as fs:
            data = json.loads(fs.read())

            area = {
                "id": current_area_id,
                "name": data['name'],
                "x": 0,
                "y": 0
            }

            environment = {
                "id": current_area_id,
                "name": data['name'],
                "color": 1,
                "htmlcolor": "#00B300"
            }

            environments.append(dict_to_element(environment, "environment"))

            # Add area element
            areas.append(dict_to_element(area, "area"))

            for r in data['rooms']:
                room = {
                    "id": r['vnum'],
                    "area": current_area_id,
                    "title": r['name'],
                    "environment": 1
                }

                # Add the room element
                vnum = r['vnum']
                room = dict_to_element(room, "room")
                coord = r['coords']

                if coord is None:
                    print(f"[WARNING] Room {vnum} has no coordinates.  This _could_ be fine, if for instance, the room is a pet store shop.")
                    continue

                room.append(dict_to_element(coord, "coord"))

                for e in r['exits']:
                    target = e['to']
                    direction = dir_to_direction(e['direction'])
                    exit = {
                        "direction": direction,
                        "target": target
                    }

                    room.append(dict_to_element(exit, "exit"))
                rooms.append(room)

        current_area_id += 1

    with open(args.output, "w+") as out_file:
        pretty_xml = etree.tostring(map, pretty_print=True, encoding='utf-8', xml_declaration=True).decode("utf-8")
        out_file.write(pretty_xml)
        print(f"File '{args.output}' written successfully.")
