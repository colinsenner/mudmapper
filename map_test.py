import matplotlib.pyplot as plt
import numpy as np

# Define points (nodes)
points = np.array([[1, 2], [4, 5], [2, 7], [3, 9], [9, 2]])

# Define edges as pairs of indices into the points array
edges = np.array([[0, 1], [3, 4], [3, 2], [2, 4]])

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