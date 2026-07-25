# Software and Asset Licence Record

This project contains original Python source code written for the prototype. Add
the project team's chosen source-code licence before external distribution.

| Dependency or asset | Role | Licence / source note |
|---|---|---|
| Python | Runtime | Python Software Foundation License |
| MoviePy | Primary renderer | MIT License; verify the installed release metadata |
| FFmpeg / FFprobe | Fallback renderer and probe | LGPL/GPL configuration-dependent; record the exact build used |
| NumPy | MoviePy array processing | BSD-3-Clause |
| Pillow | Locally generated text images | HPND License |
| pytest | Test runner | MIT License |
| DejaVu Sans, when available | Text rendering | Bitstream Vera / DejaVu font licence |
| Input video footage | Source material | Must be original, simulated, or covered by explicit permission |
| Music | Not included | Do not add without recording source and licence |

FFmpeg licence obligations depend on build flags and linked codecs. Before
submission or distribution, save `ffmpeg -version`, identify whether the selected
build is GPL-enabled, and comply with that build's licence terms.

