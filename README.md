# brainvomit

Personal site built with [Quarto](https://quarto.org) → static HTML on GitHub Pages
(`https://vvmai.github.io`). No server, no runtime download.

- `*.qmd` — pages (Markdown). Sidebar/nav/theme in `_quarto.yml` (default `cosmo`).
- Interactive pages (slim-jim, grad-school, puppy) use **OJS** (client-side, reactive). Puppy's sigmoid fit is a self-contained JS Levenberg–Marquardt — no CDN dep.
- `nyc.qmd` — heavy geo analysis as **Python cells**, kernel `brainvomit` (the `.venv`). Outputs cached in `_freeze/` (committed) so CI renders without geopandas or `data/`.
- `data_loaders.py`, `nyc_analysis.py` — NYC analysis helpers (used only at local render).
- `.github/workflows/deploy.yml` — push to `main` → `quarto render` → Pages.

## Dev loop

```bash
export PATH="$HOME/.local/quarto-1.9.38/bin:$PATH"   # wherever quarto lives
quarto preview          # live-reload; Python cells execute, plots inline
```

Editing a `.qmd` re-renders on save. New page = add `foo.qmd` + a line under `website.sidebar.contents` in `_quarto.yml`.

## Gotchas

- Pages source must = **GitHub Actions** (Settings → Pages). Repo must be public on the free plan.
- Re-render NYC after changing the analysis: `quarto render nyc.qmd` (needs `.venv` + local `data/`). Commit the updated `_freeze/`.
- Kernel registered once: `.venv/bin/python -m ipykernel install --user --name brainvomit`.
- `data/` is gitignored (44 MB raw inputs, local only); `_freeze/` is committed.
