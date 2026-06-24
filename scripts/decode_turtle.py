#!/usr/bin/env python3

import math
import re
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

TURTLE_FILE = '/home/pulgamecanica/42Org/boot2root/turtle'
OUTPUT_IMAGE = '/home/pulgamecanica/42Org/boot2root/turtle_message.png'

rx_dict = {
    'right':    re.compile(r'^Tourne droite de (\d+) degrees'),
    'left':     re.compile(r'^Tourne gauche de (\d+) degrees'),
    'forward':  re.compile(r'^Avance (\d+) spaces'),
    'backward': re.compile(r'^Recule (\d+) spaces')
}

def simulate_figure(instructions, start_heading=90):
    x, y = 0.0, 0.0
    heading = start_heading
    points = [(x, y)]
    for cmd, val in instructions:
        val = int(val)
        rad = math.radians(heading)
        if cmd == 'forward':
            x += val * math.cos(rad)
            y += val * math.sin(rad)
            points.append((x, y))
        elif cmd == 'backward':
            x -= val * math.cos(rad)
            y -= val * math.sin(rad)
            points.append((x, y))
        elif cmd == 'left':
            heading += val
        elif cmd == 'right':
            heading -= val
    return points

figures = []
figure = []
with open(TURTLE_FILE, 'r') as f:
    for line in f:
        if line == "\n":
            if figure:
                figures.append(figure.copy())
            figure.clear()
        for key, rx in rx_dict.items():
            match = rx.search(line)
            if match:
                figure.append((key, match.group(1)))

fig, axes = plt.subplots(1, len(figures), figsize=(4 * len(figures), 6))
fig.patch.set_facecolor('black')

for i, instructions in enumerate(figures):
    pts = simulate_figure(instructions, start_heading=90)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    ax = axes[i]
    ax.set_facecolor('black')
    ax.plot(xs, ys, color='lime', linewidth=1.5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f'Fig {i+1}', color='white', fontsize=10)

plt.suptitle('Turtle Message', color='white', fontsize=14)
plt.tight_layout()
plt.savefig(OUTPUT_IMAGE, dpi=150, bbox_inches='tight', facecolor='black')
print(f"[*] Image saved to {OUTPUT_IMAGE}")
