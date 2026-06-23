# brainvomit

A personal Streamlit site that runs **entirely in the browser** via
[stlite](https://github.com/whitphx/stlite) (Streamlit → WebAssembly/Pyodide),
served as static files on **GitHub Pages**. No server.

## Contents
- [How it works](#how-it-works)
- [Layout](#layout)
- [Deploy](#deploy)
- [The NYC page (pre-rendered)](#the-nyc-page-pre-rendered)
- [Develop locally](#develop-locally)

## How it works
`index.html` mounts the Streamlit app with stlite, listing every file the app
needs in the in-browser filesystem. The app code (`app.py`, `pages/`) is
unmodified Streamlit; pip packages (`pandas`, `numpy`, `scipy`, `matplotlib`,
`shapely`) load from the Pyodide CDN at runtime.

## Layout
| Path | Role |
|------|------|
| `index.html` | stlite mount point — the only true entry file |
| `app.py`, `About.py`, `pages/`, `utils.py` | Streamlit app (runs in browser) |
| `assets/maps/` | Pre-rendered NYC outputs (Plotly HTML, network PNG, ranking CSV) |
| `photos/` | Images used by `st.image` |
| `.streamlit/config.toml` | Theme |
| `.github/workflows/deploy.yml` | CI: assemble static site → GitHub Pages |
| `prerender/` | Offline generator for the NYC assets (heavy geo deps, **not** deployed) |
| `data/` | Raw NYC datasets, input to the prerender step only (**not** deployed) |

## Deploy
Pushes to `main` trigger `.github/workflows/deploy.yml`, which copies the static
files (everything except `data/`, `prerender/`, `.venv/`) into `_site/`, adds a
`404.html` SPA fallback, and publishes to Pages.

One-time setup: **Settings → Pages → Build and deployment → Source = GitHub
Actions**.

> Note: a refreshed/bookmarked deep link (e.g. `/Slim_Jim_percentage`) loads the
> app at the home (About) page rather than restoring that exact page — stlite
> derives its base path from the URL. In-app navigation works normally.

## The NYC page (pre-rendered)
"Plotting my next move" relies on `geopandas`, `networkx`, `h3pandas`,
`contextily`, and `census` — impractical in the browser. The analysis is run
**once offline** and its maps embedded as static assets, so the live page needs
only `streamlit` + `pandas`.

Regenerate after changing the analysis:
```bash
.venv/bin/python prerender/prerender_nyc.py   # writes assets/maps/
```

## Develop locally
stlite needs files served over HTTP (not `file://`):
```bash
python3 -m http.server 8000
# open http://localhost:8000/
```
The heavy geo deps are only needed for `prerender/` — see
`prerender/requirements.txt`.
