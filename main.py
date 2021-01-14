import io
from datetime import datetime as dt, timedelta as td

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
pd.options.mode.chained_assignment = None #sennò pandas si lamento quando dfOG = df


DATA_URL = "https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/somministrazioni-vaccini" \
           "-summary-latest.csv"
ITALIAN_POPULATION = 60_360_000
HIT = ITALIAN_POPULATION / 100 * 80  # We need 80% of population vaccined for herd immunity

def get_image_hash():
    import hashlib
    with open("plot.png", "rb") as fo:
        return hashlib.sha256(fo.read()).hexdigest()


r = requests.get(DATA_URL)
df = pd.read_csv(
    io.StringIO(r.text),
    index_col="data_somministrazione",
)
df.index = pd.to_datetime(
    df.index,
    format="%Y-%m-%d",
)
dfOG = df #oooof
df = df.loc[df["area"] == "ITA"]
df["totale"] = pd.to_numeric(df["totale"])
if dt.now() - df.index[-1] < td(days=1):
    df = df[:-1]  # Ignore the current day because it's often incomplete

totalVaccines = sum(df["totale"])
lastWeekData = df.loc[df.index > df.index[-1] - td(days=7) + td(hours=2)]
vaccinesPerDayAverage = sum(lastWeekData["totale"]) / 7
remainingDays = (HIT - totalVaccines) / vaccinesPerDayAverage
hitDate = df.index[-1] + td(days=remainingDays)

# Generate plot
plt.ylabel("Vaccini al giorno")
plt.xlabel("Ultima settimana")
plt.grid(True)
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
plt.gcf().autofmt_xdate()
plt.bar(lastWeekData.index, height=lastWeekData["totale"])
# Trendline
z = np.polyfit(range(0, 7), lastWeekData["totale"], 2)
p = np.poly1d(z)
plt.plot(lastWeekData.index, p(range(0, 7)), "r--")
plt.savefig("plot.png", dpi=300, bbox_inches='tight')

popolazione = [1305770, 556934, 1924701, 5785861, 4467118, 1211357, 5865544, 1543127, 10103969, 1518400, 302265, 532080, 542739 ,4341375, 4008296, 1630474, 4968410 ,3722729,880285,125501,4907704]
#popolazione di ogni regione in ordine alfabetico

if dt.now() - dfOG.index[-1] < td(days=1):
    dfOG = dfOG[:-1]

regioni = dfOG["area"].loc[dfOG.index[0]]
regioni = regioni.values.tolist()
regioni.remove("ITA")

# Generate template
with open("template.html", "r+") as f:
    with open("index.html", "w+") as wf:
        for line in f.read().splitlines():
            if "<!-- totalVaccinations -->" in line:
                line = f"{totalVaccines}"
            if "<!-- totalVaccinationsPerc -->" in line:
                line = f"{str(round(totalVaccines / ITALIAN_POPULATION * 100, 2)).replace('.', ',')}%"
            elif "<!-- totalVaccinationsLastWeek -->" in line:
                line = f"{int(vaccinesPerDayAverage*7)}"
            elif "<!-- vaccinesPerDay -->" in line:
                line = f"{int(vaccinesPerDayAverage)}"
            elif "<!-- hitDate -->" in line:
                line = f"{hitDate.strftime('%d/%m/%Y')}"
            elif "<!-- hitHour -->" in line:
                line = f"{hitDate.strftime('%H:%M:%S')}"
            elif "<!-- daysRemaining -->" in line:
                line = f"{int(remainingDays)}"
            elif "plot.png" in line:
                line = f"plot.png?build={get_image_hash()}"
            if "<!--" in line:
                x = line.split("<!-- ")[1].split(" -->")[0]
                for regione in regioni:    
                    if regione.find(x) != -1:
                        dfTemp = dfOG.loc[dfOG["area"] == regione]
                        hit_reg = popolazione[regioni.index(regione)] / 100 * 80
                        vacc_tot = sum(dfTemp["totale"])
                        
                        lastWeekData = dfTemp.loc[dfTemp.index > dfTemp.index[-1] - td(days=7) + td(hours=2)]
                        vaccinesPerDayAverage = sum(lastWeekData["totale"]) / 7
                        tempo = (hit_reg - vacc_tot) / vaccinesPerDayAverage

                        obj = {
                            "percentuale": round(vacc_tot / hit_reg * 100, 2), 
                            "tempo": int(tempo)
                        }
                        line = f'{obj},' 
            wf.write("\n" + line)
