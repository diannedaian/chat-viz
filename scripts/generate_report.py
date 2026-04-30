#!/usr/bin/env python3
"""
DEPRECATED LEGACY PIPELINE.

This script is preserved only as a reference after the project migrated to:
- apps/web/index.html
- apps/web/parser.html
- apps/web/viewer.html

The active workflow is now browser-based JSON import + parser export.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import jieba
import jieba.posseg as pseg
import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")

NAME_YIFAN = "Yifan"
NAME_DIANNE = "Dianne (戴安)"
TZ_DEFAULT = "Asia/Shanghai"
RESPONSE_CAP_S = 86400  # 24h: exclude longer gaps from response-time stats

# Minimal English stopwords (extend as needed)
EN_STOP = frozenset(
    """
    a an the and or but if in on at to for of as by with from up about into through
    during before after above below between under again further then once here there
    when where why how all both each few more most other some such no nor not only
    own same so than too very can will just don should now i me my we our you your
    he him his she her it its they them their what which who this that these those
    am is are was were be been being have has had having do does did doing would could
    should may might must shall will ve re ll d s t im ur u ve dont cant wont isnt
    """.split()
)

# Common Chinese function words / particles to de-emphasize in top words
ZH_STOP = frozenset(
    "的了是在和有不人也个这中大为上们来以说时要就出会可都而对能于子那下得与着过还"
    "所然其事里后自之么去好行很用家多如下地看天想没国年小吗嗯嘛哈哦噢喔呀哇呐呗"
)


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    default_json = root / "私聊_Yifan Kang '28.json"
    p = argparse.ArgumentParser(description="Generate chat analytics HTML report from WeFlow JSON.")
    p.add_argument(
        "--input",
        type=Path,
        default=default_json,
        help="Path to WeFlow export JSON",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=root / "report",
        help="Directory for report.html and figures/",
    )
    p.add_argument(
        "--timezone",
        default=TZ_DEFAULT,
        help="IANA timezone label for interpreting timestamps (default Asia/Shanghai)",
    )
    p.add_argument(
        "--response-cap-seconds",
        type=int,
        default=RESPONSE_CAP_S,
        help="Exclude reply gaps longer than this from response-time aggregates",
    )
    return p.parse_args()


def load_messages(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("messages") or []


def parse_local_dt(s: str | None) -> datetime | None:
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def message_dt(row: dict, tz: ZoneInfo) -> datetime | None:
    ft = parse_local_dt(row.get("formattedTime"))
    if ft is not None:
        return ft.replace(tzinfo=tz)
    ct = row.get("createTime")
    if ct is None:
        return None
    try:
        return datetime.fromtimestamp(int(ct), tz=tz)
    except (OSError, ValueError, TypeError):
        return None


def classify_script(text: str) -> str:
    """Return 'zh', 'en', or 'mixed' from character script balance."""
    if not text or not text.strip():
        return "mixed"
    cjk = sum(1 for c in text if "\u4e00" <= c <= "\u9fff" or "\u3400" <= c <= "\u4dbf")
    lat = sum(1 for c in text if ("a" <= c <= "z") or ("A" <= c <= "Z"))
    total = cjk + lat
    if total == 0:
        return "mixed"
    zh_share = cjk / total
    if zh_share >= 0.55:
        return "zh"
    if zh_share <= 0.45:
        return "en"
    return "mixed"


def strip_bracket_placeholders(s: str) -> str:
    return re.sub(r"\[[^\]]{0,80}\]", " ", s)


_CALL_DURATION_RE = re.compile(
    r"^\[(语音通话|视频通话)\]\s*(\d{1,4}):(\d{2})(?::(\d{2}))?\s*$"
)


def parse_call_duration_seconds(content: str | None) -> float | None:
    """Parse WeChat 通话消息 duration; two-part = MM:SS, three-part = H:MM:SS."""
    if not content or not isinstance(content, str):
        return None
    m = _CALL_DURATION_RE.match(content.strip())
    if not m:
        return None
    a, b, c = int(m.group(2)), int(m.group(3)), m.group(4)
    if c is not None:
        return float(a * 3600 + b * 60 + int(c))
    return float(a * 60 + b)


def resolve_sticker_caption(content: str, emoji_caption: str) -> str:
    if emoji_caption and str(emoji_caption).strip():
        return str(emoji_caption).strip()
    if content and isinstance(content, str):
        mm = re.search(r"\[表情包[：:]([^]]+)\]", content)
        if mm:
            return mm.group(1).strip()
    return "未命名"


def fmt_clock_duration(sec: float) -> str:
    sec = int(round(sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def longest_streak(days_sorted: list[date]) -> int:
    if not days_sorted:
        return 0
    best = cur = 1
    for i in range(1, len(days_sorted)):
        if days_sorted[i] == days_sorted[i - 1] + timedelta(days=1):
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best


def tokenize_english(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return [w for w in words if len(w) >= 2 and w not in EN_STOP]


def tokenize_chinese(text: str) -> list[str]:
    text = strip_bracket_placeholders(text)
    out: list[str] = []
    for w in jieba.cut(text):
        w = w.strip()
        if len(w) < 2:
            continue
        if not any("\u4e00" <= c <= "\u9fff" for c in w):
            continue
        if w in ZH_STOP:
            continue
        out.append(w)
    return out


def ensure_nltk_data() -> None:
    import nltk

    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        try:
            nltk.download("punkt_tab", quiet=True)
        except Exception:
            nltk.download("punkt", quiet=True)
    try:
        nltk.data.find("taggers/averaged_perceptron_tagger_eng")
    except LookupError:
        try:
            nltk.download("averaged_perceptron_tagger_eng", quiet=True)
        except Exception:
            nltk.download("averaged_perceptron_tagger", quiet=True)


def tokenize_english_nouns(text: str) -> list[str]:
    """Nouns/proper nouns via NLTK (NN, NNS, NNP, NNPS)."""
    import nltk
    from nltk import pos_tag, word_tokenize

    text = strip_bracket_placeholders(text)
    if not text.strip():
        return []
    try:
        tokens = word_tokenize(text.lower())
    except (LookupError, ValueError, TypeError):
        tokens = re.findall(r"[a-zA-Z]+", text.lower())
    if not tokens:
        return []
    try:
        tagged = pos_tag(tokens)
    except (LookupError, ValueError):
        return []
    out: list[str] = []
    for w, tag in tagged:
        if len(w) < 2 or not w.isalpha():
            continue
        if w in EN_STOP:
            continue
        if tag.startswith("NN"):
            out.append(w)
    return out


def _jieba_noun_flag(flag: str) -> bool:
    """True if jieba POS is in the noun family (n, nr, ns, nt, nz, ng, …)."""
    return bool(flag) and flag.startswith("n")


def tokenize_chinese_nouns(text: str) -> list[str]:
    """Chinese nouns via jieba POS; keeps tokens with CJK and noun tags."""
    text = strip_bracket_placeholders(text)
    out: list[str] = []
    for pair in pseg.cut(text):
        w = pair.word.strip()
        flag = pair.flag
        if len(w) < 2:
            continue
        if not any("\u4e00" <= c <= "\u9fff" for c in w):
            continue
        if not _jieba_noun_flag(flag):
            continue
        if w in ZH_STOP:
            continue
        out.append(w)
    return out


def ensure_style():
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "#fafafa",
            "axes.grid": True,
            "grid.alpha": 0.3,
            "font.size": 10,
            "font.sans-serif": [
                "PingFang SC",
                "Heiti SC",
                "Songti SC",
                "STHeiti",
                "Arial Unicode MS",
                "DejaVu Sans",
            ],
            "axes.unicode_minus": False,
        }
    )


def plot_pie(counts: dict[str, int], path: Path):
    fig, ax = plt.subplots(figsize=(6, 6))
    labels = list(counts.keys())
    sizes = [counts[k] for k in labels]
    colors = ["#6366f1", "#f472b6"]
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors)
    ax.set_title("Messages by sender")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_bar_senders(counts: dict[str, int], path: Path, *, title: str = "Total messages (all types)"):
    fig, ax = plt.subplots(figsize=(6, 4))
    names = list(counts.keys())
    vals = [counts[k] for k in names]
    ax.bar(names, vals, color=["#6366f1", "#f472b6"])
    ax.set_ylabel("Count")
    ax.set_title(title)
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:,}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_timeline(daily: pd.Series, path: Path):
    fig, ax = plt.subplots(figsize=(12, 4))
    idx = pd.to_datetime(daily.index)
    ax.fill_between(idx, daily.values, alpha=0.35, color="#6366f1", step="pre")
    ax.plot(idx, daily.values, drawstyle="steps-post", color="#4f46e5", linewidth=1)
    roll = daily.rolling(7, min_periods=1).mean()
    ax.plot(idx, roll.values, color="#f472b6", linewidth=2, label="7-day mean")
    ax.set_title("Daily message volume")
    ax.set_ylabel("Messages per day")
    ax.legend(loc="upper right")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_language_weekly(weekly_en_share: pd.Series, path: Path):
    fig, ax = plt.subplots(figsize=(12, 4))
    idx = pd.to_datetime(weekly_en_share.index)
    ax.plot(idx, weekly_en_share.values * 100, color="#0d9488", linewidth=2)
    ax.axhline(50, color="#94a3b8", linestyle="--", linewidth=1, label="50% English (of zh+en)")
    ax.set_ylim(0, 100)
    ax.set_ylabel("English share (%)")
    ax.set_title("Weekly English share among script-classified text (zh vs en, mixed excluded from ratio)")
    ax.legend(loc="best")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def call_duration_bucket_label(sec: float) -> int:
    """Bucket index 0..4 for histogram."""
    if sec < 60:
        return 0
    if sec < 300:
        return 1
    if sec < 900:
        return 2
    if sec < 3600:
        return 3
    return 4


def plot_call_duration_buckets(
    bucket_counts: list[int],
    bucket_labels: list[str],
    title: str,
    path: Path,
):
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(bucket_labels))
    ax.bar(x, bucket_counts, color="#8b5cf6")
    ax.set_xticks(x)
    ax.set_xticklabels(bucket_labels, rotation=25, ha="right")
    ax.set_ylabel("Connected calls")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_peak_hours(hours: np.ndarray, path: Path):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(range(24), hours, color="#6366f1")
    ax.set_xticks(range(24))
    ax.set_xlabel("Hour of day (0-23)")
    ax.set_ylabel("Messages")
    ax.set_title("Messages by hour of day")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_top_words(
    counter: Counter,
    title: str,
    path: Path,
    top_n: int = 5,
    *,
    bar_color: str = "#0d9488",
):
    top = counter.most_common(top_n)
    if not top:
        fig, ax = plt.subplots(figsize=(6, 2))
        ax.text(0.5, 0.5, "No tokens", ha="center", va="center")
        ax.axis("off")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return
    words, counts = zip(*top, strict=True)
    fig, ax = plt.subplots(figsize=(6, 3))
    y = np.arange(len(words))
    ax.barh(y, counts, color=bar_color)
    ax.set_yticks(y)
    ax.set_yticklabels(words)
    ax.invert_yaxis()
    ax.set_xlabel("Count")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def build_html(
    out_dir: Path,
    meta: dict,
    sections_html: list[str],
) -> None:
    body = "\n".join(sections_html)
    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Chat analytics report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 24px auto; padding: 0 16px;
      color: #1f2937; line-height: 1.5; }}
    h1 {{ font-size: 1.75rem; }}
    h2 {{ font-size: 1.25rem; margin-top: 2rem; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.25rem; }}
    .meta {{ color: #6b7280; font-size: 0.9rem; margin-bottom: 1.5rem; }}
    img {{ max-width: 100%; height: auto; border-radius: 8px; margin: 12px 0;
      box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
    th, td {{ border: 1px solid #e5e7eb; padding: 8px 10px; text-align: left; }}
    th {{ background: #f9fafb; }}
    ul.notes {{ font-size: 0.9rem; color: #4b5563; }}
  </style>
</head>
<body>
  <h1>WeChat chat analytics (Phase 1)</h1>
  <div class="meta">{html.escape(meta["summary"])}</div>
  {body}
</body>
</html>
"""
    (out_dir / "report.html").write_text(doc, encoding="utf-8")


def main() -> None:
    args = parse_args()
    tz = ZoneInfo(args.timezone)
    cap = args.response_cap_seconds
    out_dir = args.output_dir.resolve()
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    ensure_style()
    jieba.initialize()
    ensure_nltk_data()

    print("Loading JSON…")
    raw = load_messages(args.input)

    rows: list[dict] = []
    for m in raw:
        if not isinstance(m, dict):
            continue
        dt = message_dt(m, tz)
        if dt is None:
            continue
        is_send = m.get("isSend")
        if is_send not in (0, 1):
            continue
        ec_raw = m.get("emojiCaption")
        emoji_caption = ec_raw.strip() if isinstance(ec_raw, str) else ""
        rows.append(
            {
                "dt": dt,
                "date": dt.date(),
                "hour": dt.hour,
                "is_send": int(is_send),
                "sender": NAME_DIANNE if is_send == 1 else NAME_YIFAN,
                "type": m.get("type") or "",
                "content": m.get("content") if isinstance(m.get("content"), str) else "",
                "createTime": int(m["createTime"]),
                "emoji_caption": emoji_caption,
            }
        )

    df = pd.DataFrame(rows).sort_values("createTime").reset_index(drop=True)
    total = len(df)

    # --- Big numbers ---
    dates_active = sorted(df["date"].unique())
    active_days = len(dates_active)
    first_d, last_d = dates_active[0], dates_active[-1]
    calendar_span = (last_d - first_d).days + 1
    avg_per_day = total / active_days if active_days else 0
    streak = longest_streak(list(dates_active))

    counts_sender = df["sender"].value_counts().to_dict()
    # Ensure both keys for charts
    pie_counts = {NAME_YIFAN: counts_sender.get(NAME_YIFAN, 0), NAME_DIANNE: counts_sender.get(NAME_DIANNE, 0)}

    daily = df.groupby("date").size()
    plot_pie(pie_counts, fig_dir / "pie_senders.png")
    plot_bar_senders(pie_counts, fig_dir / "bar_senders.png")
    plot_timeline(daily, fig_dir / "timeline_daily.png")

    # --- Language (text only) ---
    text_df = df[df["type"] == "文本消息"].copy()
    text_df["script"] = text_df["content"].apply(classify_script)
    script_counts = text_df["script"].value_counts().to_dict()
    zh_n = script_counts.get("zh", 0)
    en_n = script_counts.get("en", 0)
    mixed_n = script_counts.get("mixed", 0)
    en_share_overall = en_n / (zh_n + en_n) if (zh_n + en_n) > 0 else 0.0

    # Weekly English share: among zh+en only per week (tz-aware Grouper keeps local week boundaries)
    weekly_rows: list[tuple[datetime, float]] = []
    g_week = text_df.groupby(
        pd.Grouper(key="dt", freq="W-MON", label="left", closed="left"),
        sort=True,
    )
    for week_start, g in g_week:
        if g.empty:
            continue
        z = (g["script"] == "zh").sum()
        e = (g["script"] == "en").sum()
        if z + e == 0:
            continue
        weekly_rows.append((week_start, e / (z + e)))
    weekly_en = (
        pd.Series({t: v for t, v in weekly_rows}, dtype=float) if weekly_rows else pd.Series(dtype=float)
    )
    if len(weekly_en):
        plot_language_weekly(weekly_en, fig_dir / "language_over_time.png")

    # --- Peak hours (all messages) ---
    hour_counts = df["hour"].value_counts().reindex(range(24), fill_value=0).values
    plot_peak_hours(hour_counts, fig_dir / "peak_hours.png")
    peak_h = int(hour_counts.argmax())
    low_h = int(hour_counts.argmin())

    # --- Top words ---
    en_counter: Counter = Counter()
    zh_counter: Counter = Counter()
    en_noun_counter: Counter = Counter()
    zh_noun_counter: Counter = Counter()
    for _, r in text_df.iterrows():
        c = r["content"]
        if not isinstance(c, str):
            continue
        clean = strip_bracket_placeholders(c)
        if r["script"] == "en":
            en_counter.update(tokenize_english(clean))
            en_noun_counter.update(tokenize_english_nouns(clean))
        elif r["script"] == "zh":
            zh_counter.update(tokenize_chinese(clean))
            zh_noun_counter.update(tokenize_chinese_nouns(clean))
        else:
            en_counter.update(tokenize_english(clean))
            zh_counter.update(tokenize_chinese(clean))
            en_noun_counter.update(tokenize_english_nouns(clean))
            zh_noun_counter.update(tokenize_chinese_nouns(clean))

    plot_top_words(en_counter, "Top English tokens (text messages)", fig_dir / "top_words_en.png")
    plot_top_words(zh_counter, "Top Chinese tokens (text messages, jieba)", fig_dir / "top_words_zh.png")
    top5_en = en_counter.most_common(5)
    top5_zh = zh_counter.most_common(5)

    plot_top_words(
        en_noun_counter,
        "Top English nouns (NLTK POS: NN/NNS/NNP/NNPS)",
        fig_dir / "top_nouns_en.png",
        bar_color="#7c3aed",
    )
    plot_top_words(
        zh_noun_counter,
        "Top Chinese nouns (jieba POS: n*)",
        fig_dir / "top_nouns_zh.png",
        bar_color="#7c3aed",
    )
    top5_en_n = en_noun_counter.most_common(5)
    top5_zh_n = zh_noun_counter.most_common(5)

    # --- Top sticker captions (动画表情) ---
    sticker_df = df[df["type"] == "动画表情"].copy()
    sticker_df["_cap"] = sticker_df.apply(
        lambda r: resolve_sticker_caption(str(r["content"]), str(r["emoji_caption"])),
        axis=1,
    )
    sticker_counter: Counter = Counter(sticker_df["_cap"].tolist())
    plot_top_words(
        sticker_counter,
        "Top 5 sticker captions (动画表情)",
        fig_dir / "top_stickers.png",
        top_n=5,
        bar_color="#f59e0b",
    )
    top5_stickers = sticker_counter.most_common(5)
    sticker_split_rows = []
    for sticker_label, _ in top5_stickers:
        sub = sticker_df[sticker_df["_cap"] == sticker_label]
        sticker_split_rows.append(
            (
                sticker_label,
                int((sub["is_send"] == 1).sum()),
                int((sub["is_send"] == 0).sum()),
                len(sub),
            )
        )

    # --- Voice/video calls (通话消息) ---
    call_df = df[df["type"] == "通话消息"].copy()
    call_df["_sec"] = call_df["content"].map(parse_call_duration_seconds)
    connected = call_df[call_df["_sec"].notna()]
    total_call_sec = float(connected["_sec"].sum()) if len(connected) else 0.0
    call_events_yifan = int((call_df["is_send"] == 0).sum())
    call_events_dianne = int((call_df["is_send"] == 1).sum())
    call_events_total = len(call_df)
    longest_call_sec = 0.0
    longest_call_when = ""
    longest_call_content = ""
    longest_call_kind = ""
    if len(connected):
        li = connected["_sec"].idxmax()
        row = call_df.loc[li]
        longest_call_sec = float(connected.loc[li, "_sec"])
        longest_call_when = row["dt"].strftime("%Y-%m-%d %H:%M")
        longest_call_content = str(row["content"])
        mkind = _CALL_DURATION_RE.match(longest_call_content.strip())
        longest_call_kind = mkind.group(1) if mkind else ""

    plot_bar_senders(
        {NAME_YIFAN: call_events_yifan, NAME_DIANNE: call_events_dianne},
        fig_dir / "bar_call_events.png",
        title="通话消息 rows by sender (call log events)",
    )

    # --- Calls in trailing 365 days (long vs short summary) ---
    last_dt = df["dt"].max()
    trail_start = last_dt - timedelta(days=365)
    connected_year = connected[connected["dt"] >= trail_start].copy()
    py1_n = len(connected_year)
    py1_total_sec = float(connected_year["_sec"].sum()) if py1_n else 0.0
    py1_mean = float(connected_year["_sec"].mean()) if py1_n else 0.0
    py1_median = float(connected_year["_sec"].median()) if py1_n else 0.0
    py1_longest_sec = 0.0
    py1_longest_when = ""
    py1_longest_line = ""
    py1_shortest_sec = 0.0
    py1_shortest_when = ""
    py1_shortest_line = ""
    bucket_labels = ["Under 1 min", "1-5 min", "5-15 min", "15-60 min", "1 hour +"]
    bucket_counts = [0, 0, 0, 0, 0]
    if py1_n:
        li_mx = connected_year["_sec"].idxmax()
        li_mn = connected_year["_sec"].idxmin()
        r_mx = call_df.loc[li_mx]
        r_mn = call_df.loc[li_mn]
        py1_longest_sec = float(connected_year.loc[li_mx, "_sec"])
        py1_shortest_sec = float(connected_year.loc[li_mn, "_sec"])
        py1_longest_when = r_mx["dt"].strftime("%Y-%m-%d %H:%M")
        py1_shortest_when = r_mn["dt"].strftime("%Y-%m-%d %H:%M")
        py1_longest_line = str(r_mx["content"])
        py1_shortest_line = str(r_mn["content"])
        for s in connected_year["_sec"].astype(float):
            bucket_counts[call_duration_bucket_label(s)] += 1
    plot_call_duration_buckets(
        bucket_counts,
        bucket_labels,
        f"Connected call lengths (trailing 365 days to {last_dt.strftime('%Y-%m-%d')})",
        fig_dir / "call_duration_buckets_year.png",
    )

    # --- Response times ---
    latencies_yifan: list[float] = []
    latencies_dianne: list[float] = []
    for i in range(len(df) - 1):
        a, b = df.iloc[i], df.iloc[i + 1]
        if a["is_send"] == b["is_send"]:
            continue
        delta = b["createTime"] - a["createTime"]
        if delta <= 0 or delta > cap:
            continue
        if b["is_send"] == 0:
            latencies_yifan.append(delta)
        else:
            latencies_dianne.append(delta)

    def summarize_latencies(xs: list[float]) -> tuple[float, float, float, int]:
        if not xs:
            return (float("nan"), float("nan"), float("nan"), 0)
        arr = np.array(xs, dtype=float)
        return (
            float(np.mean(arr)),
            float(np.median(arr)),
            float(np.percentile(arr, 90)),
            len(xs),
        )

    my_mean, my_med, my_p90, my_n = summarize_latencies(latencies_yifan)
    di_mean, di_med, di_p90, di_n = summarize_latencies(latencies_dianne)

    def fmt_dur(sec: float) -> str:
        if sec != sec:  # nan
            return "—"
        if sec < 60:
            return f"{sec:.1f}s"
        if sec < 3600:
            return f"{sec / 60:.1f} min"
        return f"{sec / 3600:.2f} h"

    # --- Extremes ---
    busiest_date = daily.idxmax()
    busiest_n = int(daily.max())
    nonzero = daily[daily > 0]
    quietest_date = nonzero.idxmin()
    quietest_n = int(nonzero.min())

    text_only = text_df.copy()
    text_only["len_raw"] = text_only["content"].str.len()
    longest_idx = text_only["len_raw"].idxmax() if len(text_only) else None
    longest_len = int(text_only.loc[longest_idx, "len_raw"]) if longest_idx is not None else 0
    longest_preview = ""
    if longest_idx is not None:
        raw = str(text_only.loc[longest_idx, "content"])
        longest_preview = raw[:200] + ("…" if len(raw) > 200 else "")

    meta_summary = (
        f"Source: {args.input.name} · Timezone: {args.timezone} · "
        f"Response stats exclude gaps > {cap // 3600}h · Generated {datetime.now(tz).strftime('%Y-%m-%d %H:%M')}"
    )

    sections: list[str] = []

    sections.append(
        f"""
<h2>1. Big numbers</h2>
<table>
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>Total messages (all types)</td><td>{total:,}</td></tr>
<tr><td>Active days (≥1 message)</td><td>{active_days:,}</td></tr>
<tr><td>Calendar span (first→last date)</td><td>{calendar_span:,} days</td></tr>
<tr><td>Average messages per active day</td><td>{avg_per_day:.1f}</td></tr>
<tr><td>Longest streak (consecutive days with activity)</td><td>{streak} days</td></tr>
<tr><td>{NAME_YIFAN}</td><td>{pie_counts[NAME_YIFAN]:,}</td></tr>
<tr><td>{NAME_DIANNE}</td><td>{pie_counts[NAME_DIANNE]:,}</td></tr>
</table>
<p><img src="figures/bar_senders.png" alt="Bar senders"/><br/>
<img src="figures/pie_senders.png" alt="Pie senders"/></p>
<ul class="notes">
<li>Volume includes stickers, images, system types, etc., whenever a row has a timestamp.</li>
</ul>
"""
    )

    sections.append(
        f"""
<h2>2. Timeline — texting density</h2>
<p><img src="figures/timeline_daily.png" alt="Timeline"/></p>
<ul class="notes">
<li>Daily counts (stepped area) with a 7-day rolling mean overlay.</li>
</ul>
"""
    )

    lang_img = (
        '<p><img src="figures/language_over_time.png" alt="Language over time"/></p>'
        if len(weekly_en)
        else "<p><em>No weekly language series (no text messages).</em></p>"
    )
    sections.append(
        f"""
<h2>3. Language split (文本消息)</h2>
<table>
<tr><th>Script label</th><th>Messages</th></tr>
<tr><td>Mostly Chinese</td><td>{zh_n:,}</td></tr>
<tr><td>Mostly English</td><td>{en_n:,}</td></tr>
<tr><td>Mixed / other letters</td><td>{mixed_n:,}</td></tr>
<tr><td>English share (of zh+en only)</td><td>{en_share_overall * 100:.1f}%</td></tr>
</table>
{lang_img}
<ul class="notes">
<li>Per message: CJK vs Latin letter counts; ≥55% CJK → Chinese, ≤45% CJK → English, else mixed.</li>
<li>Weekly chart: among messages labeled Chinese or English only, fraction that are English (mixed excluded from denominator).</li>
</ul>
"""
    )

    sections.append(
        f"""
<h2>4. Peak hours</h2>
<p>Busiest hour: <strong>{peak_h}:00</strong> · Quietest hour: <strong>{low_h}:00</strong></p>
<p><img src="figures/peak_hours.png" alt="Peak hours"/></p>
<ul class="notes">
<li>Hour buckets use timestamps in {args.timezone}.</li>
</ul>
"""
    )

    sections.append(
        f"""
<h2>5. Top tokens</h2>
<table>
<tr><th>English (top 5)</th><th>Count</th></tr>
{"".join(f"<tr><td>{html.escape(w)}</td><td>{c}</td></tr>" for w, c in top5_en)}
</table>
<table>
<tr><th>Chinese (top 5, jieba)</th><th>Count</th></tr>
{"".join(f"<tr><td>{html.escape(w)}</td><td>{c}</td></tr>" for w, c in top5_zh)}
</table>
<p><img src="figures/top_words_en.png" alt="Top EN"/><br/>
<img src="figures/top_words_zh.png" alt="Top ZH"/></p>
<h3>Top nouns (POS-filtered)</h3>
<p>English: words tagged as nouns/proper nouns (NLTK). Chinese: jieba part-of-speech tags starting with <code>n</code> (普通名、地名、机构名等).</p>
<table>
<tr><th>English nouns (top 5)</th><th>Count</th></tr>
{"".join(f"<tr><td>{html.escape(w)}</td><td>{c}</td></tr>" for w, c in top5_en_n)}
</table>
<table>
<tr><th>Chinese nouns (top 5)</th><th>Count</th></tr>
{"".join(f"<tr><td>{html.escape(w)}</td><td>{c}</td></tr>" for w, c in top5_zh_n)}
</table>
<p><img src="figures/top_nouns_en.png" alt="Top EN nouns"/><br/>
<img src="figures/top_nouns_zh.png" alt="Top ZH nouns"/></p>
<ul class="notes">
<li>POS tagging is imperfect on slang and short fragments; treat as directional, not ground truth.</li>
</ul>
<h3>Top 5 sticker captions (动画表情)</h3>
<p>From <code>emojiCaption</code> when present; otherwise parsed from <code>[表情包：…]</code> in content; else labeled 未命名.</p>
<table>
<tr><th>Caption</th><th>Count</th></tr>
{"".join(f"<tr><td>{html.escape(w)}</td><td>{c}</td></tr>" for w, c in top5_stickers)}
</table>
<table>
<tr><th>Caption</th><th>{html.escape(NAME_DIANNE)}</th><th>{html.escape(NAME_YIFAN)}</th><th>Total</th></tr>
{"".join(
        f"<tr><td>{html.escape(cap)}</td><td>{dn}</td><td>{yf}</td><td>{tot}</td></tr>"
        for cap, dn, yf, tot in sticker_split_rows
    )}
</table>
<p><img src="figures/top_stickers.png" alt="Top sticker captions"/></p>
<ul class="notes">
<li>Chart uses the same font stack as other CJK plots so captions render in the PNG.</li>
</ul>
"""
    )

    sections.append(
        f"""
<h2>6. Reply speed (speaker change, next message is the “reply”)</h2>
<table>
<tr><th>Person (replier)</th><th>N</th><th>Mean</th><th>Median</th><th>P90</th></tr>
<tr><td>{NAME_YIFAN}</td><td>{my_n}</td><td>{fmt_dur(my_mean)}</td><td>{fmt_dur(my_med)}</td><td>{fmt_dur(my_p90)}</td></tr>
<tr><td>{NAME_DIANNE}</td><td>{di_n}</td><td>{fmt_dur(di_mean)}</td><td>{fmt_dur(di_med)}</td><td>{fmt_dur(di_p90)}</td></tr>
</table>
<ul class="notes">
<li>Only pairs where the sender alternates; gaps longer than {cap // 3600} hours are excluded from these aggregates.</li>
</ul>
"""
    )

    sections.append(
        f"""
<h2>7. Extremes</h2>
<table>
<tr><th>Busiest day</th><td>{busiest_date} ({busiest_n:,} messages)</td></tr>
<tr><th>Quietest day (among days with &gt;0)</td><td>{quietest_date} ({quietest_n:,} messages)</td></tr>
<tr><th>Longest text message (characters)</td><td>{longest_len:,}</td></tr>
</table>
<p><strong>Longest preview:</strong> {html.escape(longest_preview)}</p>
"""
    )

    longest_call_html = ""
    if longest_call_sec > 0:
        longest_call_html = (
            f"<tr><th>Longest connected call</th><td>{fmt_clock_duration(longest_call_sec)} "
            f"({html.escape(longest_call_kind)}) at {html.escape(longest_call_when)}<br/>"
            f"<code>{html.escape(longest_call_content)}</code></td></tr>"
        )
    else:
        longest_call_html = "<tr><th>Longest connected call</th><td>No parsed durations in export</td></tr>"

    trail_end_s = last_dt.strftime("%Y-%m-%d")
    trail_start_s = trail_start.strftime("%Y-%m-%d")
    if py1_n:
        py1_long_short_html = f"""
<tr><th>Longest call (in window)</th><td>{fmt_clock_duration(py1_longest_sec)} at {html.escape(py1_longest_when)}<br/><code>{html.escape(py1_longest_line)}</code></td></tr>
<tr><th>Shortest connected call (in window)</th><td>{fmt_clock_duration(py1_shortest_sec)} at {html.escape(py1_shortest_when)}<br/><code>{html.escape(py1_shortest_line)}</code></td></tr>
"""
    else:
        py1_long_short_html = "<tr><th>Longest / shortest (in window)</th><td>No connected calls with duration in this period</td></tr>"

    sections.append(
        f"""
<h2>8. Voice &amp; video calls (<code>通话消息</code>)</h2>
<table>
<tr><th>Total connected call time</th><td>{fmt_clock_duration(total_call_sec)} ({total_call_sec:,.0f}s); only rows with a parsed <code>MM:SS</code> or <code>H:MM:SS</code> duration after <code>[语音通话]</code>/<code>[视频通话]</code></td></tr>
<tr><th>Call log rows (all statuses)</th><td>{call_events_total:,} total ({NAME_YIFAN}: {call_events_yifan:,}, {NAME_DIANNE}: {call_events_dianne:,})</td></tr>
{longest_call_html}
</table>
<p><img src="figures/bar_call_events.png" alt="Call events by sender"/></p>
<h3>Past year: long and short calls (trailing 365 days)</h3>
<p>Window: <strong>{html.escape(trail_start_s)}</strong> through <strong>{html.escape(trail_end_s)}</strong> (from latest message in export). Only connected calls with a parsed duration.</p>
<table>
<tr><th>Connected calls (with duration)</th><td>{py1_n:,}</td></tr>
<tr><th>Total time in window</th><td>{fmt_clock_duration(py1_total_sec)} ({py1_total_sec:,.0f}s)</td></tr>
<tr><th>Mean call length</th><td>{fmt_clock_duration(py1_mean)}</td></tr>
<tr><th>Median call length</th><td>{fmt_clock_duration(py1_median)}</td></tr>
{py1_long_short_html}
</table>
<p><img src="figures/call_duration_buckets_year.png" alt="Call duration buckets past year"/></p>
<ul class="notes">
<li>Buckets: under 1 min (quick check-ins), 1-5, 5-15, 15-60 min, and 1 hour or longer (long calls).</li>
<li>Each row is one WeChat call log line on this export; <code>isSend</code> maps to which side the line is attributed to (proxy for who initiated / whose UI logged it).</li>
<li>Rows like 已取消 / 对方已拒绝 / 忙线未接听 have no duration and do not add to total time.</li>
<li>Timestamps use {args.timezone}.</li>
</ul>
"""
    )

    build_html(out_dir, {"summary": meta_summary}, sections)
    print(f"Wrote {out_dir / 'report.html'}")


if __name__ == "__main__":
    main()
