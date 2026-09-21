import io
import time
import wave

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

try:
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    import altair as alt
    HAS_ALTAIR = True
except ImportError:
    HAS_ALTAIR = False

try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="StreamTunes",
    page_icon="📻",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "StreamTunes — a Streamlit feature demo, FM tuner edition."},
)

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------
COL_BG = "#1B1620"
COL_PANEL = "#241D2B"
COL_AMBER = "#E8A33D"
COL_TEAL = "#4A9B95"
COL_RUST = "#B5473F"
COL_SLATE = "#6E7B8B"
COL_PLUM = "#8B7BA8"
COL_GOLD = "#C9A66B"
COL_CREAM = "#F2E9DC"
COL_MUTED = "#8A8094"
COL_HAIRLINE = "#3A3140"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600&display=swap');

    .stApp { background-color: #1B1620; color: #F2E9DC; font-family: 'Inter', sans-serif; }

    [data-testid="stSidebar"] { background-color: #14101A; border-right: 1px solid #3A3140; }
    [data-testid="stSidebar"] * { font-family: 'Inter', sans-serif; }

    h1, h2, h3 { font-family: 'Fraunces', serif !important; letter-spacing: -0.01em; }

    code { font-family: 'IBM Plex Mono', monospace !important; color: #E8A33D; background: transparent !important; }

    hr { border: none; border-top: 1px solid #3A3140; }

    .stButton>button {
        background-color: #241D2B; color: #F2E9DC; border: 1px solid #3A3140;
        border-radius: 4px; font-family: 'Inter', sans-serif;
    }
    .stButton>button:hover { border-color: #E8A33D; color: #E8A33D; }

    [data-testid="stMetric"] {
        background-color: #241D2B; border: 1px solid #3A3140; border-radius: 6px; padding: 12px 16px;
    }
    [data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace; color: #E8A33D; }

    [data-testid="stExpander"], [data-testid="stForm"], [data-testid="stDataFrame"] {
        border: 1px solid #3A3140 !important; border-radius: 6px !important; background-color: #241D2B;
    }

    .stTabs [data-baseweb="tab"] { font-family: 'IBM Plex Mono', monospace; color: #8A8094; }
    .stTabs [aria-selected="true"] { color: #E8A33D !important; }

    div[role="radiogroup"] label { padding: 4px 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


def page_header(freq, title, subtitle=None):
    sub_html = f"<p style='color:#8A8094;margin-top:0;'>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"""
        <span style="font-family:'IBM Plex Mono',monospace;color:#4A9B95;font-size:13px;letter-spacing:0.08em;">FM {freq}</span>
        <h1 style="margin-top:2px;margin-bottom:2px;">{title}</h1>
        {sub_html}
        <hr style="margin:8px 0 20px 0;">
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Audio + artwork generators (no external files)
# ---------------------------------------------------------------------------
def generate_tone_bytes(frequency=440, duration=3, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave_data = 0.5 * np.sin(2 * np.pi * frequency * t)
    audio = (wave_data * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio.tobytes())
    buf.seek(0)
    return buf.read()


def generate_vinyl_art(label_text, accent_hex, size=300):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cy = size // 2
    r_disc = int(size * 0.47)

    draw.ellipse([cx - r_disc, cy - r_disc, cx + r_disc, cy + r_disc], fill="#111014")
    for i in range(6):
        r = int(r_disc * (0.55 + i * 0.07))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline="#2A2830", width=1)

    r_label = int(size * 0.19)
    draw.ellipse([cx - r_label, cy - r_label, cx + r_label, cy + r_label], fill=accent_hex)
    r_hole = int(size * 0.02)
    draw.ellipse([cx - r_hole, cy - r_hole, cx + r_hole, cy + r_hole], fill="#111014")

    font = ImageFont.load_default()
    initials = "".join(w[0] for w in label_text.split()[:2]).upper()
    bbox = draw.textbbox((0, 0), initials, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - tw / 2, cy - th / 2 - 2), initials, fill="#14101A", font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def render_vu_meter(percent, segments=28):
    lit = int(segments * percent / 100)
    bars = []
    for i in range(segments):
        if i < lit:
            frac = i / segments
            color = COL_TEAL if frac < 0.6 else (COL_AMBER if frac < 0.85 else COL_RUST)
        else:
            color = "#2A2830"
        h = 16 + (i % 3) * 5
        bars.append(f'<div style="flex:1;height:{h}px;background:{color};border-radius:1px;"></div>')
    return f"""
    <div style="display:flex;align-items:flex-end;gap:3px;height:34px;padding:4px 0;">
        {''.join(bars)}
    </div>
    <div style="font-family:'IBM Plex Mono',monospace;color:#8A8094;font-size:11px;letter-spacing:0.05em;margin-top:2px;">
        {percent}% · VU
    </div>
    """


# ---------------------------------------------------------------------------
# Track data — mix of fictional catalog + real July 2026 chart tracks
# (title / artist metadata only, no lyrics)
# ---------------------------------------------------------------------------
SONGS = [
    {"title": "Neon Nights", "artist": "The Waveforms", "album": "Electric Dreams", "genre": "Electronic", "duration": 210, "plays": 15234, "color": COL_TEAL, "freq": 440},
    {"title": "Midnight Drive", "artist": "Aria Shore", "album": "Coastline", "genre": "Pop", "duration": 185, "plays": 9821, "color": COL_AMBER, "freq": 349},
    {"title": "Blue Room", "artist": "Sam Ellery", "album": "Slow Hours", "genre": "Jazz", "duration": 260, "plays": 4210, "color": COL_GOLD, "freq": 261},
    {"title": "Static Riot", "artist": "Voltage", "album": "Overdrive", "genre": "Rock", "duration": 195, "plays": 12043, "color": COL_SLATE, "freq": 392},
    {"title": "Paper Skies", "artist": "Aria Shore", "album": "Coastline", "genre": "Pop", "duration": 202, "plays": 7654, "color": COL_AMBER, "freq": 330},
    {"title": "Low Tide", "artist": "Sam Ellery", "album": "Slow Hours", "genre": "Jazz", "duration": 240, "plays": 3021, "color": COL_GOLD, "freq": 294},
    {"title": "Circuit Breaker", "artist": "The Waveforms", "album": "Electric Dreams", "genre": "Electronic", "duration": 220, "plays": 11890, "color": COL_TEAL, "freq": 466},
    {"title": "Gravel Road", "artist": "Voltage", "album": "Overdrive", "genre": "Rock", "duration": 178, "plays": 8890, "color": COL_SLATE, "freq": 415},
    # -- currently charting (Billboard Hot 100, July 2026) --
    {"title": "Choosin' Texas", "artist": "Ella Langley", "album": "Single", "genre": "Country", "duration": 195, "plays": 620000, "color": COL_RUST, "freq": 246},
    {"title": "Janice STFU", "artist": "Drake", "album": "Iceman", "genre": "Hip-Hop", "duration": 200, "plays": 540000, "color": COL_SLATE, "freq": 233},
    {"title": "Drop Dead", "artist": "Olivia Rodrigo", "album": "Single", "genre": "Pop", "duration": 180, "plays": 480000, "color": COL_AMBER, "freq": 370},
    {"title": "I Just Might", "artist": "Bruno Mars", "album": "Single", "genre": "Pop", "duration": 190, "plays": 510000, "color": COL_AMBER, "freq": 311},
    {"title": "Man I Need", "artist": "Olivia Dean", "album": "Single", "genre": "Soul", "duration": 205, "plays": 300000, "color": COL_GOLD, "freq": 277},
    {"title": "Opalite", "artist": "Taylor Swift", "album": "The Life of a Showgirl", "genre": "Pop", "duration": 215, "plays": 700000, "color": COL_AMBER, "freq": 392},
    {"title": "Swim", "artist": "BTS", "album": "Single", "genre": "K-Pop", "duration": 198, "plays": 460000, "color": COL_TEAL, "freq": 349},
    {"title": "Dracula", "artist": "Tame Impala and Jennie", "album": "Single", "genre": "Alt Rock", "duration": 208, "plays": 250000, "color": COL_PLUM, "freq": 220},
    {"title": "Back to Friends", "artist": "Sombr", "album": "Single", "genre": "Indie Pop", "duration": 190, "plays": 320000, "color": COL_TEAL, "freq": 262},
    {"title": "Folded", "artist": "Kehlani", "album": "Single", "genre": "R&B", "duration": 212, "plays": 280000, "color": COL_GOLD, "freq": 233},
]

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
st.session_state.setdefault("liked", set())
st.session_state.setdefault("playlists", {"Chill Vibes": {"color": COL_TEAL, "songs": []}, "Workout": {"color": COL_RUST, "songs": []}})
st.session_state.setdefault("recently_played", [])
st.session_state.setdefault("current_track", SONGS[0]["title"])
st.session_state.setdefault("volume", 70)
st.session_state.setdefault("play_count", {s["title"]: 0 for s in SONGS})


@st.dialog("Queue")
def show_queue():
    st.write("### Recently Played")
    if st.session_state.recently_played:
        for t in reversed(st.session_state.recently_played[-10:]):
            st.write(f"- {t}")
    else:
        st.write("No tracks played yet.")
    if st.button("Close"):
        st.rerun()


# ---------------------------------------------------------------------------
# Sidebar — FM dial navigation
# ---------------------------------------------------------------------------
NAV_ITEMS = [
    ("88.5", "🏠", "Home"),
    ("91.3", "🔍", "Search"),
    ("94.7", "🎵", "Player"),
    ("97.1", "📚", "Library"),
    ("100.5", "📊", "Charts"),
    ("103.9", "💬", "Assistant"),
    ("107.3", "⚙️", "Settings"),
    ("109.9", "🧩", "Playground"),
]
label_to_page, labels = {}, []
for freq, icon, name in NAV_ITEMS:
    label = f"`{freq}`  {icon}  {name}"
    labels.append(label)
    label_to_page[label] = name

st.sidebar.markdown("### 📻 StreamTunes")
st.sidebar.caption("Tune in to a channel")
selected_label = st.sidebar.radio("Navigate", labels, label_visibility="collapsed")
page = label_to_page[selected_label]

st.sidebar.markdown(
    f"""
    <div style="margin-top:16px;padding:10px 12px;background:{COL_PANEL};border:1px solid {COL_HAIRLINE};border-radius:6px;">
        <div style="font-family:'IBM Plex Mono',monospace;color:{COL_RUST};font-size:11px;letter-spacing:0.1em;">● ON AIR</div>
        <div style="font-family:'Fraunces',serif;font-size:15px;margin-top:2px;">{st.session_state.current_track}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------
if page == "Home":
    page_header("88.5", "StreamTunes", "Your dial, your tracks.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Songs", len(SONGS))
    m2.metric("Playlists", len(st.session_state.playlists))
    m3.metric("Liked", len(st.session_state.liked))
    m4.metric("Played", len(st.session_state.recently_played))

    st.subheader("🔥 Trending Now")
    cols = st.columns(4)
    for i, song in enumerate(SONGS[8:12]):
        with cols[i]:
            st.image(generate_vinyl_art(song["title"], song["color"]), use_container_width=True)
            st.write(f"**{song['title']}**")
            st.caption(song["artist"])
            if st.button("▶ Play", key=f"home_play_{song['title']}"):
                st.session_state.current_track = song["title"]
                st.toast(f"Now playing {song['title']}", icon="🎵")

    with st.expander("✨ What's new"):
        st.markdown("- 10 new tracks added to the catalog\n- FM-dial navigation\n- VU-meter playback view")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎉 Celebrate"):
            st.balloons()
    with c2:
        if st.button("❄️ Chill out"):
            st.snow()

# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------
elif page == "Search":
    page_header("91.3", "Search")
    query = st.text_input("Search songs or artists")

    col1, col2, col3 = st.columns(3)
    with col1:
        genre_filter = st.multiselect("Genre", sorted(set(s["genre"] for s in SONGS)))
    with col2:
        duration_range = st.slider("Duration (seconds)", 60, 400, (60, 400))
    with col3:
        sort_by = st.selectbox("Sort by", ["Title", "Artist", "Plays"])

    results = [
        s for s in SONGS
        if (query.lower() in s["title"].lower() or query.lower() in s["artist"].lower() or query == "")
        and (not genre_filter or s["genre"] in genre_filter)
        and (duration_range[0] <= s["duration"] <= duration_range[1])
    ]
    sort_key = {"Title": "title", "Artist": "artist", "Plays": "plays"}[sort_by]
    results = sorted(results, key=lambda s: s[sort_key], reverse=(sort_by == "Plays"))

    if results:
        df = pd.DataFrame([{k: s[k] for k in ("title", "artist", "album", "genre", "duration", "plays")} for s in results])
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download results as CSV", csv, "search_results.csv", "text/csv")
    else:
        st.info("No songs match your filters.")

# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------
elif page == "Player":
    page_header("94.7", "Now Playing")
    current = next(s for s in SONGS if s["title"] == st.session_state.current_track)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(generate_vinyl_art(current["title"], current["color"]), use_container_width=True)
    with col2:
        st.subheader(current["title"])
        st.write(f"**{current['artist']}** — {current['album']}")
        st.caption(f"Genre: {current['genre']} · {current['duration']}s")

        liked = current["title"] in st.session_state.liked
        if st.toggle("❤️ Liked", value=liked, key="like_toggle"):
            st.session_state.liked.add(current["title"])
        else:
            st.session_state.liked.discard(current["title"])

        st.audio(generate_tone_bytes(current["freq"]), format="audio/wav")

        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("⏮ Previous"):
                idx = SONGS.index(current)
                st.session_state.current_track = SONGS[idx - 1]["title"]
                st.rerun()
        with b2:
            play_clicked = st.button("▶️ Play")
        with b3:
            if st.button("⏭ Next"):
                idx = SONGS.index(current)
                st.session_state.current_track = SONGS[(idx + 1) % len(SONGS)]["title"]
                st.rerun()

        if play_clicked:
            st.session_state.recently_played.append(current["title"])
            st.session_state.play_count[current["title"]] += 1
            vu_placeholder = st.empty()
            for pct in range(0, 101, 4):
                vu_placeholder.markdown(render_vu_meter(pct), unsafe_allow_html=True)
                time.sleep(0.03)
            st.toast("Playback finished!", icon="✅")

        with st.popover("🔊 Volume & Options"):
            st.session_state.volume = st.slider("Volume", 0, 100, st.session_state.volume)
            st.checkbox("Shuffle", key="shuffle")
            st.checkbox("Repeat", key="repeat")

        if st.button("📜 View Queue"):
            show_queue()

        if st.button("🔄 Buffer track"):
            with st.status("Buffering track...", expanded=True) as status:
                st.write("Connecting to server...")
                time.sleep(0.4)
                st.write("Fetching audio stream...")
                time.sleep(0.4)
                st.write("Ready to play")
                status.update(label="Buffering complete", state="complete", expanded=False)

# ---------------------------------------------------------------------------
# Library
# ---------------------------------------------------------------------------
elif page == "Library":
    page_header("97.1", "Your Library")
    tab1, tab2, tab3, tab4 = st.tabs(["Playlists", "Liked Songs", "Recently Played", "Upload"])

    with tab1:
        with st.form("new_playlist_form", clear_on_submit=True):
            st.subheader("Create a new playlist")
            pl_name = st.text_input("Playlist name")
            pl_color = st.color_picker("Cover color", COL_AMBER)
            pl_songs = st.multiselect("Add songs", [s["title"] for s in SONGS])
            submitted = st.form_submit_button("Create playlist")
            if submitted and pl_name:
                st.session_state.playlists[pl_name] = {"color": pl_color, "songs": pl_songs}
                st.success(f"Playlist '{pl_name}' created!")

        for name, data in st.session_state.playlists.items():
            with st.expander(f"🎼 {name} ({len(data.get('songs', []))} songs)"):
                if data.get("songs"):
                    st.data_editor(
                        pd.DataFrame({"track": data["songs"]}),
                        num_rows="dynamic",
                        use_container_width=True,
                        key=f"editor_{name}",
                    )
                else:
                    st.caption("No songs yet.")

    with tab2:
        liked_songs = [s for s in SONGS if s["title"] in st.session_state.liked]
        if liked_songs:
            st.dataframe(pd.DataFrame(liked_songs), use_container_width=True, hide_index=True)
        else:
            st.info("You haven't liked any songs yet. Like songs from the Player page!")

    with tab3:
        if st.session_state.recently_played:
            st.table(pd.DataFrame({"Recently played": list(reversed(st.session_state.recently_played[-10:]))}))
        else:
            st.info("Nothing played yet.")

    with tab4:
        uploaded = st.file_uploader("Upload your own track", type=["mp3", "wav", "ogg"])
        if uploaded is not None:
            st.audio(uploaded)
            st.success(f"Uploaded {uploaded.name}")

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
elif page == "Charts":
    page_header("100.5", "Streaming Analytics")

    dates = pd.date_range(end=pd.Timestamp.today(), periods=30)
    plays_df = pd.DataFrame({"plays": np.random.randint(50, 500, size=30).cumsum()}, index=dates)
    st.line_chart(plays_df, color=[COL_AMBER])

    genre_plays = pd.DataFrame({"genre": sorted(set(s["genre"] for s in SONGS))})
    genre_plays["plays"] = np.random.randint(100, 1000, size=len(genre_plays))
    st.bar_chart(genre_plays.set_index("genre"), color=[COL_TEAL])
    st.area_chart(plays_df, color=[COL_AMBER])

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Plays", f"{int(plays_df['plays'].iloc[-1]):,}", delta="+12%")
    c2.metric("Active Listeners", "1.2M", delta="-3%")
    c3.metric("Avg. Session", "24 min", delta="+2 min")

    if HAS_MPL:
        st.subheader("Matplotlib chart")
        fig, ax = plt.subplots()
        fig.patch.set_facecolor(COL_BG)
        ax.set_facecolor(COL_PANEL)
        ax.plot(plays_df.index, plays_df["plays"], color=COL_AMBER)
        ax.tick_params(colors=COL_MUTED)
        for spine in ax.spines.values():
            spine.set_color(COL_HAIRLINE)
        ax.set_title("Plays over time", color=COL_CREAM)
        st.pyplot(fig)

    if HAS_ALTAIR:
        st.subheader("Altair chart")
        chart = alt.Chart(genre_plays).mark_bar(color=COL_TEAL).encode(x="genre", y="plays")
        st.altair_chart(chart, use_container_width=True)

    if HAS_PLOTLY:
        st.subheader("Plotly chart")
        fig2 = px.pie(
            genre_plays, names="genre", values="plays", title="Plays by Genre",
            color_discrete_sequence=[COL_TEAL, COL_AMBER, COL_RUST, COL_SLATE, COL_PLUM, COL_GOLD],
        )
        fig2.update_layout(paper_bgcolor=COL_BG, font_color=COL_CREAM)
        st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Raw analytics JSON"):
        st.json({"total_plays": int(plays_df["plays"].iloc[-1]), "genres": genre_plays.to_dict(orient="records")})

# ---------------------------------------------------------------------------
# Assistant
# ---------------------------------------------------------------------------
elif page == "Assistant":
    page_header("103.9", "Music Assistant", "Rule-based demo · st.chat_message / st.chat_input")

    st.session_state.setdefault("messages", [])
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    prompt = st.chat_input("Ask about a song or artist...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        match = next((s for s in SONGS if s["title"].lower() in prompt.lower() or s["artist"].lower() in prompt.lower()), None)
        reply = (
            f"'{match['title']}' by {match['artist']} is a {match['genre']} track."
            if match else
            "I don't have info on that yet — try asking about a song in the Library!"
        )
        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.write(reply)

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
elif page == "Settings":
    page_header("107.3", "Settings")

    st.toggle("Dark mode (visual only)", key="dark_mode")
    st.checkbox("Allow explicit content", key="explicit")
    st.radio("Audio quality", ["Low", "Normal", "High", "Very High"], key="quality")
    st.select_slider("Crossfade duration (s)", options=list(range(0, 13)), key="crossfade")
    st.time_input("Daily mix notification time")
    st.date_input("Wrapped reveal date")
    st.color_picker("Accent color", COL_AMBER, key="accent")

    photo = st.camera_input("Take a profile photo (optional)")
    if photo:
        st.image(photo)

    st.link_button("Visit Streamlit Docs", "https://docs.streamlit.io")

    try:
        st.feedback("thumbs")
    except Exception:
        st.caption("(st.feedback needs a newer Streamlit version)")

    st.subheader("Query params")
    st.write(dict(st.query_params))
    if st.button("Set demo query param"):
        st.query_params["demo"] = "true"

    with st.expander("🔍 Debug: session state"):
        st.json({k: (list(v) if isinstance(v, set) else v) for k, v in st.session_state.items()})

# ---------------------------------------------------------------------------
# Playground
# ---------------------------------------------------------------------------
elif page == "Playground":
    page_header("109.9", "Widgets Playground")

    st.subheader("Text elements")
    st.write("st.write can render:", "strings,", 123, [1, 2, 3], {"a": 1})
    st.markdown("**Bold**, *italic*, and [a link](https://streamlit.io)")
    st.code("def play(song):\n    print(f'Playing {song}')", language="python")
    st.latex(r"E = mc^2")
    st.divider()

    st.subheader("Status messages")
    st.info("This is an info message.")
    st.success("This is a success message.")
    st.warning("This is a warning message.")
    st.error("This is an error message.")

    if st.button("Trigger sample exception"):
        try:
            1 / 0
        except Exception as e:
            st.exception(e)

    st.subheader("Placeholders")
    placeholder = st.empty()
    if st.button("Update placeholder"):
        placeholder.write("✅ Placeholder updated!")
    else:
        placeholder.write("Placeholder waiting for update...")

    st.subheader("Fun stuff")
    fc1, fc2 = st.columns(2)
    with fc1:
        if st.button("🎈 Balloons", key="playground_balloons"):
            st.balloons()
    with fc2:
        if st.button("❄️ Snow", key="playground_snow"):
            st.snow()