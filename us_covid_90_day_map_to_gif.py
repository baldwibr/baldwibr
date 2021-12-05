#!/usr/bin/python3

import os
from google.cloud import bigquery
import plotly.express as px
from urllib.request import urlopen
import json
import pandas as pd
import numpy as np
from chart_studio.plotly import image as PlotlyImage
from PIL import Image as PILImage
import io
import chart_studio
from datetime import datetime, timedelta

# set the environment to your GCP Project
os.environ.setdefault("GCLOUD_PROJECT", "gcp-gfs-datalab-supply-chain")

# loads your credentials
client = bigquery.Client()

sql = """
SELECT
  DATE_DIFF(DATE_SUB(CURRENT_DATE('EST'), INTERVAL 1 DAY), Date, DAY) AS date_number,
  Date,
  County_code,
  IFNULL(SAFE_DIVIDE(Moving_Avg_Cases,population),0) as pct_pop_infected,
  IFNULL(SAFE_DIVIDE(Moving_Avg_Deaths,population),0) as pct_pop_deaths
FROM
  `gcp-gfs-datalab-supply-chain.BBALDWIN.michigan_covid_data`
WHERE
  Date BETWEEN DATE_SUB(CURRENT_DATE('EST'), INTERVAL 92 DAY)
  AND DATE_SUB(CURRENT_DATE('EST'), INTERVAL 2 DAY)
  AND County_code IS NOT NULL
  AND State_code IS NOT NULL
  AND State_code NOT IN (
    'MP',
    'PR',
    'VI')
    """

# runs query and returns results inside a dataframe
df = client.query(sql).to_dataframe()

# listing the days prior as integers in an array
days_array = np.int64(df['date_number'].unique())

# retrieves the county coordinates library to use in the visualization
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

# function to build each map
def covid_plot (df, day):
    fig3 = px.choropleth(df[df['date_number']==day], geojson=counties, locations='County_code', color='pct_pop_infected',
                           color_continuous_scale="Hot",
                           range_color=(0, .003),
                           scope="usa",
                           labels={'pct_pop_infected':'Pct of Population Infected'}
                          )
    fig3.update_layout(margin={"r":0,"t":0,"l":0,"b":0},
                       title = {'text' : '7-Day Moving Avg New Infections for '+ str(datetime.date(datetime.today() - timedelta(days=int(day))).isoformat()),
                                'y':0.2,
                                'x':0.5,
                                'xanchor': 'center',
                                'yanchor': 'top'})

      # Saving the images going through bytes format

    img_bytes = PlotlyImage.get(fig3)
    image = PILImage.open(io.BytesIO(img_bytes))
    image.save(r"C:\Users\e3dy0\Desktop\Projects\GFS_projects\images\day"+str(day)+".png")

    return image

##### NOTE: the ChartIO API only allows 100 calls per 24hrs, so this will only be able to run once per day ####
# building the GIF framework
images = []
# sets the duration for the GIF animation
durations = []
# looping over the images and saving them into a list
for day in days_array:
  images.append(covid_plot(df,day))
  if day != 1:
    # animiation will play video-like speed
    durations.append(200)
  else:
    # this will hold the last frame of the GIF 10x longer before the GIF loops
    durations.append(2000)

# creating the GIF
images[0].save(r"C:\Users\e3dy0\Desktop\Projects\GFS_projects\images\covid19-case.gif",
               save_all=True, append_images=images[1:], optimize=True, duration=durations, loop=0)