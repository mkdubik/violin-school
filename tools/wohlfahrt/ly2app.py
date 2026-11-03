"""Read Wohlfahrt Op. 45 studies from Philipp Büttgenbach's LilyPond edition into JSON for gen.py.

Usage: python3 -I ly2app.py Wohlfahrt_Opus-45.ly 1 30 > op45.json

The .ly file is in IMSLP's zip (IMSLP449577) on the Op. 45 page. This reads it as text and
never runs LilyPond. It knows the LilyPond the edition uses: \\relative, \\repeat (unfold,
percent, volta), \\tuplet, chords, two-voice << >> passages, tremolo eighths (c8:16) and the
edition's own note macros. Bar checks that don't fall on a barline stop it.
"""
import json
import re
import sys
from fractions import Fraction as F

ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV",
         "XVI", "XVII", "XVIII", "XIX", "XX", "XXI", "XXII", "XXIII", "XXIV", "XXV", "XXVI", "XXVII",
         "XXVIII", "XXIX", "XXX"]
STEP = {"c": 0, "d": 1, "e": 2, "f": 3, "g": 4, "a": 5, "b": 6}
LETTER = "CDEFGAB"


def block_after(text, start):
    """Text inside the brace that opens at or after `start`, and the index after its close."""
    i = text.index("{", start)
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1:j], j + 1
    raise ValueError("unbalanced")


def strip_comments(text):
    text = re.sub(r"%\{.*?%\}", " ", text, flags=re.S)
    return re.sub(r"%[^\n]*", " ", text)


TOKEN = re.compile(r"""
    (?P<str>"[^"]*")
  | (?P<cmd>\\[A-Za-z]+)
  | (?P<open><<|\{|<(?![<])(?=\s*[a-g]))
  | (?P<close>>>|\}|>)
  | (?P<frac>\d+/\d+)
  | (?P<note>[a-gsrR](?:isis|eses|is|es|s(?![a-z]))?(?![a-zA-Z])[',]*[!?]?(?:\d+\.*)?(?:\*\d+(?:/\d+)?)?(?::\d*)?)
  | (?P<dur>(?<![a-zA-Z0-9])\d+\.*(?:\*\d+(?:/\d+)?)?)
  | (?P<tilde>~)
  | (?P<bar>\|)
  | (?P<finger>[-_^]\d)
  | (?P<artic>[-_^][.>^_!+|-]|[-_^](?=\\)|[()\[\]]|\\[<>!]|\\\(|\\\))
  | (?P<eq>=)
  | (?P<num>\#?[-\d.]+|\#'?[A-Za-z(][^\s]*|\#\#[tf])
  | (?P<word>[A-Za-z][A-Za-z.]*)
  | (?P<ws>\s+)
  | (?P<other>.)
""", re.X)


def tokenize(text):
    out = []
    for m in TOKEN.finditer(text):
        kind = m.lastgroup
        if kind == "ws":
            continue
        out.append((kind, m.group()))
    return out


class Converter:
    def __init__(self, macros):
        self.macros = macros
        self.events = []  # dicts: pitch(midi-ish tuple) or rest, dur (Fraction of whole), etc.
        self.second = []  # (start, dur, pitch) lower notes of chords and second voices
        self.time = F(0)
        self.default_dur = F(1, 4)
        self.tuplet = F(1)
        self.bars = []  # positions of | bar checks
        self.partial = None
        self.timesig = None
        self.tempo = None
        self.trem = None
        self.pending_trem = None

    # Pitches are (step, alter, octave) with octave in LilyPond terms (c' = 1). In \relative a
    # note takes the octave that puts it within a 4th of the one before, then its ' and , marks.
    @staticmethod
    def relative(ref, step, octave_marks):
        rstep, roct = ref
        octave = next(o for o in (roct - 1, roct, roct + 1) if -3 <= (o * 7 + step) - (roct * 7 + rstep) <= 3)
        return (step, octave + octave_marks)

    def parse_note(self, tok, ref):
        m = re.match(r"([a-gsrR])(isis|eses|is|es|s(?![a-z]))?([',]*)([!?]?)(\d+\.*)?(?:\*(\d+)(?:/(\d+))?)?(:\d*)?$", tok)
        name, acc, marks, _, dur, mul_n, mul_d, trem = m.groups()
        if trem is not None:
            if len(trem) > 1:
                self.trem = F(1, int(trem[1:]))
            self.pending_trem = self.trem
        if dur:
            base = F(1, int(dur.rstrip(".")))
            dots = dur.count(".")
            d = base
            add = base
            for _ in range(dots):
                add /= 2
                d += add
            self.default_dur = d
        d = self.default_dur
        if mul_n:
            d = d * F(int(mul_n), int(mul_d or 1))
        if name in "srR":
            return None, d, ref
        alter = {"is": 1, "isis": 2, "es": -1, "eses": -2, "s": -1, None: 0}[acc]
        octs = marks.count("'") - marks.count(",")
        step, octave = self.relative(ref, STEP[name], octs)
        return (STEP[name], alter, octave), d, (step, octave)

    def run(self, tokens, ref):
        i = 0
        last_event = None
        while i < len(tokens):
            kind, val = tokens[i]
            if kind == "cmd":
                c = val[1:]
                if c in self.macros:
                    tokens[i + 1:i + 1] = tokenize(self.macros[c])
                    i += 1
                    continue
                if c == "relative":
                    raise ValueError("nested relative")
                if c == "time":
                    self.timesig = tokens[i + 1][1]
                    i += 2
                    continue
                if c == "key":
                    self.key = (tokens[i + 1][1], tokens[i + 2][1][1:])
                    i += 3
                    continue
                if c == "tempo":
                    j = i + 1
                    if tokens[j][0] == "str":
                        self.tempo_text = tokens[j][1].strip('"').rstrip(".")
                        j += 1
                    if j + 2 < len(tokens) and tokens[j + 1][0] == "eq":
                        self.tempo = (tokens[j][1], tokens[j + 2][1])
                        j += 3
                    i = j
                    continue
                if c == "partial":
                    m = re.match(r"(\d+)(\.*)", tokens[i + 1][1])
                    base = F(1, int(m.group(1)))
                    d, add = base, base
                    for _ in m.group(2):
                        add /= 2
                        d += add
                    self.partial = d
                    i += 2
                    continue
                if c == "bar":
                    i += 2
                    continue
                if c in ("override", "set"):
                    # \override X.y = #value
                    j = i + 1
                    while tokens[j][0] != "eq":
                        j += 1
                    i = j + 2
                    continue
                if c == "omit":
                    i += 2
                    continue
                if c == "repeat":
                    mode, count = tokens[i + 1][1], int(tokens[i + 2][1])
                    body, j = self.group(tokens, i + 3)
                    alts = []
                    if j < len(tokens) and tokens[j] == ("cmd", "\\alternative"):
                        alt_body, j = self.group(tokens, j + 1)
                        k = 0
                        while k < len(alt_body):
                            b, k = self.group(alt_body, k)
                            alts.append(b)
                    if mode == "volta":
                        self.voltas.append((self.time, count, len(alts)))
                    reps = count if mode in ("unfold", "percent") else 1
                    # the body is made relative once and then repeated as it is
                    start_ref = ref
                    for r in range(reps):
                        ref = self.run(list(body), start_ref)
                    if mode == "volta":
                        self.voltas[-1] = self.voltas[-1] + (self.time,)
                        for a in alts[:1]:
                            ref = self.run(list(a), ref)
                    i = j
                    continue
                if c == "tuplet":
                    num, den = map(int, tokens[i + 1][1].split("/"))
                    j = i + 2
                    if tokens[j][0] in ("dur", "num"):
                        j += 1
                    body, j = self.group(tokens, j)
                    saved = self.tuplet
                    self.tuplet = saved * F(den, num)
                    ref = self.run(list(body), ref)
                    self.tuplet = saved
                    i = j
                    continue
                if c == "new":
                    i += 2
                    continue
                i += 1
                continue
            if kind == "open" and val == "<<":
                # simultaneous: first branch is the melody unless a later branch says \voiceOne
                branches = []
                j = i + 1
                while tokens[j] != ("close", ">>"):
                    if tokens[j][0] == "cmd" and tokens[j][1] == "\\new":
                        j += 2
                        continue
                    b, j = self.group(tokens, j)
                    branches.append(b)
                j += 1
                melody = 0
                for bi, b in enumerate(branches):
                    if ("cmd", "\\voiceOne") in b:
                        melody = bi
                start = self.time
                melody_end = start
                for bi, b in enumerate(branches):
                    self.time = start
                    if bi == melody:
                        ref = self.run(list(b), ref)
                        melody_end = self.time
                    else:
                        sub = Converter(self.macros)
                        sub.time = start
                        sub.default_dur = self.default_dur
                        sub.voltas = []
                        ref = sub.run(list(b), ref)
                        for ev in sub.events:
                            if ev["pitch"] is not None:
                                self.second.append((ev["start"], ev["dur"], ev["pitch"]))
                            for p in ev.get("lower", []):
                                self.second.append((ev["start"], ev["dur"], p))
                        self.default_dur = sub.default_dur
                # The melody branch says where the music goes on; the others are its 2nd voice.
                self.time = melody_end
                i = j
                continue
            if kind == "open" and val == "<":
                # chord: pitches relative in turn, ref after = first pitch
                j = i + 1
                pitches = []
                cref = ref
                first_ref = None
                while tokens[j] != ("close", ">"):
                    k, v = tokens[j]
                    if k == "note":
                        p, _, cref = self.parse_note(v, cref)
                        pitches.append(p)
                        if first_ref is None:
                            first_ref = cref
                    j += 1
                j += 1
                d = self.default_dur
                if j < len(tokens) and tokens[j][0] == "dur":
                    m = re.match(r"(\d+)(\.*)(?:\*(\d+)(?:/(\d+))?)?", tokens[j][1])
                    base = F(1, int(m.group(1)))
                    d, add = base, base
                    for _ in m.group(2):
                        add /= 2
                        d += add
                    self.default_dur = d
                    if m.group(3):
                        d = d * F(int(m.group(3)), int(m.group(4) or 1))
                    j += 1
                ref = first_ref
                top = max(pitches, key=lambda p: p[2] * 7 + p[0] + p[1] / 10)
                lower = [p for p in pitches if p is not top]
                ev = {"pitch": top, "dur": d * self.tuplet, "start": self.time, "triplet": self.tuplet != 1,
                      "lower": lower, "finger": None}
                self.events.append(ev)
                self.time += ev["dur"]
                last_event = ev
                i = j
                continue
            if kind == "open" and val == "{":
                body, j = self.group(tokens, i)
                ref = self.run(list(body), ref)
                i = j
                continue
            if kind == "note":
                self.pending_trem = None
                p, d, ref2 = self.parse_note(val, ref)
                if p is not None:
                    ref = ref2
                if self.pending_trem:
                    # a tremolo eighth: the note repeated in shorter values, written out
                    for _ in range(int(d / self.pending_trem) - 1):
                        ev = {"pitch": p, "dur": self.pending_trem * self.tuplet, "start": self.time,
                              "triplet": self.tuplet != 1, "finger": None}
                        self.events.append(ev)
                        self.time += ev["dur"]
                    d = self.pending_trem
                ev = {"pitch": p, "dur": d * self.tuplet, "start": self.time, "triplet": self.tuplet != 1,
                      "finger": None, "spacer": val[0] == "s"}
                self.events.append(ev)
                self.time += ev["dur"]
                last_event = ev
                i += 1
                continue
            if kind == "dur":
                raise ValueError(f"stray duration {val} near {tokens[max(0, i-5):i+3]}")
            if kind == "tilde":
                if last_event is not None:
                    last_event["tie"] = True
                i += 1
                continue
            if kind == "bar":
                self.bars.append(self.time)
                i += 1
                continue
            if kind == "finger":
                if last_event is not None and last_event["finger"] is None:
                    last_event["finger"] = int(val[1])
                i += 1
                continue
            i += 1
        return ref

    def group(self, tokens, i):
        """Tokens inside the {...} starting at i, and the index after it."""
        assert tokens[i] == ("open", "{"), tokens[i:i + 5]
        depth = 0
        for j in range(i, len(tokens)):
            if tokens[j] == ("open", "{"):
                depth += 1
            elif tokens[j] == ("close", "}"):
                depth -= 1
                if depth == 0:
                    return tokens[i + 1:j], j + 1
        raise ValueError("unbalanced group")


def pitch_name(p):
    step, alter, octave = p
    acc = {0: "", 1: "#", -1: "b"}[alter]
    return f"{LETTER[step]}{acc}{octave + 3}"


def convert(text, n):
    roman = ROMAN[n]
    m = re.search(rf"^study{roman} = \\new Voice \\relative ([a-g](?:is|es)?[',]*) \{{", text, re.M)
    body, _ = block_after(text, m.start())
    start = m.group(1)
    sm = re.match(r"([a-g])(?:is|es)?([',]*)", start)
    ref = (STEP[sm.group(1)], sm.group(2).count("'") - sm.group(2).count(","))
    macros = {}
    for mm in re.finditer(r"^([A-Za-z]+) = \{([^}]*)\}", text, re.M):
        macros[mm.group(1)] = mm.group(2)
    conv = Converter(macros)
    conv.voltas = []
    conv.run(tokenize(strip_comments(body)), ref)
    return conv


def main():
    src, first, last = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    text = strip_comments(open(src, encoding="utf-8").read())
    out = {}
    for n in range(first, last + 1):
        c = convert(text, n)
        num, den = map(int, c.timesig.split("/"))
        bar_len = F(num, den)
        # Spacers (s) only hold time, so they leave no note behind.
        measures = []
        offset = (bar_len - c.partial) if c.partial else F(0)
        for e in c.events:
            if e.get("spacer"):
                continue
            idx = int((e["start"] + offset) // bar_len)
            while len(measures) <= idx:
                measures.append([])
            measures[idx].append(e)
        problems = []
        for b in c.bars:
            if ((b + offset) % bar_len) != 0:
                problems.append(f"bar check off at {b}")
        for e in c.events:
            pos = (e["start"] + offset) % bar_len
            if pos + e["dur"] > bar_len and not e.get("spacer"):
                problems.append(f"note crosses bar at {e['start']}")
        if problems:
            sys.exit(f"No. {n}: {'; '.join(problems)}")
        def enc(e):
            d = e["dur"] * 4
            return {
                "rest": e["pitch"] is None,
                "pitch": None if e["pitch"] is None else pitch_name(e["pitch"]),
                "beats": str(d),
                "tie": bool(e.get("tie")),
                "triplet": e["triplet"],
                "finger": e["finger"],
                "lower": [pitch_name(p) for p in e.get("lower", [])],
            }
        out[n] = {
            "time": c.timesig,
            "tempo": c.tempo,
            "tempo_text": c.tempo_text,
            "key": c.key,
            "partial": str(c.partial * 4) if c.partial else None,
            "voltas": [[str(a * 4), cnt, nalt, str(b * 4)] for a, cnt, nalt, b in c.voltas],
            "measures": [[enc(e) for e in m] for m in measures],
            "second": [[str(s * 4), str(d * 4), pitch_name(p)] for s, d, p in c.second],
        }
    json.dump(out, sys.stdout, indent=1)


main()
