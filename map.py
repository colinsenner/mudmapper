import matplotlib.pyplot as plt
import numpy as np
import pickle

with open("area.pickle", "rb") as f:
    area = pickle.load(f)



graph = []

for room in area.rooms:
    if room.coords:
        item = {
            "vnum": room.vnum,
            "exits": [exit.to for exit in room.exits],
            "coords": room.coords
        }
        graph.append(item)


vertices = []
connections = []
for node in graph:
    x, y, z = node["coords"].x, node["coords"].y, node["coords"].z
    vertices.append((x, y, z))

# Create a mapping of coordinates to indices in the vertices array
coord_to_index = {tuple(coord): idx for idx, coord in enumerate(vertices)}

# Build edges as pairs of indices
connections = []
for node in graph:
    current_index = coord_to_index[(node["coords"].x, node["coords"].y, node["coords"].z)]

    items = []
    for exit_vnum in node["exits"]:
        # Find the target room in the graph
        target_node = next((n for n in graph if n["vnum"] == exit_vnum), None)
        if target_node:
            target_index = coord_to_index[(target_node["coords"].x, target_node["coords"].y, target_node["coords"].z)]
            connections.append((current_index, target_index))
    
    # connections.append(items)

# Define points (nodes)
points = np.array(vertices)

# Define edges as pairs of indices into the points array
edges = np.array(connections)
# points = np.array([[1, 2], [4, 5], [2, 7], [3, 9], [9, 2]])

# Extract x and y coordinates for plotting points
x = points[:, 0]
y = points[:, 1]

# Plot points as a scatter plot
plt.scatter(x, y, color='blue', marker='o', s=100) # s is marker size

# Plot edges
for edge in edges:
    start_point = points[edge[0]]
    end_point = points[edge[1]]
    plt.plot([start_point[0], end_point[0]], [start_point[1], end_point[1]], color='gray', linestyle='-')

plt.title('Points and Edges Visualization (Matplotlib)')
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.grid(True)
plt.show()
pass