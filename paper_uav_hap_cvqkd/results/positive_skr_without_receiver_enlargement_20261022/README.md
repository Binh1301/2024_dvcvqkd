# Positive-rate investigation with the receiver fixed at 8 cm

Start with `report_vi.md`, `executive_conclusion_vi.md` and `selection.json`.
Tables1-4 contain sensitivity, positive selected points, modifications and
the full rate decomposition. Eight single-plot vectorPDF/350dpiPNG figures
are in `figures/`.

Read-only verification from the project directory:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B results/positive_skr_without_receiver_enlargement_20261022/verify.py
```

The verifier hashes saved files and checks table consistency; it never imports
the evaluator or reruns a search. Its one-time `--seal` mode creates the receipt.

`numeric.py` extends only geometry/detector parameters of the previous passive
circular-Gaussian optical/full-Z homodyne diagnostic. `search.py` produces the
historical regression, StageA and StageB; `probe_detector.py` records a targeted
probe; `finish_search.py` performs detector/source/threshold/robustness work;
`extend_geometry.py` adds fixed-source geometry/noise boundaries and explicitly
uncalibrated height comparisons and updates A to the final same-channel source
winner, preserving `selection_phase2.json`. `necessity.py` tests reversions and
an additional original-geometry point with a very small positive margin.
`checks.py` validates the scoped numerical
evidence; `report.py` renders saved results. Completed numerical stages refuse
overwrite. Do not rerun them for stored-result questions.

The weather pairs23/.92,15/.89,5/.75 come from the user's reply. Visibility is a
label; no second Kruse factor is multiplied. No vertical extinction profile
was provided. Height-changed points are labeled sensitivities and excluded
from the recommended original-height shortlist.

Detector remains UNTRUSTED, receiver is always0.08m. No aperture sweep, source
moment generation/AP, production baseline/threshold approval, training,
final-test/held-out access or publication promotion. Positive functionals are
numerical candidates, not hardware- or security-validated operating rates.
