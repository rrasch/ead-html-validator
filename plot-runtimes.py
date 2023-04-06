#!/usr/bin/env python3

import argparse
import pandas as pd
import matplotlib.pyplot as plt


def prepend_text(prefix, text_list):
    return [prefix + text for text in text_list]


def plot_runtimes(df):
    labels = ["no parallelization", "multi-process", "multi-threads"]
    runtime_cols = prepend_text("duration ", labels)
    retval_cols = prepend_text("exit code ", labels)
    # reduce dataframe to only rows where exit code is 0
    # for every form of parallelization
    df = df[df[retval_cols].eq(0).all(axis=1)]
    df.plot(y=runtime_cols, use_index=True)
    plt.show()


def main():
    pd.set_option(
        "display.max_columns",
        None,
        "display.max_rows",
        None,
        "display.width",
        0,
    )

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Plot line graph of data from runtimes csv.",
    )
    parser.add_argument("csv_file", help="Input CSV file")
    args = parser.parse_args()

    df = pd.read_csv(args.csv_file)

    plot_runtimes(df)


if __name__ == "__main__":
    main()
