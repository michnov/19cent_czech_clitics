#!/usr/bin/env python3
"""Evaluation script: compares gold labels with predicted labels and reports scores."""

import argparse
import sys

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluate predicted labels against gold labels."
    )
    parser.add_argument("gold", help="Path to the file with gold labels (one per line).")
    parser.add_argument("predicted", help="Path to the file with predicted labels (one per line).")
    parser.add_argument(
        "--skip-gold",
        type=int,
        default=0,
        metavar="N",
        help="Number of lines to skip at the beginning of the gold file (default: 0).",
    )
    parser.add_argument(
        "--skip-predicted",
        type=int,
        default=0,
        metavar="N",
        help="Number of lines to skip at the beginning of the predicted file (default: 0).",
    )
    return parser.parse_args()


def read_labels(path, skip):
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    return [line.rstrip("\n") for line in lines[skip:]]


def main():
    args = parse_args()

    gold = read_labels(args.gold, args.skip_gold)
    predicted = read_labels(args.predicted, args.skip_predicted)

    if len(gold) != len(predicted):
        print(
            f"Error: after skipping lines, gold has {len(gold)} entries but "
            f"predicted has {len(predicted)} entries.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Filter out examples where the gold label is empty
    pairs = [(g, p) for g, p in zip(gold, predicted) if g != ""]
    filtered_gold = [g for g, _ in pairs]
    filtered_predicted = [p for _, p in pairs]

    if not filtered_gold:
        print("Error: no examples remain after filtering empty gold labels.", file=sys.stderr)
        sys.exit(1)

    print(f"Evaluating {len(filtered_gold)} examples "
          f"({len(gold) - len(filtered_gold)} skipped due to empty gold labels).\n")

    print("Accuracy:", accuracy_score(filtered_gold, filtered_predicted))
    print()
    print("Classification report:")
    print(classification_report(filtered_gold, filtered_predicted))
    print("Confusion matrix:")
    print(confusion_matrix(filtered_gold, filtered_predicted))


if __name__ == "__main__":
    main()
