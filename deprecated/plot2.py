import plotly.plotly as py
import plotly.graph_objs as go

import pandas as pd
import plotly

plotly.tools.set_credentials_file(username='spencerhongcornell', api_key='dDxGTorvGXVFVyYa0dLC')

# Read data from a csv
z_data = pd.read_csv('4bar-sim-results.csv')

data = [
    go.Surface(
        z=z_data.as_matrix(),
        contours=go.surface.Contours(
            z=go.surface.contours.Z(
              show=True,
              usecolormap=True,
              highlightcolor="#42f462",
              project=dict(z=True)
            )
        )
    )
]
layout = go.Layout(
    title='Real COP',
    autosize=False,
    scene=dict(camera=dict(eye=dict(x=1.87, y=0.88, z=-0.64))),
    width=500,
    height=500,
    margin=dict(
        l=65,
        r=50,
        b=65,
        t=90
    )
)

fig = go.Figure(data=data, layout=layout)
py.iplot(fig, filename='elevations-3d-surface-contours')