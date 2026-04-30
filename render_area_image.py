'''Render a single .are file as a PNG image map.

For each z-level present in the area, writes one PNG showing rooms as
labelled squares and connections as cardinal lines between them.
'''
import os
from argparse import ArgumentParser
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from rom import Area
from rom.merc import dir_to_direction


parser = ArgumentParser(description=__doc__)
parser.add_argument('-i', '--input', required=True, help='Path to the .are file')
parser.add_argument('-o', '--output', required=True,
                    help='Output image path. If the area spans multiple z-levels, '
                         '"_z<level>" is inserted before the extension.')
parser.add_argument('--cell-size', type=float, default=0.8,
                    help='Side length of a room square in grid units (default 0.8)')
parser.add_argument('--dpi', type=int, default=150, help='Output DPI (default 150)')


_DIR_DELTAS = {
    'north': (0, 1), 'south': (0, -1),
    'east':  (1, 0), 'west':  (-1, 0),
}


def _draw_level(rooms_at_z, all_coords, out_path, cell_size, dpi, title):
    '''rooms_at_z: list of Room with coords on this z. all_coords: dict vnum->(x,y,z) for the whole area (so cross-level exits can be flagged).'''
    xs = [r.coords.x for r in rooms_at_z]
    ys = [r.coords.y for r in rooms_at_z]
    if not xs:
        return

    pad = 1.5
    xmin, xmax = min(xs) - pad, max(xs) + pad
    ymin, ymax = min(ys) - pad, max(ys) + pad

    width = max(8, (xmax - xmin) * 0.4)
    height = max(8, (ymax - ymin) * 0.4)

    fig, ax = plt.subplots(figsize=(width, height))
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect('equal')
    ax.set_facecolor('black')
    fig.patch.set_facecolor('black')
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(title, color='white')

    half = cell_size / 2.0

    # Per-room flags for vertical exits, drawn as arrows on the room itself.
    has_up = set()
    has_down = set()

    # Draw connection lines first so rooms render on top.
    for room in rooms_at_z:
        ax_x, ax_y = room.coords.x, room.coords.y
        for exit_ in room.exits:
            target = all_coords.get(exit_.to)
            direction = dir_to_direction(exit_.direction)

            if direction == 'up':
                has_up.add(room.vnum)
                continue
            if direction == 'down':
                has_down.add(room.vnum)
                continue

            if target is None:
                # External / unmapped exit — draw a short stub arrow.
                if direction in _DIR_DELTAS:
                    dxx, dyy = _DIR_DELTAS[direction]
                    ax.annotate('', xy=(ax_x + dxx * 0.7, ax_y + dyy * 0.7),
                                xytext=(ax_x, ax_y),
                                arrowprops=dict(arrowstyle='->', color='red', lw=1))
                continue

            tx, ty, tz = target
            if tz != room.coords.z:
                # Cardinal exit on a different z (rare) — skip line.
                continue

            # Cardinal line between the two rooms on this level.
            ax.plot([ax_x, tx], [ax_y, ty], color='lightgray', lw=1, zorder=1)

    # Draw rooms (and up/down arrows on top of them).
    arrow_inset = cell_size * 0.22
    arrow_size = cell_size * 0.32
    for room in rooms_at_z:
        x, y = room.coords.x, room.coords.y
        ax.add_patch(Rectangle((x - half, y - half), cell_size, cell_size,
                               facecolor='#7a1d1d', edgecolor='white', lw=0.8,
                               zorder=2))
        ax.text(x, y, str(room.vnum), ha='center', va='center',
                fontsize=5.5, color='white', zorder=3)

        if room.vnum in has_up:
            tip_x = x + half - arrow_inset
            base_y = y + half - arrow_inset - arrow_size
            tip_y = y + half - arrow_inset
            ax.fill([tip_x - arrow_size / 2, tip_x + arrow_size / 2, tip_x],
                    [base_y, base_y, tip_y],
                    color='#7fe07f', zorder=4)

        if room.vnum in has_down:
            tip_x = x + half - arrow_inset
            base_y = y - half + arrow_inset + arrow_size
            tip_y = y - half + arrow_inset
            ax.fill([tip_x - arrow_size / 2, tip_x + arrow_size / 2, tip_x],
                    [base_y, base_y, tip_y],
                    color='#ff8888', zorder=4)

    plt.tight_layout()
    fig.savefig(out_path, dpi=dpi, facecolor='black')
    plt.close(fig)
    print(f"Wrote {out_path}")


if __name__ == '__main__':
    args = parser.parse_args()

    area = Area.load(args.input)

    rooms_with_coords = [r for r in area.rooms if r.coords is not None]
    by_z = defaultdict(list)
    for r in rooms_with_coords:
        by_z[r.coords.z].append(r)

    all_coords = {r.vnum: (r.coords.x, r.coords.y, r.coords.z)
                  for r in rooms_with_coords}

    base, ext = os.path.splitext(args.output)
    multi = len(by_z) > 1

    for z, rooms in sorted(by_z.items()):
        out_path = f"{base}_z{z}{ext}" if multi else args.output
        title = f"{area.name}  (z={z})" if multi else area.name
        _draw_level(rooms, all_coords, out_path, args.cell_size, args.dpi, title)
