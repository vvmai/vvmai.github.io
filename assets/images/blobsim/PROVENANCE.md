# blobsim asset provenance

These images are **build artifacts of the `blobsim` package**, not hand-made
figures. Source: <https://github.com/vvmai/gol> (local checkout:
`/Users/vmai/Repos/scratch/gol`). Regenerate from there, then sync the outputs
into this directory and commit them — the `.gitignore` `!assets/**` rule lets the
PNGs through the blanket `*.png` ignore so they deploy to GitHub Pages.

The website only *embeds* these files (`![](/assets/images/blobsim/…)`); all
simulation and plotting lives in the package. To add a chart: write its
generator in the gol `benchmark/` or `scenarios/` layer, run it, copy the output
here under the name the page references, and commit.

## Where each asset comes from

| Asset(s) | gol generator |
| --- | --- |
| `sc1_decay_extinction.gif`, `sc4_boom_bust.gif`, `sc5_sparse.gif`, `sc5_dense.gif`, `c2_extinction.gif`, `c2_survival.gif`, `c3_competition.gif` | `benchmark/generate_gifs.py` (`blobsim.rendering.render_gif`) |
| `cyclic_ouroboros.gif`, `cyclic_collapse.gif`, `cyclic_orbit.gif`, `cyclic_frames.png`, `cyclic_populations.png` | `scenarios/cyclic_ouroboros.py`, `scenarios/spatial_ouroboros.py` (3-species omnivore predation) |
| `cyclic_finite_size.png` | grid-size coexistence sweep over the cyclic config (`scenarios/`) |
| `bench_lifespan.png`, `bench_extinction.png`, `bench_extinction_time.png`, `bench_carrying.png`, `bench_carrying_time.png`, `bench_lone_energy.png`, `bench_threshold.png` | `benchmark/` scenarios (`b2a_single_lifespan`, `sc1`/`sc4`, `sc5_carrying_capacity`, `sc6_energy_equilibrium`, `c2_extinction_boundary`) + plotting |
| `thronglets.jpg` | header image (not generated) |

## Regenerate

```bash
cd /Users/vmai/Repos/scratch/gol
.venv/bin/python -m benchmark.generate_gifs        # the *.gif assets
.venv/bin/python -m scenarios.cyclic_ouroboros     # cyclic_* charts/gif
# …then copy benchmark/gifs/* and scenarios/figs/* here under the page's names.
```
