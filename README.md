# brainvomit

Streamlit app served static on GitHub Pages via [stlite](https://github.com/whitphx/stlite) (Pyodide/WASM, runs in browser, no server).

- `index.html` — stlite mount; lists app files + pip deps (pandas/numpy/scipy/matplotlib/shapely).
- `app.py`, `About.py`, `pages/`, `utils.py` — unmodified Streamlit, runs in browser.
- `assets/maps/` — pre-rendered NYC outputs (Plotly HTML + network PNG + ranking CSV).
- `prerender/` — offline generator for `assets/maps/` (heavy geo deps; NOT deployed). `data/` = its inputs.
- `.github/workflows/deploy.yml` — push to `main` → assemble static site → Pages.

## Gotchas

- Pages source must = **GitHub Actions** (Settings → Pages).
- Prerender resets `pio.templates.default="plotly"` — streamlit import flips it to a dark template (= black maps). Mirrors live `st.plotly_chart(theme=None)`.
- Regenerate maps: `.venv/bin/python prerender/prerender_nyc.py`
- Local dev: `python3 -m http.server` (needs HTTP, not file://).
