from pathlib import Path
import numpy as np
from scipy.ndimage import map_coordinates
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from matplotlib.colors import ListedColormap

OUT = Path(__file__).resolve().parent
CELL = 40
NX, NY = 400, 50
WIDTH, HEIGHT = NX * CELL, NY * CELL
SEED, COMPONENTS = 42, 400
THRESHOLDS = np.array([3, 5, 8, 10, 12])
TIMES = np.array([0, 300, 1000])
VELOCITY = -5
STARTS = -VELOCITY * TIMES

plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'],
                     'mathtext.fontset': 'stix', 'font.size': 7, 'axes.linewidth': 0.55,
                     'pdf.fonttype': 42, 'ps.fonttype': 42, 'svg.fonttype': 'none'})
rng = np.random.default_rng(SEED)
x = (np.arange(NX) + 0.5) * CELL
y = (np.arange(NY) + 0.5) * CELL
X, Y = np.meshgrid(x, y)
cx = rng.uniform(0, WIDTH, COMPONENTS)
cy = rng.uniform(0, HEIGHT, COMPONENTS)
sx = rng.uniform(60, 220, COMPONENTS)
sy = rng.uniform(60, 220, COMPONENTS)
sx[:40] = rng.uniform(220, 380, 40)
sy[:40] = rng.uniform(140, 280, 40)
amplitude = rng.uniform(2.0, 8.5, COMPONENTS)
field = np.zeros((NY, NX))
for j in range(COMPONENTS):
    field += amplitude[j] * np.exp(-0.5 * (((X-cx[j])/sx[j])**2 + ((Y-cy[j])/sy[j])**2))
field = np.clip(field, 0, 15)
masks = np.array([field >= threshold for threshold in THRESHOLDS])
# The 1500 m window starts halfway between background columns: bilinear sampling
# preserves its exact geometry and draws on the same sampled background field.
local = np.stack([map_coordinates(field, np.meshgrid(np.arange(NY),
                   (start + (np.arange(50) + 0.5)*CELL)/CELL - 0.5,
                   indexing='ij'), order=1, mode='nearest') for start in STARTS])
assert field.shape == (50, 400) and local.shape == (3, 50, 50)
assert CELL * 50 == 2000 and np.array_equal(STARTS, [0, 1500, 5000])
assert field.min() >= 0 and field.max() <= 15
assert all(np.array_equal(mask, field >= threshold) for mask, threshold in zip(masks, THRESHOLDS))
assert all(np.all(~masks[i+1] | masks[i]) for i in range(len(masks)-1))
assert np.array_equal(local[0], field[:, 0:50]) and np.array_equal(local[2], field[:, 125:175])
np.savez_compressed(OUT / 'cloud_field_data.npz', field=field, masks=masks, thresholds=THRESHOLDS,
                    local_fields=local, starts=STARTS, times=TIMES, cell_m=CELL, seed=SEED,
                    component_x=cx, component_y=cy, sigma_x=sx, sigma_y=sy, amplitude=amplitude)

cmap = ListedColormap(['white', '#202020'])
extent = (0, WIDTH, 0, HEIGHT)

def base_axis(ax):
    ax.set_xlim(0, WIDTH); ax.set_ylim(0, HEIGHT)
    ax.set_xticks(np.arange(0, WIDTH+1, 2000)); ax.set_yticks([0, 1000, 2000])
    ax.tick_params(labelsize=6.3, length=2, pad=2)
    ax.set_ylabel('$y$ (m)', labelpad=2)

def windows(ax, labels=True):
    for start, t in zip(STARTS, TIMES):
        ax.add_patch(Rectangle((start, 0), 2000, 2000, fill=False, ec='#c51e28',
                               lw=0.9, zorder=3, clip_on=False))
        if labels:
            ax.text(start+1000, 1.10, rf'$t={t}$ s', transform=ax.get_xaxis_transform(),
                    color='#b31c24', ha='center', va='bottom', fontsize=7)

def save(fig, stem):
    for extension in ('pdf', 'svg', 'png'):
        fig.savefig(OUT / f'{stem}.{extension}', dpi=600, facecolor='white')
    plt.close(fig)

fig = plt.figure(figsize=(7.2, 3.25))
fig.suptitle('Dynamic Gaussian Cloud Map and Binary Cloud Blockage Model', fontsize=9, y=0.98)
ax1 = fig.add_axes([0.10, 0.64, 0.74, 0.205])
ax2 = fig.add_axes([0.10, 0.25, 0.74, 0.205])
for ax in (ax1, ax2):
    base_axis(ax)
    windows(ax)
    ax.set_xlabel('$x$ (m)', labelpad=2)
im = ax1.imshow(field, origin='lower', extent=extent, cmap='Greys', vmin=0, vmax=15,
                interpolation='nearest', aspect='auto', rasterized=True)
ax2.imshow(masks[2], origin='lower', extent=extent, cmap=cmap, vmin=0, vmax=1,
           interpolation='nearest', aspect='auto', rasterized=True)
ax1.text(0, 1.30, '(a) Gaussian CLWC Cloud Map', transform=ax1.transAxes, fontsize=8, fontweight='bold')
ax2.text(0, 1.49, '(b) Binary Cloud Blockage Map', transform=ax2.transAxes, fontsize=8, fontweight='bold')
ax1.annotate('Relative cloud-map shift', xy=(0.98, 1.30), xytext=(0.64, 1.30),
             xycoords='axes fraction', textcoords='axes fraction', ha='right', va='center',
             fontsize=6.5, arrowprops=dict(arrowstyle='->', lw=0.7, color='black'))
cax = fig.add_axes([0.87, 0.64, 0.013, 0.205])
cb = fig.colorbar(im, cax=cax, ticks=[0, 3, 6, 9, 12, 15])
cb.set_label('CLWC (mg/m³)', fontsize=7, labelpad=3)
cb.ax.tick_params(labelsize=6, length=2)
ax2.legend(handles=[Patch(facecolor='#202020', label='Cloud blockage'),
                    Patch(facecolor='white', edgecolor='0.4', label='Non-blocking region')],
           loc='upper left', bbox_to_anchor=(1.015, 1.04), frameon=False,
           fontsize=6.2, handlelength=1, borderaxespad=0)
fig.text(0.10, 0.07, 'Each window: 2 km × 2 km; 50 × 50 cells; 40 m × 40 m per cell.', fontsize=7)
save(fig, 'figure_a_cloud_model')

fig = plt.figure(figsize=(7.2, 2.9))
fig.suptitle('CLWC Threshold Sensitivity', fontsize=9, y=0.98)
for i, (threshold, mask) in enumerate(zip(THRESHOLDS, masks)):
    ax = fig.add_axes([0.09 + (i % 3)*0.30, 0.65 - (i // 3)*0.38, 0.25, 0.078])
    base_axis(ax)
    ax.imshow(mask, origin='lower', extent=extent, cmap=cmap, vmin=0, vmax=1,
              interpolation='nearest', aspect='auto', rasterized=True)
    ax.add_patch(Rectangle((STARTS[0], 0), 2000, 2000, fill=False, ec='#c51e28', lw=0.9, clip_on=False))
    ax.text(0, 1.12, rf'$L_{{\mathrm{{th}}}}={threshold}$ mg/m³  (blocked: {mask.mean()*100:.1f}%)',
            transform=ax.transAxes, fontsize=7, va='bottom')
    ax.set_xticks([0, 8000, 16000])
    ax.set_yticks([0, 2000])
    ax.tick_params(labelsize=5.5)
    ax.set_xlabel('$x$ (m)', labelpad=2)
save(fig, 'cloud_threshold_sensitivity')
print('Field:', field.shape, 'range:', f'{field.min():.4f} to {field.max():.4f}', 'mg/m³')
print('Blocked fractions:', ', '.join(f'{t}: {100*m.mean():.2f}%' for t, m in zip(THRESHOLDS, masks)))
print('Windows:', STARTS.tolist(), 'm; local shape:', local.shape, '; 300 s window uses bilinear interpolation')
print('All shape, threshold, nesting, shift, and aligned-window assertions passed.')



