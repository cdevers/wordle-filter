#!/usr/bin/env python3
"""
Annotate Wordle word list with frequency data from Peter Norvig's n-gram corpus.

Source: https://norvig.com/ngrams/count_1w.txt
  ~330,000 English words with raw occurrence counts from a large web corpus.
  Far broader coverage than the Google 10k list, and gives meaningful scores
  to common-but-not-top-10k words like 'attic', 'tacit', 'taunt', etc.

Scoring: log-scaled normalization.
  Raw word frequencies follow a Zipf distribution — 'the' is millions of times
  more common than 'attic'. Linear scaling would compress everything below the
  top ~100 words into near-zero noise. Log scaling preserves meaningful
  differentiation across the full range.

  score = (log(count) - log(min_count)) / (log(max_count) - log(min_count))

  Result: scores in [0.0, 1.0] with comfortable separation between tiers.
  Words absent from the corpus get 0.0001 (genuine floor — obscure or invented).
"""

import sys
import math
import urllib.request


NORVIG_URL = "https://norvig.com/ngrams/count_1w.txt"
FLOOR_SCORE = 0.0001


def fetch_norvig_counts():
    """Fetch Norvig's word frequency list (word<TAB>count per line)."""
    print(f"Fetching frequency data from {NORVIG_URL} ...", file=sys.stderr)
    print("(~30 MB download, may take a moment)", file=sys.stderr)
    try:
        with urllib.request.urlopen(NORVIG_URL, timeout=60) as response:
            data = response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching Norvig corpus: {e}", file=sys.stderr)
        sys.exit(1)

    counts = {}
    for line in data.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) == 2:
            word, count_str = parts
            try:
                counts[word.lower()] = int(count_str)
            except ValueError:
                pass

    print(f"Loaded {len(counts):,} words from Norvig corpus", file=sys.stderr)
    return counts


def build_log_scores(counts):
    """
    Convert raw counts to log-scaled scores in [FLOOR_SCORE, 1.0].

    We use the full corpus min/max so the scale is consistent regardless of
    which words end up being queried. This means the top score (1.0) belongs
    to the single most common word in the whole corpus ('the'), and all other
    words are placed relative to that.
    """
    if not counts:
        return {}

    log_counts = {w: math.log(c) for w, c in counts.items() if c > 0}
    log_min = min(log_counts.values())
    log_max = max(log_counts.values())
    span = log_max - log_min

    if span == 0:
        return {w: 1.0 for w in log_counts}

    scores = {}
    for word, lc in log_counts.items():
        scores[word] = (lc - log_min) / span

    return scores


def annotate_wordle_list(wordle_file, freq_scores):
    """Read the Wordle word list and attach frequency scores."""
    print(f"Reading Wordle word list from {wordle_file} ...", file=sys.stderr)

    annotated = []
    five_letter_count = 0
    found_in_corpus = 0

    with open(wordle_file, 'r') as f:
        for line in f:
            word = line.strip().lower()
            if not word:
                continue
            is_five = len(word) == 5
            if is_five:
                five_letter_count += 1
            score = freq_scores.get(word, FLOOR_SCORE)
            if is_five and score > FLOOR_SCORE:
                found_in_corpus += 1
            annotated.append((word, score))

    coverage = found_in_corpus / five_letter_count * 100 if five_letter_count else 0
    print(f"Processed {five_letter_count:,} five-letter words", file=sys.stderr)
    print(f"Found in corpus: {found_in_corpus:,} ({coverage:.1f}%)", file=sys.stderr)
    not_found = five_letter_count - found_in_corpus
    print(f"Floor (not in corpus): {not_found:,} ({100-coverage:.1f}%)", file=sys.stderr)

    return annotated, five_letter_count, found_in_corpus


def print_score_distribution(annotated):
    """Print score tier breakdown for the 5-letter words."""
    five = [(w, s) for w, s in annotated if len(w) == 5]
    brackets = [
        (0.8, 1.01, ">0.8  (very common)"),
        (0.6, 0.8,  "0.6-0.8"),
        (0.4, 0.6,  "0.4-0.6"),
        (0.2, 0.4,  "0.2-0.4"),
        (0.05, 0.2, "0.05-0.2"),
        (0.001, 0.05, "0.001-0.05"),
        (FLOOR_SCORE, 0.001, f"0.001-{FLOOR_SCORE} (near-floor)"),
        (0, FLOOR_SCORE + 1e-9, f"={FLOOR_SCORE} (floor / not in corpus)"),
    ]
    print("\nScore distribution (5-letter words):", file=sys.stderr)
    for lo, hi, label in brackets:
        n = sum(1 for _, s in five if lo <= s < hi)
        print(f"  {label}: {n:,}", file=sys.stderr)

    # Spot-check some words users might care about
    check = ['attic', 'tacit', 'taunt', 'taint', 'civic', 'panic', 'topic',
             'magic', 'watch', 'today', 'match', 'yacht', 'takht', 'tatou']
    score_dict = dict(five)
    print("\nSpot-check scores:", file=sys.stderr)
    for w in check:
        s = score_dict.get(w)
        if s is not None:
            print(f"  {w}: {s:.6f}", file=sys.stderr)


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 wordle_freq_annotator.py <wordle.txt> <output.txt>",
              file=sys.stderr)
        print("\nExample:", file=sys.stderr)
        print("  python3 wordle_freq_annotator.py wordle-words.txt wordle-freq-full.txt",
              file=sys.stderr)
        sys.exit(1)

    wordle_file = sys.argv[1]
    output_file = sys.argv[2]

    # Fetch and score
    counts = fetch_norvig_counts()
    print("Computing log-scaled scores ...", file=sys.stderr)
    freq_scores = build_log_scores(counts)

    # Annotate
    annotated, n_five, n_found = annotate_wordle_list(wordle_file, freq_scores)

    # Sort alphabetically to preserve grep-friendliness
    annotated.sort(key=lambda x: x[0])

    # Write output — 6 decimal places instead of 4, to expose differentiation
    # in the 0.0001–0.01 tier that previously all rounded to 0.0001
    print(f"\nWriting annotated list to {output_file} ...", file=sys.stderr)
    with open(output_file, 'w') as f:
        for word, score in annotated:
            f.write(f"{word} {score:.6f}\n")

    print(f"\nDone. Format: <word> <log-scaled frequency score>", file=sys.stderr)
    print(f"  1.000000 = 'the' (most frequent word in corpus)", file=sys.stderr)
    print(f"  0.000100 = not in corpus (genuine floor)", file=sys.stderr)
    print(f"  6 decimal places expose differentiation in the rare-word tier", file=sys.stderr)

    print_score_distribution(annotated)


if __name__ == "__main__":
    main()
