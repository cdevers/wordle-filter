# wordle-filter

Command-line tools for filtering Wordle candidates and ranking them by
likelihood, using positional letter frequency and English word commonality.

## Tools

### `wdl-filter`

The main tool. Takes your guesses and their results, filters the word list
down to remaining candidates, and ranks them by a composite score of
positional letter frequency × word commonality.

### `wordle_freq_annotator.py`

One-time setup script. Downloads Peter Norvig's word frequency corpus and
annotates `wordle-words.txt` with log-scaled frequency scores, producing
`wordle-freq-full.txt`. Run this once before first use (see Setup below).

## Setup

**Requirements:** Python 3, internet access for the one-time corpus download.

```bash
make setup
```

This downloads ~30 MB from `norvig.com` and generates `wordle-freq-full.txt`
alongside `wordle-words.txt`. It only needs to be run once.

By default, `wdl-filter` looks for its data files in `~/`:

| File | Default path | Purpose |
|------|-------------|---------|
| Word list | `~/wordle-words.txt` | All valid Wordle words |
| Frequency data | `~/wordle-freq-full.txt` | Log-scaled word frequencies |

You can override either path with environment variables:

```bash
export WORDLE_WORDLIST=~/wordle/wordle-words.txt
export FREQ_FILE=~/wordle/wordle-freq-full.txt
```

Add these to your `.zshrc` / `.bashrc` to make them permanent. Alternatively,
copy both files to `~/` and skip the environment variables entirely.

**Install the script:**

```bash
make install       # copies wdl-filter to ~/bin/
```

Make sure `~/bin` is on your `PATH`.

## Usage

### Guess mode (recommended)

Pass your guesses directly as `WORD:RESULT` arguments. Result codes:

| Code | Meaning |
|------|---------|
| `g` | **Green** — correct letter, correct position |
| `y` | **Yellow** — correct letter, wrong position |
| `_` | **Grey** — letter not in answer |
| `x` | **Grey, duplicate** — letter is present but this instance is surplus; the answer has exactly as many of this letter as the `g`/`y` hits account for |

```bash
# After one guess
wdl-filter slate:_____

# After two guesses
wdl-filter slate:_____ crony:____g

# After three guesses
wdl-filter slate:_____ crony:____g bumpy:____g

# Track a specific word's rank even if it's outside the top 30
wdl-filter slate:_____ --show-word dizzy
```

### Pipeline mode (original)

The tool also works as a filter in a grep pipeline, for cases where you want
to experiment with custom letter constraints:

```bash
sort wordle-words.txt | grep "..a.." | egrep -v '[sle]' | wdl-filter

# Pipeline and guess args can be combined
grep ".e..." wordle-words.txt | wdl-filter slate:g___y
```

### Example session

Today's word was `dizzy`. Starting from `slate` (all grey), then `crony`
(y green at end):

```
$ wdl-filter slate:_____ crony:____g
Guesses:
  slate  _____
  crony  ____g

matching words: 85
...
# Top 30 words (by composite score = match x freq^2):
    buddy ( 47.45, 0.5222)    jimmy ( 34.46, 0.4809)    puppy ( 33.59, 0.4344) ...
    dizzy ( 15.65, 0.3274) ...

$ wdl-filter slate:_____ crony:____g bumpy:____g giddy:_gy_g
Guesses:
  ...

matching words: 2
    dizzy (  2.62, 0.3274)    divvy (  0.53, 0.0665)
```

## How scoring works

Each candidate word gets a **composite score**:

```
composite = match_score × freq ^ k
```

- **`match_score`** — sum of positional letter frequencies across all 5
  positions. A word whose letters are common at their specific positions
  scores higher.
- **`freq`** — log-scaled word frequency from the Norvig corpus (0.0001
  floor for words absent from the corpus).
- **`k`** — dynamic exponent that scales with candidate pool size:

  | Candidates | k | Effect |
  |---|---|---|
  | > 100 | 3 | Floor words collapse to ~0; common words dominate |
  | 30–100 | 2 | Strong frequency penalty |
  | 10–30 | 1.5 | Moderate penalty |
  | ≤ 10 | 1 | Positional fit starts to differentiate floor words |

  This means early in the game, obscure words are suppressed heavily in
  favour of likely answers. As the field narrows, positional fit becomes
  the primary signal.

## Files

```
wordle-words.txt          All valid Wordle guesses (~15k words)
wordle-freq-full.txt      Generated: log-scaled frequency scores (gitignored)
wdl-filter                Main filter script (Python 3)
wordle_freq_annotator.py  One-time setup: builds wordle-freq-full.txt
Makefile                  setup, install, help targets
`index.html`              Web interface — runs entirely in the browser, no server needed

```
## Web interface

A browser-based version is available at **https://cdevers.github.io/wdl** —
useful when you're away from the command line (phone, tablet, etc.).

**`index.html`** at the repo root is the single-file web app. It loads the
word list and frequency data directly from this repo at runtime, so no build
step or server is needed. Just open the URL.

Features:
- Tap tiles to cycle through green / yellow / grey / duplicate states
- Tap any word in the results list to fill it into the input automatically
- Candidate count shown after each guess, narrowing as you add more
- Share button encodes your current session in the URL
- Undo button (🗑️) on the last guess row to roll back a mistake

## License

MIT
