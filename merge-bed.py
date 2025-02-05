#!/usr/bin/env python3

import pandas as pd
import argparse


def load_bed_as_dataframe(bed_path):
    """
    Load a BED file into a pandas DataFrame.

    params:
        bed_path: str
            Path to the input BED file.

    returns:
        pd.DataFrame
            A DataFrame containing the BED file contents.
    """
    # Load the BED file into a DataFrame
    bed_columns = ["seqname", "start", "end", "ID"]
    bed_df = pd.read_csv(
        bed_path,
        sep="\t",
        header=None,
        names=bed_columns + [f"extra_col_{i}" for i in range(4, 100)],
        engine="python",
    )
    return bed_df


def merge_bed_features(bed_df, distance_threshold):
    """
    Merge features in a BED DataFrame if they are within a specified distance.

    params:
        bed_df: pd.DataFrame
            A DataFrame containing BED file contents.
        distance_threshold: int
            Maximum distance between features to merge them.

    returns:
        pd.DataFrame
            A DataFrame with merged features.
    """
    # Sort the BED file by seqname and start position
    bed_df = bed_df.sort_values(by=["seqname", "start"]).reset_index(drop=True)

    merged_records = []
    current_record = bed_df.iloc[0].to_dict()

    for _, next_record in bed_df.iloc[1:].iterrows():
        # Check if the next feature is within the distance threshold
        if (
            current_record["seqname"] == next_record["seqname"]
            and next_record["start"] - current_record["end"] <= distance_threshold
        ):
            # Merge the features by extending the current feature's end position
            current_record["end"] = max(current_record["end"], next_record["end"])
            current_record["ID"] += f",{next_record['ID']}"  # Concatenate IDs

            # Concatenate any extra columns
            for col in bed_df.columns[4:]:
                if pd.notna(next_record[col]):
                    if pd.isna(current_record[col]):
                        current_record[col] = next_record[col]
                    else:
                        current_record[col] += f",{next_record[col]}"
        else:
            # Add the current record to the merged list and move to the next
            merged_records.append(current_record)
            current_record = next_record.to_dict()

    # Add the last record
    merged_records.append(current_record)

    # Convert the merged records back to a DataFrame
    merged_bed_df = pd.DataFrame(merged_records)

    return merged_bed_df


def save_bed_from_dataframe(bed_df, output_path):
    """
    Save a BED DataFrame to a file.

    params:
        bed_df: pd.DataFrame
            A DataFrame containing BED file contents.
        output_path: str
            Path to the output BED file.

    returns:
        None
    """
    bed_df.to_csv(output_path, sep="\t", header=False, index=False)


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Merge features in a BED file if they are within a specified distance."
    )
    parser.add_argument(
        "input_bed", type=str, help="Path to the input BED file."
    )
    parser.add_argument(
        "output_bed", type=str, help="Path to the output BED file."
    )
    parser.add_argument(
        "-d",
        "--distance",
        type=int,
        default=0,
        help="Maximum distance between features to merge them (default: 0).",
    )
    args = parser.parse_args()

    # Load the input BED file
    bed_df = load_bed_as_dataframe(args.input_bed)

    # Merge features
    merged_bed_df = merge_bed_features(bed_df, args.distance)

    # Save the merged BED file
    save_bed_from_dataframe(merged_bed_df, args.output_bed)


if __name__ == "__main__":
    main()
