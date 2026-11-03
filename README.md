# Violin School

A practice companion for beginner violinists, in the browser.

**Open the app: https://mkdubik.github.io/violin-school/**

## What's in it

- **Tuner** – reference tones for the G, D, A and E strings (A = 440 Hz), one at a time or all in turn. Listen mode uses the microphone to show whether a string is in tune and which way to turn the peg. With Automatic ticked it starts on the G string and moves on to D, A and E by itself, each once it has stayed in tune for a moment, and marks the strings it has done.
- **Rhythms** – the beginner rhythms with their Icelandic syllables (Kópavogur hoppstopp, Hann fer – Hún fer, Fá epli, Banani, Apríkósa), looped at an adjustable tempo with the current syllable highlighted, after a start delay that counts down (3 s by default).
- **Notes** – sheet music for the Suzuki Violin School Vol 1 pieces (the Twinkle variations and theme, Lightly Row, Song of the Wind, Go Tell Aunt Rhody, O Come, Little Children, May Song, Long, Long Ago, the three Bach minuets, The Happy Farmer and Gossec's Gavotte), with Rússakeisari in a second songbook and a third, Heartstrings, of pieces that move an audience: Ode to Joy, Shenandoah, Danny Boy, Pachelbel's Canon, I Vow to Thee, My Country, The Star-Spangled Banner, Lofsöngur, Schumann's Träumerei and Schubert's Ave Maria, a fourth, Jól, of Christmas songs for December concerts: Heims um ból (Silent Night), Jingle Bells, Deck the Halls, We Wish You a Merry Christmas and Good King Wenceslas, a fifth, Íslensk lög, of Icelandic songs, so far the folk lullaby Sofðu, unga ástin mín (in A minor), and a sixth, Scales, of A, D and G major scales and arpeggios, one octave and two where they fit, all in first position. Suzuki's own pieces (Allegro, Perpetual Motion, Allegretto, Andantino, Etude) are still under copyright and not included. Each piece opens at its full tempo (marked ♩ = … above the first bar and shown beside the Tempo slider, e.g. 72 / 104). Play along with the highlighted notes, slow it down, add a start delay, and turn the melody, the piano, a 2nd violin and, under the scales, a drone of the key note and its 5th on or off. Every piece with piano chords has a 2nd violin part made from them (chord notes a 3rd or 6th under the melody, in first position), so you can play the melody as a duet with it. Loop practises a passage: tap its first and last note, and Play repeats those bars until Stop, at the piece's own speeds there, waiting the start delay (with its countdown) before each time round. Letting go of the Tempo slider while anything plays changes the speed at once. Tap any note to hear it, see which finger and string it is on, and use listen mode to check your own pitch.
- **Learn** – reading sheet music step by step: the notes on the staff and where they sit on the violin, note values and rests, the signs on the page, intervals from a half step to an octave with a violin example of each, the two finger patterns (high 2 and low 2) on each string, and quizzes for naming notes, playing them, finding them on the fingerboard, recognising rhythms, reading signs, hearing intervals and naming a piece from how it begins. Progress is saved in the browser.
- **Metronome** – a steady click from 30 to 208 BPM with the tempo marking shown, 1 to 6 beats per bar with the first beat accented, optional eighth, triplet or sixteenth clicks, and tap tempo. Space starts and stops it.
- **Accelerator** – an hour a day, half in the morning and half in the evening, and a record of it kept in your own browser. Today's hour lists its blocks (a cold try, tone, scales, the new piece, an étude, review, sight-reading, theory) to tick off, each with a timer that rings at the end. A streak and the week show which days had practice, counted while a sound, the mic or a timer is on. Hard spots come from Notes: Loop a passage and tap Hard spot, and it starts slow and goes up 4 bpm after 3 clean runs in a row until it is at full tempo. The next morning the latest one comes back as the cold try, played once before warming up. The review rotation picks hard spots and pieces not touched for longest, to switch between a couple of minutes each. Listening minutes count the recordings you listen to outside the hour. Milestones run from a start date to framhaldspróf, each with a target date you can change; moving the start date moves the ones not yet reached. Under each piece in its songbook is when you last played it and the fastest tempo. Export saves the record as a file and Import brings it back.

## Running it locally

The whole app is one file, `index.html`, with no build step or dependencies. Open it in a browser, or serve the folder so the microphone works:

```bash
python3 -m http.server 8000
```

Then go to http://localhost:8000.

## Adding pieces

Pieces are defined in `PIECES` in `index.html` and listed in a songbook in `COLLECTIONS`. A piece is a list of measures written with small helpers, for example `e("A4")` for an eighth note and `h("E5")` for a half note; the comments above `PIECES` describe the notation, piano chords and tempo marks.

Songbooks you want to keep to yourself can go in `local/songbooks.js`, which the app loads when it exists and git ignores. Play-along recordings of the rhythms can go in `local/recordings.js`, with their audio files under `local/`: they get a Recordings subtab in Rhythms that highlights each syllable as the recording plays it, says which string and finger, rests while the piano answers, and slows down with the Tempo slider without changing pitch. Each phrase lists the times its syllables start in the recording; the comment at the top of the file describes the format. Anything else meant only for this computer can go in `local/extras.js`, which runs after the app when it exists.
