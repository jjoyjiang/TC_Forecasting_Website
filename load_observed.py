import matplotlib.pyplot as plt
import os

# Sample data
x = [1, 2, 3, 4, 5]
y = [2.3, 3.5, 1.2, 4.8, 3.3]

# Define the output path
output_dir = 'outputs/plots'
output_path = os.path.join(output_dir, 'scatterplot.png')

# Create directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Delete the file if it already exists
if os.path.exists(output_path):
    os.remove(output_path)
    print(f"Deleted existing file: {output_path}")

# Create the scatterplot
plt.figure(figsize=(6, 4))
plt.scatter(x, y, color='blue', label='Data points')
plt.title('Sample Scatterplot')
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.legend()

# Save the figure
plt.savefig(output_path)
plt.close()

print(f"New plot saved to {output_path}")