import io
import json
from datetime import datetime as dt, timedelta as td

import numpy as np
import pandas as pd
import requests

DATA_URL = "https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/somministrazioni-vaccini" \
           "-summary-latest.csv"
ITALIAN_POPULATION = 60_360_000
HIT = ITALIAN_POPULATION / 100 * 80  # We need 80% of population vaccined for herd immunity


def get_dataset():
    df = pd.read_csv(
        io.StringIO(requests.get(DATA_URL).text),
        index_col="data_somministrazione",
    )
    df.index = pd.to_datetime(
        df.index,
        format="%Y-%m-%d",
    )
    df = df.loc[df["area"] != "ITA"]
    df = df.groupby(df.index).sum()
    # Considerate only the second dose = the number of vaccinated people
    df["seconda_dose"] = pd.to_numeric(df["seconda_dose"])
    if dt.now() - df.index[-1] < td(days=1):
        df = df[:-1]  # Ignore the current day because it's often incomplete
    return df


def generate_hope(df):
    vaccinated = np.sum(df["seconda_dose"])
    remaining_ppl = HIT - vaccinated
    df = df.loc[df.index > df.index[-1] - td(days=7) + td(hours=2)]
    vaccines_per_day_avg = np.average(df.loc[df["seconda_dose"] > 0])
    remaining_days = round(remaining_ppl / vaccines_per_day_avg)
    return {
        'remaining_days': remaining_days,
        'hit_date': (df.index[-1] + td(days=remaining_days)).timestamp(),
        'vaccines_per_day': vaccines_per_day_avg,
        'vaccinated': int(vaccinated),
        'perc_vaccinated': str(round(vaccinated / ITALIAN_POPULATION * 100, 2)).replace('.', ',')
    }


if __name__ == "__main__":
    data = generate_hope(get_dataset())
    with open("data.json", "w+") as f:
        json.dump(data, f)
