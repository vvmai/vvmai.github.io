# brainvomit

A personal website. The pages are written in Markdown, turned into static HTML by
[Quarto](https://quarto.org), and served by GitHub Pages at
<https://vvmai.github.io>. There is no backend: everything the visitor needs is a
plain file, so pages load instantly and there is nothing to run server-side.

## Contents

- [How a page works](#how-a-page-works)
- [Files](#files)
- [Edit and preview locally](#edit-and-preview-locally)
- [The NYC page (Python + freeze)](#the-nyc-page-python--freeze)
- [Deployment](#deployment)

## How a page works

Each page is a `.qmd` file (Quarto Markdown: Markdown plus optional code cells).
`quarto render` converts every `.qmd` into an HTML page under `_site/`. Three
kinds of page appear here:

- **Static** (e.g. `index.qmd`) — prose and images only.
- **Interactive** (`slim-jim.qmd`, `grad-school.qmd`, `puppy.qmd`) — use **OJS**
  (Observable JavaScript), Quarto's built-in reactive JS. Inputs and charts run in
  the visitor's browser; no Python or server is involved. The puppy page fits a
  sigmoid to editable data using a Levenberg–Marquardt routine written inline in
  JS, so it has no external library dependency.
- **Python** (`nyc.qmd`) — see [below](#the-nyc-page-python--freeze).

## Files

| Path | Purpose | Tracked? |
| ---- | ------- | -------- |
| `*.qmd` | the pages | yes |
| `_quarto.yml` | site config: title, sidebar/nav, theme (`brite`) | yes |
| `_freeze/` | cached outputs of `nyc.qmd`'s Python cells | yes (required — see below) |
| `photos/` | images | yes |
| `.github/workflows/deploy.yml` | build + deploy on push to `main` | yes |
| `analysis/` | NYC analysis helpers; used only to refresh `_freeze/` | no (gitignored, local-only) |
| `data/` | raw NYC datasets, ~44 MB; inputs to the analysis only | no (gitignored, local-only) |

## Edit and preview locally

```bash
export PATH="$HOME/.local/quarto-1.9.38/bin:$PATH"   # adjust to your Quarto path
quarto preview                                        # serves with live reload
```

Saving a `.qmd` re-renders it automatically. To add a page: create `foo.qmd` and
add one entry under `website.sidebar.contents` in `_quarto.yml`.

## The NYC page (Python + freeze)

`nyc.qmd` runs a geospatial analysis (geopandas, networkx, contextily, h3) whose
dependencies and ~44 MB of data are too heavy to install in CI. Quarto's **freeze**
feature solves this: it runs the Python cells once locally and stores the rendered
outputs in `_freeze/`. Because `_freeze/` is committed, the GitHub Actions build
reuses those cached outputs and never executes Python — so CI needs neither
geopandas nor `data/`. This is why `_freeze/` must stay tracked; gitignoring it
would force CI to re-run the analysis and fail.

To refresh the page after changing the analysis (needs the local `.venv`, the
`data/` directory, and the one-time kernel registration below):

```bash
python -m ipykernel install --user --name brainvomit   # one time
quarto render nyc.qmd                                   # regenerates _freeze/
git add _freeze && git commit                           # commit the new cache
```

## Deployment

Pushing to `main` triggers `.github/workflows/deploy.yml`, which runs
`quarto render` and publishes `_site/` to GitHub Pages. Two one-time settings:

- **Settings → Pages → Source = GitHub Actions.**
- The repository must be **public** (GitHub Pages on the free plan does not serve
  private repos).
