import json
import base64
import io
import pandas as pd


def load_config(file_path: str) -> dict:
    """Load configuration file."""
    with open(file_path, "r") as f:
        return json.load(f)


def save_converted_csv(df, column_mappings):
    converted_df = df.rename(columns=dict(zip(df.columns, column_mappings)))
    converted_df.to_csv("converted.csv", index=False)


def parse_contents(contents: str, filename: str, separator: str) -> pd.DataFrame:
    """Parse file contents and return a DataFrame."""
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)

    try:
        if filename.endswith(".csv"):
            return pd.read_csv(io.StringIO(decoded.decode("utf-8")), sep=separator)
        else:
            raise ValueError("Invalid file format")
    except Exception as e:
        print(e)
        raise e


def generate_csv(df, column_mappings, separator):
    # Create a dictionary to store the new column names
    new_column_names = {}

    # Get only the mapped column names and remove any None values
    for expected_col, mapped_col in column_mappings.items():
        if mapped_col is not None:
            new_column_names[mapped_col] = expected_col

    # Rename the columns in the dataframe using the new_column_names dictionary
    new_df = df.rename(columns=new_column_names)

    # Keep only the columns that are in the new_column_names dictionary
    selected_columns = list(new_column_names.values())
    new_df = new_df[selected_columns]

    return new_df.to_csv(index=False, sep=",")  # Changed the separator to ","
