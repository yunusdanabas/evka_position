# Quick IPT — Technical Reports

Two LaTeX reports on the Quick IPT hidden-point tool, each in its own folder:

| Folder | Document | What it is |
|---|---|---|
| `overview/` | `main.tex` → `main.pdf` | Short overview (~4 pp): what IPT is, the two solver modes, quality flags, TikZ diagrams. |
| `detailed/` | `main.tex` → `main.pdf` | Deep companion (~11 pp): full derivations of the three estimators, the dilution-of-precision / conditioning analysis, the implementation walkthrough, and an original simulation study (figures + table). |

## Build

```bash
cd overview  && latexmk -pdf main.tex     # overview  -> overview/main.pdf
cd detailed  && latexmk -pdf main.tex     # detailed  -> detailed/main.pdf
```

Clean build artifacts with `latexmk -C` inside a folder.

## Simulation study (detailed report)

The accuracy numbers, results table, and pgfplots figures in `detailed/main.tex`
come from running the *actual* solver:

```bash
python docs/reports/ipt/detailed/sim_study.py
```

It sweeps `solve_ipt` over sweep half-angle, sensor noise, and point count, prints
booktabs rows + pgfplots coordinate blocks (baked into `detailed/main.tex`), and ends
with a self-check `assert`. Reproducible (fixed ground truth + seeds); needs `numpy` only.

## Dependencies

- LaTeX distribution (TeX Live, MiKTeX, or MacTeX).
- Packages: `amsmath`, `tikz`, `hyperref`, `booktabs`, `listings`, `xcolor`, `microtype`
  (both docs); `pgfplots`, `titlesec` (detailed only).
- `python` + `numpy` — only to regenerate the study via `sim_study.py`.

## Layout

```
docs/reports/ipt/
  README.md                 this index
  overview/
    main.tex  main.pdf
    references.bib           (kept for reference; not needed to compile)
  detailed/
    main.tex  main.pdf
    sim_study.py             regenerates the study numbers/figures
```
