# Violin School

A practice companion for beginner violinists, in the browser.

**Open the app: https://mkdubik.github.io/violin-school/**

## What's in it

- **Tuner** – reference tones for the G, D, A and E strings (A = 440 Hz), one at a time or all in turn. Listen mode uses the microphone to show whether a string is in tune and which way to turn the peg.
- **Rhythms** – the beginner rhythms with their Icelandic syllables (Kópavogur hoppstopp, Hann fer – Hún fer, Fá epli, Banani, Apríkósa), looped at an adjustable tempo with the current syllable highlighted. Each rhythm also comes with piano accompaniment on the open E string.
- **Notes** – sheet music for the Suzuki Violin School Vol 1 pieces (the Twinkle variations and theme, Lightly Row, Song of the Wind, Go Tell Aunt Rhody, O Come, Little Children, May Song, Long, Long Ago, the three Bach minuets, The Happy Farmer and Gossec's Gavotte), with Rússakeisari in a second songbook and a third, Heartstrings, of pieces that move an audience: Ode to Joy, Shenandoah, Danny Boy, Pachelbel's Canon, I Vow to Thee, My Country, Lofsöngur, Schumann's Träumerei and Schubert's Ave Maria, all in first position. Suzuki's own pieces (Allegro, Perpetual Motion, Allegretto, Andantino, Etude) are still under copyright and not included. Each piece opens at its full tempo (marked ♩ = … above the first bar and shown beside the Tempo slider, e.g. 72 / 104). Play along with the highlighted notes, slow it down, add a start delay, and choose melody, piano or both. A bar of clicks counts you in (two bars in 2/4, and a pickup comes in on its beat), or the click can go on under every beat. Tap any note to hear it, see which finger and string it is on, and use listen mode to check your own pitch.
- **Learn** – reading sheet music step by step: the notes on the staff and where they sit on the violin, note values and rests, the signs on the page, intervals from a half step to an octave with a violin example of each, and quizzes for naming notes, playing them, recognising rhythms, reading signs and hearing intervals. Progress is saved in the browser.
- **Metronome** – a steady click from 30 to 208 BPM with the tempo marking shown, 1 to 6 beats per bar with the first beat accented, optional eighth, triplet or sixteenth clicks, and tap tempo. Space starts and stops it.

## Running it locally

The whole app is one file, `index.html`, with no build step or dependencies. Open it in a browser, or serve the folder so the microphone works:

```bash
python3 -m http.server 8000
```

Then go to http://localhost:8000.

## Adding pieces

Pieces are defined in `PIECES` in `index.html` and listed in a songbook in `COLLECTIONS`. A piece is a list of measures written with small helpers, for example `e("A4")` for an eighth note and `h("E5")` for a half note; the comments above `PIECES` describe the notation, piano chords and tempo marks.

Songbooks you want to keep to yourself can go in `local/songbooks.js`, which the app loads when it exists and git ignores.
