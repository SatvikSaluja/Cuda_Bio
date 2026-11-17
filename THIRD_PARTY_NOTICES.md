# Third-party notices

WarpAlign's original source is MIT-licensed. No WFA2/WFA-GPU/GASAL2 implementation is vendored.

The native Python module uses pybind11 headers (BSD-style licence). The bundled Studio build includes React, React DOM and Scheduler (MIT). Their licence texts are included in `python/warpalign/licenses/` and distributed with the Python package. Build tools and independently installed optional services retain their own licences.

Minimap2 and WFA2 are external, separately installed tools. The original baseline adapter does not change their redistribution or attribution requirements. See docs/prior_art.md and preserve dependency notices when packaging external binaries. This notice does not grant rights to separately supplied sequencing datasets.
