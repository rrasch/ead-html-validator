#!/usr/bin/env python3

import argparse
import datetime
import pandas as pd
import matplotlib.pyplot as plt


def prepend_text(prefix, text_list):
    return [prefix + text for text in text_list]


def plot_runtimes(df):
    labels = ["no parallelization", "multi-process", "multi-threads"]

    duration_cols = prepend_text("duration ", labels)
    runtime_cols = prepend_text("runtime ", labels)
    retval_cols = prepend_text("exit code ", labels)

    # df[runtime_cols] = df[duration_cols].apply(pd.to_timedelta, unit="S")
    df[runtime_cols] = df[duration_cols] / 3600

    cmap = plt.get_cmap("Paired")

    # ax = df[runtime_cols].sum().plot.bar(rot=0, color=["C0", "C1", "C2"])
    ax = (
        df[runtime_cols]
        .sum()
        .plot.bar(figsize=(10, 6), rot=0, color=cmap.colors)
    )

    ax.bar_label(ax.containers[0], fmt="%.2f hours", label_type="edge")
    ax.set_title("Total Runtimes for EAD HTML Validator")
    ax.set_xlabel("parallelization method (8 CPUs)")
    ax.set_ylabel("runtime (hours)")
    ax.set_xticklabels(labels)

    df[runtime_cols] = df[duration_cols] / 60

    # # reduce dataframe to only rows where exit code is 0
    # for every form of parallelization
    # df = df[df[retval_cols].eq(0).all(axis=1)]

    # df = df[(df[duration_cols[0]] >= 300)]
    df = df[(df[duration_cols[0]] >= 300) & (df[duration_cols[0]] < 5000)]
    df = df.sort_values(duration_cols[0]).reset_index(drop=True)

    idx_max_value = df[runtime_cols[1]].idxmax()

    ax = df.plot(y=runtime_cols, use_index=True, figsize=(10, 6), rot=90)
    ax.set_title("Individual EAD HTML Validator Runtimes Longer Than 5 Minutes")
    ax.set_xlabel("EADs (sorted by no parallelization runtime)")
    ax.set_ylabel("runtime (minutes)")
    ax.set_xticks(ticks=range(len(df)), labels=df["collection"])
    ax.annotate(
        df.loc[idx_max_value, "collection"],
        (idx_max_value, df.loc[idx_max_value, runtime_cols[1]]),
        xytext=(15, 0),
        textcoords="offset points",
        arrowprops=dict(arrowstyle="-|>"),
    )

    # plt.hist(df[duration_cols[0]])

    plt.tight_layout()

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
    parser.add_argument("ccount_file")
    args = parser.parse_args()

    df = pd.read_csv(args.csv_file)
    print(df.shape)

    # Drop the last row if it contains NaN values
    if df.iloc[-1].isna().any():
        print("Dropping last row.")
        df = df.iloc[:-1]

    ccount = pd.read_csv(args.ccount_file)
    print(ccount.shape)

    df = df.merge(ccount, on=["partner", "collection"])
    print(df.shape)

    plot_runtimes(df)


if __name__ == "__main__":
    main()
