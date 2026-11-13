# QKD-aware binary cloud availability

The independent workflow is delivered in `results/ibrahim_binary_qkd_20261112/`.
Read its `report_vi.md` and `README.md` for equations, precise populations,
threshold scope, data keys, reproduction and read-only verification commands.

The official 0.55 m threshold is pending. The current native SKR/Holevo import
fails Windows Application Control; no 0.55 m numerical SKR evaluation or root
was executed. The separately named diagnostic uses an illustrative 0.1 dB
threshold and assumes all reference columns are clear-sky feasible. It is not
an official threshold or a physically calibrated secure-availability result.

`src/ibrahim_binary_qkd.py` contains the deterministic classifier, conditional
statistics and optional binary T/R approximation interface. Arrays retain
`[t,y,x]`. Blockage is 0=available, 1=unavailable, 255=unresolved. The Boolean
`qkd_available` is False at unknown cells; always preserve `resolved_mask`,
`classification_status`, scope and the tri-state clear-sky map.

For known clear-sky-unavailable cells, blockage is 1 even at zero added loss.
For clear-feasible cells, a positive finite threshold and finite nonnegative
attenuation are required; equality is unavailable. Unknowns are never available.
The classifier accepts maps as well as scalars, but does not itself certify
the scientific origin of a supplied threshold.

The 1000 source Gaussian, CLWC, attenuation and physical transmittance arrays
are read without regeneration or alteration. The source attenuation maps are
vertical-reference cloud columns; their coordinates are not silently identified
with ray-traced UAV coordinates. No trajectory algorithm or QKD source is edited.

Do not replace physical transmittance by the binary state. The optional binary
channel/rate interface requires resolved classification and explicit clear-sky
inputs; no such inputs are invented or exported here. Operational integration
requires validated thresholds/clear maps, geometry and secure-model evidence.
