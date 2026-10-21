# Violin School

A practice companion for beginner violinists, in the browser.

**Open the app: https://mkdubik.github.io/violin-school/**

## What's in it

- **Tuner** – reference tones for the G, D, A and E strings (A = 440 Hz), one at a time or all in turn. Listen mode uses the microphone to show whether a string is in tune and which way to turn the peg.
- **Rhythms** – the beginner rhythms with their Icelandic syllables (Kópavogur hoppstopp, Hann fer – Hún fer, Fá epli, Banani, Apríkósa), looped at an adjustable tempo with the current syllable highlighted. Each rhythm also comes with piano accompaniment on the open E string.
- **Notes** – sheet music for beginner pieces (Twinkle, Twinkle, Little Star; Lightly Row; Song of the Wind; Rússakeisari). Play along with the highlighted notes, change the tempo, add a start delay, and choose melody, piano or both. Tap any note to hear it, see which finger and string it is on, and use listen mode to check your own pitch.
- **Learn** – reading sheet music step by step: the notes on the staff and where they sit on the violin, note values and rests, the signs on the page, and quizzes for naming notes, playing them, recognising rhythms and reading signs. Progress is saved in the browser.

## Running it locally

The whole app is one file, `index.html`, with no build step or dependencies. Open it in a browser, or serve the folder so the microphone works:

```bash
python3 -m http.server 8000
```

Then go to http://localhost:8000.

## Adding pieces

Pieces are defined in `PIECES` in `index.html` and listed in a songbook in `COLLECTIONS`. A piece is a list of measures written with small helpers, for example `e("A4")` for an eighth note and `h("E5")` for a half note; the comments above `PIECES` describe the notation, piano chords and tempo marks.

Songbooks you want to keep to yourself can go in `local/songbooks.js`, which the app loads when it exists and git ignores.
