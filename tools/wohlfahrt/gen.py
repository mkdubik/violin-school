"""Write wohlfahrt.js from ly2app.py's JSON.

Usage: python3 -I gen.py op45.json ../../wohlfahrt.js

CORRECTIONS holds the notes where the 1905 Schirmer edition (IMSLP19882) shows the LilyPond
edition is wrong; check a new one against that scan before adding it.
"""
import json
import sys
from fractions import Fraction as F

data = json.load(open(sys.argv[1]))

# Where the LilyPond edition differs from the 1905 Schirmer edition, the book wins:
# (étude, measure index, note index): (LilyPond's pitch, the book's pitch).
CORRECTIONS = {
    ("22", 13, 0): ("D4", "E4"),
    ("28", 20, 6): ("D5", "C5"),
}
for (n, mi, ni), (was, now) in CORRECTIONS.items():
    note = data[n]["measures"][mi][ni]
    assert note["pitch"] == was, (n, mi, ni, note["pitch"])
    note["pitch"] = now

KEY_NAMES = {"c": "C", "g": "G", "d": "D", "a": "A", "f": "F", "bes": "B♭", "ees": "E♭"}
KEY_ACCENT = {"c": "#8a8a7a", "g": "#c47a3a", "d": "#5a9e6f", "a": "#4a8fc4", "f": "#9a76b4",
              "bes": "#b86a7a", "ees": "#a4646a"}
FOURTH = {"D4", "A4", "E5"}  # 4th finger instead of the open string above
SECOND = {"13", "27", "28"}  # double stops worth hearing: their lower notes are the 2nd violin
NOTES = {
    "1": "the book: hold the fingers down as long as possible, the left wrist very quiet",
    "15": "each eighth bowed as two sixteenths (the book writes an eighth with a slash)",
}


def num(fr):
    fr = F(fr)
    return str(fr.numerator) if fr.denominator == 1 else str(float(fr)).rstrip("0")


def item(n):
    beats = F(n["beats"])
    if n["rest"]:
        return "REST" if beats == 1 else f"rest({num(beats)})"
    p = f'"{n["pitch"]}"'
    if n["triplet"]:
        x = {F(1, 3): f"t({p})", F(1, 6): f"t6({p})"}[beats]
    else:
        x = {F(1): p, F(1, 2): f"e({p})", F(1, 4): f"s({p})", F(2): f"h({p})", F(4): f"w({p})",
             F(3): f"dotted(h({p}))", F(3, 2): f"dotted({p})", F(3, 4): f"dotted(e({p}))"}[beats]
    if n["tie"]:
        x = f"tied({x})"
    if n["finger"] == 4 and n["pitch"] in FOURTH:
        x = f"f4({x})"
    return x


def rests(beats):
    out = []
    for length in (F(4), F(2), F(1), F(1, 2), F(1, 4)):
        while beats >= length:
            out.append({"rest": True, "beats": str(length)})
            beats -= length
    assert beats == 0
    return out


def midi(p):
    names = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    acc = {"": 0, "#": 1, "b": -1}[p[1:-1]]
    return (int(p[-1]) + 1) * 12 + names[p[0]] + acc


def build_second(s, n_bars, bar_beats, pickup_beats):
    # all in quarter beats from the start of the piece
    events = [(F(st), F(d), p) for st, d, p in s["second"]]
    t = F(0)
    for m in s["measures"]:
        for e in m:
            if e["lower"]:
                events.append((t, F(e["beats"]), max(e["lower"], key=midi)))
            t += F(e["beats"])
    # one voice: at each start keep the highest; cut a note short where the next begins
    by_start = {}
    for st, d, p in events:
        if st not in by_start or midi(p) > midi(by_start[st][1]):
            by_start[st] = (d, p)
    starts = sorted(by_start)
    line = []
    for i, st in enumerate(starts):
        d, p = by_start[st]
        if i + 1 < len(starts):
            d = min(d, starts[i + 1] - st)
        line.append((st, d, p))
    bars = []
    bar_starts = [F(0)] + [F(pickup_beats or bar_beats) + bar_beats * k for k in range(n_bars)]
    for b in range(n_bars):
        lo, hi = bar_starts[b], bar_starts[b + 1]
        at = lo
        bar = []
        for st, d, p in line:
            if lo <= st < hi:
                if st > at:
                    bar += rests(st - at)
                d = min(d, hi - st)
                bar.append({"rest": False, "pitch": p, "beats": str(d), "tie": False, "triplet": False,
                            "finger": None})
                at = st + d
        if at < hi:
            bar += rests(hi - at)
        bars.append(bar)
    return bars


def main():
    groups = [(1, 10), (11, 20), (21, 30)]
    pieces = []
    for n in range(1, 31):
        s = data[str(n)]
        num_, den = map(int, s["time"].split("/"))
        bar_beats = F(num_ * 4, den)
        key = s["key"][0]
        tempo_unit, tempo_val = s["tempo"]
        bpm = round(int(tempo_val) * 4 / int(tempo_unit))
        extras = []
        if s["partial"]:
            extras.append("starts on a pickup")
        if s["voltas"]:
            extras.append("both halves played twice")
        if str(n) in SECOND:
            extras.append("double stops: the lower notes are the 2nd violin")
        if str(n) in NOTES:
            extras.append(NOTES[str(n)])
        meta = " · ".join([f"F. Wohlfahrt, Op. 45 No. {n}", s["tempo_text"], f"{KEY_NAMES[key]} major", s["time"]] + extras)
        lines = [f"    op45no{n}: {{",
                 f'      title: "Étude No. {n}",',
                 f'      detail: "{s["tempo_text"]} · {KEY_NAMES[key]} major · {s["time"]}",',
                 f'      meta: "{meta}",',
                 f'      accent: "{KEY_ACCENT[key]}",',
                 f"      tempo: [{{ bar: 1, bpm: {bpm} }}],"]
        if tempo_unit == "8":
            lines.append('      tempoUnit: "eighth",')
        if s["partial"]:
            lines.append("      pickup: true,")
        if s["voltas"]:
            secs = []
            # bar index (1-based, as the app numbers them in `sections`) for a time in quarters
            def bar_at(q):
                q = F(q)
                if s["partial"]:
                    q += bar_beats - F(s["partial"])
                return int(q // bar_beats)
            prev_end = 0
            for start, count, nalt, end in s["voltas"]:
                a, b = bar_at(start) + 1, bar_at(end)
                if a > prev_end + 1:
                    secs.append(f"{{ from: {prev_end + 1}, to: {a - 1} }}")
                secs.append(f"{{ from: {a}, to: {b}, repeat: true }}")
                prev_end = b
            lines.append(f"      sections: [{', '.join(secs)}],")
        if bar_beats != 4 and den == 8:
            lines.append(f"      beamBeats: {num(bar_beats if num_ == 3 else bar_beats / 2)},")
        lines.append("      measures: [")
        for m in s["measures"]:
            lines.append(f"        [{', '.join(item(e) for e in m)}],")
        lines.append("      ],")
        if str(n) in SECOND:
            sec = build_second(s, len(s["measures"]), bar_beats, F(s["partial"]) if s["partial"] else None)
            lines.append("      second: [")
            for m in sec:
                lines.append(f"        [{', '.join(item(e) for e in m)}],")
            lines.append("      ],")
        if s["time"] == "3/8":
            lines.append("      sheetLayout: { measuresPerSystem: 6 },")
        lines.append("    },")
        pieces.append("\n".join(lines))

    def keys_in(a, b):
        seen = []
        for n in range(a, b + 1):
            k = KEY_NAMES[data[str(n)]["key"][0]]
            if k not in seen:
                seen.append(k)
        return ", ".join(seen[:-1]) + " and " + seen[-1] + " major" if len(seen) > 1 else seen[0] + " major"

    group_lines = []
    for a, b in groups:
        ids = ", ".join(f'"op45no{n}"' for n in range(a, b + 1))
        group_lines.append(
            f'        {{ title: "Nos. {a}–{b}", detail: "{keys_in(a, b)}", accent: "{KEY_ACCENT[data[str(a)]["key"][0]]}", pieces: [{ids}] }},')
    body = "\n".join(pieces)
    js = HEADER + body + "\n" + MIDDLE + "\n".join(group_lines) + "\n" + FOOTER
    open(sys.argv[2], "w").write(js)


HEADER = """// Franz Wohlfahrt's 60 Studies, Op. 45, Book I (Nos. 1–30), for the Notes tab: the étude
// book that goes beside Suzuki Books 2–3, all in first position (No. 30 reaches C6 with the
// 4th finger stretched). The notes are read from Philipp Büttgenbach's LilyPond edition on
// IMSLP (CC BY-SA 4.0) and checked against the 1905 Schirmer edition (ed. Gaston Blay),
// which settles the two places they differ (No. 22 bar 13 starts on E4, No. 28 bar 21 has C5
// as its 7th note).
// Wohlfahrt marks only a tempo word; the tempo numbers are the LilyPond edition's (in 6/8
// and 3/8 its ♪ = 123 becomes 124, as the slider moves in whole quarter beats).
//
// As written in the book, with these changes for the app: the 4th fingers the book marks
// on the notes an open string also plays (D4, A4, E5) are kept with f4; other fingerings,
// slurs, bowings and dynamics are left out. Double stops and chords play their top note;
// in Nos. 13, 27 and 28 their lower notes are the 2nd violin part. No. 15's slashed eighths
// are written out as sixteenths, and in No. 28 both halves repeat.
//
// Made by tools/wohlfahrt/ (ly2app.py, then gen.py): change those and run them again rather
// than editing this file.
(window.SONGBOOKS ??= []).push(({ h, w, e, s, t, t6, dotted, tied, f4, rest, REST }) => ({
  pieces: {
"""
MIDDLE = """  },
  collection: {
    id: "wohlfahrt",
    title: "Wohlfahrt Op. 45",
    detail: "Études, Book I · Nos. 1–30 · first position",
    accent: "#7a8a6a",
    pieces: [
"""
FOOTER = """    ],
  },
}));
"""

main()
