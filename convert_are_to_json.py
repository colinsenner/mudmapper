import glob
import os
from argparse import ArgumentParser

from rom import Area

parser = ArgumentParser(description='Process a directory of .are files and outputs them to json.')
parser.add_argument('-i', '--input', required=True, help='Directory to search for .are files to parse')
parser.add_argument('-o', '--output', required=True, help='Directory to save the json output')


def write_to_json(area, out_file):
    with open(out_file, "w+") as out:
        out.write(area.toJSON())


if __name__ == "__main__":
    args = parser.parse_args()

    area_files = glob.glob(os.path.join(args.input, '*.are'))

    if len(area_files) == 0:
        print(f"Could find any *.are files in directory '{args.input}'")
        exit(1)

    for file in area_files:
        # There's some files I don't care to parse because they don't contain map data
        ignore_files = ['group.are', 'help.are', 'rom.are', 'proto.are', 'social.are']

        if os.path.basename(file) in ignore_files:
            print(f"Skipping file '{file}' because it's in the ignore list")
            continue

        print(f"Loading file {file}...")
        area = Area.load(file)

        basename = os.path.basename(file)
        filename = os.path.splitext(basename)[0] + '.json'
        out_file = os.path.join(args.output, filename)
        write_to_json(area, out_file)

        print(f"Output written to: '{out_file}'")
