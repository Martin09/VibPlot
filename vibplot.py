import logging
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def string_to_timedelta(s: str) -> timedelta:
    """Converts a string to a timedelta object"""
    hours, minutes, seconds = map(int, s.split(':'))
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)


def to_datetime(row: pd.Series) -> datetime:
    """Converts a Pandas Dataframe row with columns "Date" and "Time" and returns a datetime object"""
    dt_str = row['Date'] + ' ' + row['Time']
    return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')


def create_vibplot_html(data: pd.DataFrame, file_path: Path):
    """Takes a DataFrame containing a time-indexed data of vibration intensity at different frequencies and plots this
    2D data using plotly. Outputting a html file."""

    # Extract the frequencies and times from the data
    frequencies = data.columns.values
    times = data.index
    amplitudes = data.values.T

    # Create the Heatmap trace
    trace = go.Heatmap(
        x=times,
        y=frequencies,
        z=amplitudes,
        colorscale='Viridis',
        zmin=np.percentile(data, 1),
        zmax=np.percentile(data, 99),
        colorbar=dict(title='Amplitude')
    )

    # Create the figure and plot the spectrogram
    fig = go.Figure(data=[trace])

    fig.update_layout(
        xaxis=dict(title='Time'),
        yaxis=dict(title='Frequency (Hz)', type='log'),
    )

    pio.write_html(fig, file=file_path.with_suffix('.html'))


# def run_analysis(vib_file: Union[str, Path]) -> None:
def run_analysis(vib_files: list[str]) -> None:  # Note we now take a list of file paths
    for vib_file_str in vib_files:
        logging.info(f'Running analysis on "{vib_file_str}"')
        vib_file = Path(vib_file_str)

        if not vib_file.is_file():
            logging.error(f"Could not find input file at {vib_file}. Skipping.")
            continue

        # Read in the data file and wrestle it into a workable format
        df = pd.read_csv(vib_file, skiprows=28, delim_whitespace=True, dtype=str)
        df = df.iloc[1:-4]
        df['Timer'] = df['Timer'].apply(string_to_timedelta)
        df['Time'] = df.apply(to_datetime, axis=1)
        df = df.drop(columns=['Date'])
        df.set_index('Time', inplace=True)
        df[df.columns[2:]] = df[df.columns[2:]].astype(float)

        # Rename columns properly
        new_cols = [col for col in df.columns if col not in ['Band', '[Hz]']]
        df = df.iloc[:, :-2]
        df.columns = new_cols

        # Create an interactive graph for all frequencies in input file
        data_all = df.iloc[:, 2:]
        create_vibplot_html(data_all, vib_file)

        # Create an interactive graph for low frequencies in input file (easier to see differences in low-freq data)
        data_lf = data_all.iloc[:, :12]  # Select low frequency data
        create_vibplot_html(data_lf, vib_file.with_stem(vib_file.stem + '_lf'))


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Don't want a full GUI, so keep the root window from appearing

    # Show an "Open" dialog box and return the path to the selected file(s) (allows selection of multiple files)
    input_files = filedialog.askopenfilenames(title='Please select input file(s) for visualization')

    logging.info(f'Running analysis on {input_files}')
    run_analysis(input_files)
    logging.info('Done!')

    # Prompt user when processing is finished
    messagebox.showinfo(title='Done Message',
                        message=f'Done processing {len(input_files)} file{"" if len(input_files) == 1 else "s"}!')
