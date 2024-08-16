import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

def graph(time_seconds, areas, smoke_dir, points):
    fig = plt.figure(figsize=(12, 8))
    gs = fig.add_gridspec(2, 2, width_ratios=[2, 1])

    # First subplot: Cumulative Area
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(time_seconds, areas, label='Area')
    ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('Area')
    ax1.set_title('Area Over Time')
    ax1.grid(True)

    # Second subplot: Growth in area over time
    area_growth = [areas[i+2] - areas[i+1] for i in range(len(areas) - 2)]
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(time_seconds[2:], area_growth, label='Area Growth', color='orange')
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('Growth in Area')
    ax2.set_title('Growth in Area Over Time')
    ax2.grid(True)

    # Third subplot: Wind Direction plot
    ax3 = fig.add_subplot(gs[0, 1], polar=True)
    ax3.hist(np.radians(smoke_dir), bins=30, color='skyblue', alpha=0.7)
    ax3.set_xlabel('Direction', fontsize=12)
    ax3.set_theta_direction(-1)
    ax3.set_rticks([])  # Remove radial ticks
    ax3.set_title('Wind Direction')

    # Fourth subplot: Path representation
    ax4 = fig.add_subplot(gs[1, 1])
    x, y = zip(*points)
    ax4.plot(x, y, marker='o', color='orange', markersize=3, label='Path')
    ax4.invert_yaxis()

    # Label the start and end points
    ax4.plot(x[0], y[0], marker='*', color='red', markersize=10, label='Start')
    ax4.plot(x[-1], y[-1], marker='*', color='green', markersize=10, label='End')

    ax4.set_xlabel('X Coordinate')
    ax4.set_ylabel('Y Coordinate')
    ax4.set_title('Path Representation')
    ax4.grid(True)
    ax4.legend()

    plt.tight_layout()
    # plt.savefig('forest_fire_analysis1.png', dpi=300, bbox_inches='tight')

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)

    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')

    return img_str
