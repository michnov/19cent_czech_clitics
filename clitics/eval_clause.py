"""Evaluate predicted clause types (HV/VV) against gold annotations.

Both files are TSV with a header row.  Data rows are counted from 1 (the
header does not count).  Rows whose 1-based numbers appear in --skip-gold /
--skip-pred are removed *before* alignment, so the two resulting lists must
have the same length.
"""
import argparse
import csv
import sys
from collections import Counter


def load_col(path, skip_rows, col):
    """Return a list of values from *col* in *path*, skipping 1-based rows.

    *col* is a column name (matched against the header) or a 0-based integer
    index.
    """
    values = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh, delimiter="\t")
        header = next(reader)
        if isinstance(col, str):
            if col not in header:
                sys.exit(f"Column '{col}' not found in {path}. Available: {header}")
            col_idx = header.index(col)
        else:
            col_idx = col
        for row_num, row in enumerate(reader, 1):
            if row_num in skip_rows:
                continue
            values.append(row[col_idx].strip() if col_idx < len(row) else "")
    return values


def evaluate(gold, pred):
    """Print accuracy, confusion matrix and per-class P/R/F1."""
    if len(gold) != len(pred):
        sys.exit(
            f"Row count mismatch after filtering: gold={len(gold)}, pred={len(pred)}. "
            "Check --skip-gold / --skip-pred."
        )
    classes = sorted(set(gold) | set(pred))
    total = len(gold)
    correct = sum(g == p for g, p in zip(gold, pred))

    print(f"Total pairs: {total}")
    print(f"Correct:     {correct}")
    if total:
        print(f"Accuracy:    {correct / total:.4f}")
    else:
        print("Accuracy:    N/A")

    confusion = Counter((g, p) for g, p in zip(gold, pred))

    print("\nConfusion matrix (rows=gold, cols=pred):")
    header_row = "\t".join([""] + classes)
    print(header_row)
    for g_cls in classes:
        cells = [str(confusion.get((g_cls, p_cls), 0)) for p_cls in classes]
        print("\t".join([g_cls] + cells))

    print("\nPer-class metrics:")
    for cls in classes:
        tp = confusion.get((cls, cls), 0)
        fp = sum(confusion.get((g, cls), 0) for g in classes if g != cls)
        fn = sum(confusion.get((cls, p), 0) for p in classes if p != cls)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        print(f"  {cls}:  P={prec:.4f}  R={rec:.4f}  F1={f1:.4f}")


def parse_skip(spec):
    """Parse a comma-separated list of integers into a set."""
    return {int(x) for x in spec.split(",") if x.strip()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gold", help="Gold TSV file (with header)")
    parser.add_argument("pred", help="Predicted features TSV file (with header)")
    parser.add_argument(
        "--gold-col",
        default="clause_type",
        help="Column name or 0-based index for the clause type in the gold file "
             "(default: 'clause_type')",
    )
    parser.add_argument(
        "--pred-col",
        default="clause_type",
        help="Column name or 0-based index for the clause type in the pred file "
             "(default: 'clause_type')",
    )
    parser.add_argument(
        "--skip-gold",
        default="",
        help="Comma-separated 1-based data row numbers to skip in the gold file",
    )
    parser.add_argument(
        "--skip-pred",
        default="",
        help="Comma-separated 1-based data row numbers to skip in the pred file",
    )
    args = parser.parse_args()

    skip_gold = parse_skip(args.skip_gold)
    skip_pred = parse_skip(args.skip_pred)

    try:
        gold_col = int(args.gold_col)
    except ValueError:
        gold_col = args.gold_col

    try:
        pred_col = int(args.pred_col)
    except ValueError:
        pred_col = args.pred_col

    gold_vals = load_col(args.gold, skip_gold, gold_col)
    pred_vals = load_col(args.pred, skip_pred, pred_col)

    evaluate(gold_vals, pred_vals)


if __name__ == "__main__":
    main()
