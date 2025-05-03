from datetime import date
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import os


# Function to append data to a Parquet file
def append_to_parquet(data, filename):
    filename = filename + ".parquet"
    df = pd.DataFrame(data)

    # Convert to PyArrow Table
    table = pa.Table.from_pandas(df)

    # Open Parquet file in append mode
    try:
        with pq.ParquetWriter(filename, table.schema, compression="snappy") as writer:
            writer.write_table(table)
    except Exception as e:
        print(f"Error appending data: {e}")

def consolidate_files(folder_path, tipo):
    # List all parquet files starting with "ABC"
    parquet_files = [
        f for f in os.listdir(folder_path) if tipo in f and f.endswith(".parquet")
    ]

    if not parquet_files:
        print("No matching Parquet files found.")
        return

    # Read all parquet files into a single dataframe
    df_list = [
        pq.read_table(os.path.join(folder_path, file)).to_pandas()
        for file in parquet_files
    ]
    consolidated_df = pd.concat(df_list, ignore_index=True)

    # Save the merged dataframe to a new parquet file
    output_file = (
        folder_path + "/" + tipo + "_Consolidado_" + str(date.today()) + ".parquet"
    )
    consolidated_df.to_parquet(output_file, engine="pyarrow")

    print(f"Successfully consolidated {len(parquet_files)} files into {output_file}")

    for file in parquet_files:
        os.remove(os.path.join(folder_path, file))
