# 📻 StreamTunes

A Spotify-style music app built entirely in **Streamlit** — a hands-on tour through nearly every widget, layout element, and chart type Streamlit offers, wrapped in a custom FM-tuner / vinyl-record visual identity instead of a default template look.

**🔗 Live demo:** [lamify.streamlit.app](https://lamify.streamlit.app/)

---

## About

This started as an exercise in covering Streamlit's full feature surface — widgets, layout, media, charts, forms, session state, chat, dialogs — inside a single `apps.py` file. Rather than a plain dashboard, it's themed as an FM radio / turntable: pages are "frequencies," album art is a generated vinyl record, and playback is shown on a custom VU meter instead of a default progress bar.

## Features by page

| Page | Frequency | What it demos |
|---|---|---|
| 🏠 Home | 88.5 | Dashboard metrics, a trending-tracks grid with generated vinyl artwork, an expander changelog, balloon/snow easter eggs |
| 🔍 Search | 91.3 | Text search, genre multiselect, duration range slider, sortable results table, CSV export |
| 🎵 Player | 94.7 | Now-playing vinyl art, a procedurally generated audio tone (no external audio files needed), like toggle, prev/next, an animated VU-meter for playback, a popover for volume/shuffle/repeat, a modal (`st.dialog`) queue viewer, a simulated buffering status |
| 📚 Library | 97.1 | Create playlists via a form, edit playlist tracklists with `st.data_editor`, view liked songs, recently played history, upload and play your own audio file |
| 📊 Charts | 100.5 | Line/bar/area charts, metrics with deltas, optional Matplotlib/Altair/Plotly charts (skipped automatically if a library isn't installed), a raw JSON view |
| 💬 Assistant | 103.9 | A small rule-based chatbot using `st.chat_message` / `st.chat_input` |
| ⚙️ Settings | 107.3 | Toggle, checkbox, radio, select_slider, time/date input, color picker, camera input, link button, feedback widget, query params, and a live session-state debug view |
| 🧩 Playground | 109.9 | `st.write`, `st.code`, `st.latex`, status messages, exception handling, empty placeholders, balloons/snow |

## Design notes

- **Palette:** deep plum background, amber + teal accents — chosen to avoid the generic "black background, neon green" AI-app look.
- **Type:** Fraunces (headings), IBM Plex Mono (data/frequencies), Inter (body text).
- **Signature elements:**
  - Album art is a vinyl record generated on the fly with Pillow (grooves, center label, initials) instead of a flat placeholder image.
  - Playback progress is a custom animated VU meter built from HTML/CSS, not the default `st.progress` bar.
  - Sidebar navigation uses real FM frequency numbers as labels instead of a plain menu.

## Track catalog

A mix of fictional artists (for demo variety) plus a set of real, currently-charting songs (Billboard Hot 100, July 2026) — title and artist only, no lyrics.

## Tech stack

Python · Streamlit · Pandas · NumPy · Pillow · (optional) Matplotlib, Altair, Plotly

## Project structure

```
Spotify-like-app-using-streamlit/
├── apps.py            # the entire app — single file
├── requirements.txt   # dependencies
└── README.md
```

## Running it locally

```bash
git clone https://github.com/lamlam25/Spotify-like-app-using-streamlit.git
cd Spotify-like-app-using-streamlit
pip install -r requirements.txt
streamlit run apps.py
```

## Deployment

Deployed on **Streamlit Community Cloud**, pointed at `apps.py` on the `main` branch of this repo. Live at [lamify.streamlit.app](https://lamify.streamlit.app/) — any push to `main` redeploys it automatically.

## Notes / limitations

- Audio is procedurally generated sine tones standing in for real track playback, not actual song audio.
- Play counts and streaming stats are randomized demo numbers, not real streaming data.
- `st.dialog`, `st.popover`, and `st.feedback` need a reasonably recent version of Streamlit (see `requirements.txt`).

## Author

Built by [Lamlam](https://github.com/lamlam25) as a project exploring Streamlit's feature set end to end.
