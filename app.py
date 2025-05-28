import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import json
import dash_leaflet as dl
import requests
import bs4

races = pd.read_csv("f1_data/races.csv")
results = pd.read_csv("f1_data/results.csv")
drivers = pd.read_csv("f1_data/drivers.csv")
qualifying = pd.read_csv("f1_data/qualifying.csv")
circuits = pd.read_csv("f1_data/circuits.csv")

with open("f1_data/mc-1929.geojson") as f:
    monaco_geojson = json.load(f)

df = results.merge(drivers, on='driverId')
df = df.merge(races, on='raceId')

df_senna = df[(df['surname'] == 'Senna') & (df['forename'] == 'Ayrton')]

senna_wins = df_senna[df_senna['positionOrder'] == 1]

wins_per_season = senna_wins.groupby('year')['positionOrder'].count().reset_index()
wins_per_season.columns = ['Season', 'Wins']

url = 'https://en.wikipedia.org/wiki/List_of_Formula_One_fatalities'
req = requests.get(url)
soup = bs4.BeautifulSoup(req.text, 'html.parser')
table = soup.find_all('table')[2]
rows = table.find_all('tr')

headers = [th.get_text(strip=True) for th in rows[0].find_all('th')]
data = []
for row in rows[1:]:
    cells = row.find_all(['td', 'th'])
    if len(cells) != len(headers):
        continue
    row_data = [cell.get_text(strip=True) for cell in cells]
    data.append(row_data)

df = pd.DataFrame(data, columns=headers)
df['Date'] = pd.to_datetime(df['Date of accident'], errors='coerce')
df = df.dropna(subset=['Date'])
df['Year'] = df['Date'].dt.year.astype(int)

df['Decade'] = (df['Year'] // 10) * 10
fatalities_per_decade = df.groupby('Decade').size().reset_index(name='Fatalities')

before_1994 = df[df['Year'] < 1994].shape[0]
after_1994 = df[df['Year'] >= 1994].shape[0]
pie_data = pd.DataFrame({
    'Period': ['Before 1994', '1994 and After'],
    'Fatalities': [before_1994, after_1994]
})

drivers['driverName'] = drivers['forename'] + ' ' + drivers['surname']

top_drivers = [
    'Ayrton Senna', 'Michael Schumacher', 'Lewis Hamilton',
    'Sebastian Vettel', 'Alain Prost', 'Niki Lauda', 'Max Verstappen'
]

# --- Dash App Initialization ---
external_stylesheets = [
    dbc.themes.LITERA,
    "https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,300..800;1,300..800&display=swap"
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# --- Layout ---
app.layout = dbc.Container([

    html.H1("Ayrton Senna: Formula 1 Legend", className="text-center text-danger my-4 display-3 fw-bold", style={"fontFamily": "'Open Sans', sans-serif"}),

    dbc.Row([
        dbc.Col([
            html.Img(src="/assets/senna.avif", style={"width": "100%", "borderRadius": "20px", "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.2)"})
        ], width=4),

        dbc.Col([
            html.P(
                "Ayrton Senna da Silva was a Brazilian Formula One driver widely regarded as one of the greatest in the sport's history. "
                "Born on March 21, 1960, into a wealthy family, Senna discovered his passion for racing at the age of four when his father gave him a miniature go-kart. "
                "He won his first kart race at 13 and later moved to Britain, where he dominated Formula Ford and Formula 3, winning five championships in three years. "
                "Forsaking a future in his family’s business, he debuted in Formula 1 with Toleman in 1984. "
                "His remarkable second-place finish in the rain-soaked Monaco Grand Prix signaled the arrival of a phenomenal talent.",
                style={"fontSize": "1.7rem", "fontFamily": "'Open Sans', sans-serif"}
            )
        ], width=8)
    ], className="mb-5"),

    html.H2("Career Overview – Senna in Numbers", className="text-danger mb-4 text-center fw-bold display-4", style={"fontFamily": "'Open Sans', sans-serif"}),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("161", className="card-title text-danger fw-bold display-5 text-center", style={"fontFamily": "'Open Sans', sans-serif"}),
                    html.P("Races", className="text-center display-8", style={"fontFamily": "'Open Sans', sans-serif"})
                ])
            ], className="shadow rounded-4 border-danger")
        ], width=3),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("41", className="card-title text-danger fw-bold display-5 text-center", style={"fontFamily": "'Open Sans', sans-serif"}),
                    html.P("Wins", className="text-center display-8", style={"fontFamily": "'Open Sans', sans-serif"})
                ])
            ], className="shadow rounded-4 border-danger")
        ], width=3),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("65", className="card-title text-danger fw-bold display-5 text-center", style={"fontFamily": "'Open Sans', sans-serif"}),
                    html.P("Pole Positions", className="text-center display-8", style={"fontFamily": "'Open Sans', sans-serif"})
                ])
            ], className="shadow rounded-4 border-danger")
        ], width=3),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("3", className="card-title text-danger fw-bold display-5 text-center", style={"fontFamily": "'Open Sans', sans-serif"}),
                    html.P("Championships", className="text-center display-8", style={"fontFamily": "'Open Sans', sans-serif"})
                ])
            ], className="shadow rounded-4 border-danger")
        ], width=3),
    ], className="mb-5"),

    dbc.Row([
        # Wins per Season
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Wins per Season", className="bg-danger text-white fw-bold fs-5"),
                dbc.CardBody([
                    dcc.RangeSlider(
                        id='season-range-slider',
                        min=df_senna['year'].min(),
                        max=df_senna['year'].max(),
                        value=[df_senna['year'].min(), df_senna['year'].max()],
                        marks={str(year): str(year) for year in sorted(df_senna['year'].unique())},
                        step=1,
                        allowCross=False,
                        tooltip={"placement": "bottom", "always_visible": False}
                    ),
                    dcc.Graph(id='wins-season-bar')])
            ], className="shadow-lg rounded-4 h-100")
        ], width=4),

        # Points per Season
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Points per Season", className="bg-danger text-white fw-bold fs-5"),
                dbc.CardBody([
                    dcc.RangeSlider(
                        id='points-season-slider',
                        min=df_senna['year'].min(),
                        max=df_senna['year'].max(),
                        value=[df_senna['year'].min(), df_senna['year'].max()],
                        marks={str(year): str(year) for year in sorted(df_senna['year'].unique())},
                        step=1,
                        allowCross=False,
                        tooltip={"placement": "bottom", "always_visible": False}
                    ),
                    dcc.Graph(id='points-season-bar')])
            ], className="shadow-lg rounded-4 h-100")
        ], width=4),

        # Pie Chart
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Race Outcomes", className="bg-danger text-white fw-bold fs-5"),
                dbc.CardBody([dcc.Graph(id='senna-pie-chart')])
            ], className="shadow-lg rounded-4 h-100")
        ], width=4),
    ], className="mb-5"),

    html.H2("Qualifying Master", className="text-danger my-4 text-center fw-bold display-4", style={"fontFamily": "'Open Sans', sans-serif"}),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Number of Poles by Track", className="bg-danger text-white fw-bold fs-5"),
                dbc.CardBody([dcc.Graph(id='poles-by-track')])
            ], className="shadow-lg rounded-4 h-100")
        ], width=6),

        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Pole Positions vs Race Wins per Year", className="bg-danger text-white fw-bold fs-5"),
                dbc.CardBody([dcc.Graph(id='poles-vs-wins')])
            ], className="shadow-lg rounded-4 h-100")
        ], width=6)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Top Pole Sitters Comparison", className="bg-danger text-white fw-bold fs-5"),
                dbc.CardBody([
                        dcc.Dropdown(
                            id='driver-selector',
                            options=[{'label': name, 'value': name} for name in top_drivers],
                            value=['Ayrton Senna', 'Michael Schumacher', 'Lewis Hamilton'],  # default selected
                            multi=True,
                            placeholder="Select drivers..."
                        ),
                        dcc.Graph(id='pole-comparison-graph')])
            ], className="shadow-lg rounded-4 h-100")
        ])
    ], className="mb-4"),

    dbc.Alert("Senna held the record for most poles (65) until 2006.", color="danger", className="fw-bold fs-5 text-center shadow-lg"),

    html.H2("The Monaco King", className="text-danger my-4 text-center fw-bold display-4", style={"fontFamily": "'Open Sans', sans-serif"}),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Monaco Grand Prix Finishes", className="bg-danger text-white fw-bold fs-5"),
                dbc.CardBody([
                        dcc.RangeSlider(
                            id='monaco-year-slider',
                            min=df_senna['year'].min(),
                            max=df_senna['year'].max() - 1,
                            value=[1984, 1993],
                            marks={str(year): str(year) for year in sorted(df_senna['year'].unique()) if 1984 <= year <= 1993},
                            step=1,
                            allowCross=False,
                            tooltip={"placement": "bottom", "always_visible": False}
                        ),
                        dcc.Graph(id='monaco-finishes')])
            ], className="shadow-lg rounded-4 h-100"),
        ], width=6),

        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Monaco Circuit Layout", className="bg-danger text-white fw-bold fs-5"),
                dbc.CardBody(   dl.Map(center=[43.7347, 7.4206], zoom=15, style={'width': '100%', 'height': '600px'}, children=[
                                dl.TileLayer(),
                                dl.GeoJSON(data=monaco_geojson, id="geojson")
                            ]))
            ], className="shadow-lg rounded-4 h-100")
        ], width=6),
    ], className="mb-4"),

    dbc.Row([
    dbc.Col([
        html.Video(
            controls=True,
            src="/assets/1984_monaco_gp_rain.mp4", 
            style={'width': '100%', 'borderRadius': '10px'}
        ),
        dbc.Alert("1984 Monaco Grand Prix", color="primary", className="text-center fw-bold mt-2", style={"fontFamily": "'Open Sans', sans-serif"})
    ], width=6),

    dbc.Col([
        html.Video(
            controls=True,
            src="/assets/1990_monaco_gp.mp4", 
            style={'width': '100%', 'borderRadius': '10px'}
        ),
        dbc.Alert("1990 Monaco Grand Prix", color="primary", className="text-center fw-bold mt-2", style={"fontFamily": "'Open Sans', sans-serif"})
        ], width=6),
    ], className="mt-4"),

    dbc.Alert("Senna won Monaco 6 times – a record that stood for years.", color="danger", className="fw-bold fs-5 text-center shadow-lg"),

    html.H2("Legacy – After the Tragedy", className="text-danger my-4 text-center fw-bold display-4", style={"fontFamily": "'Open Sans', sans-serif"}),
    html.P("His death at Imola 1994 led to massive F1 safety reforms. His impact lives on.", className="text-center", style={"fontFamily": "'Open Sans', sans-serif"}),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("F1 Driver Fatalities per Decade", className="bg-danger text-white fw-bold fs-5"),
                dbc.CardBody([dcc.Graph(id='fatalities-line')])
            ], className="shadow-lg rounded-4 h-100")
        ], width=6),

        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Fatalities Before and After Senna's Death", className="bg-danger text-white fw-bold fs-5"),
                dbc.CardBody([dcc.Graph(id='fatalities-pie')])
            ], className="shadow-lg rounded-4 h-100")
        ], width=6),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([ dbc.Alert([
        html.I(className="bi bi-quote fs-3 me-2"),
        html.Span("Senna was the last F1 driver to die during a race before Jules Bianchi (2014).")
        ], color="secondary", className="fs-5", style={"fontFamily": "'Open Sans', sans-serif", "textAlign": "center"}),
        ]),
        dbc.Col([html.Video(
            controls=True,
            src="/assets/imola_crash.mp4", 
            style={'width': '100%', 'borderRadius': '10px'}
        ),])
    ]),
    
    html.H2("Sources", className="text-danger my-4 text-center fw-bold display-4", style={"fontFamily": "'Open Sans', sans-serif"}),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Ul([
                        html.Li([
                            html.A("Kaggle – Formula 1 World Championship (1950–2020)", 
                                   href="https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020", 
                                   target="_blank", 
                                   style={"textDecoration": "none", "color": "#dc3545", "fontWeight": "bold"})
                        ]),
                        html.Li([
                            html.A("Wikipedia – Ayrton Senna", 
                                   href="https://en.wikipedia.org/wiki/Ayrton_Senna", 
                                   target="_blank", 
                                   style={"textDecoration": "none", "color": "#dc3545", "fontWeight": "bold"})
                        ]),
                        html.Li([
                            html.A("Ayrton Senna Photo", 
                                   href="https://www.biography.com/athletes/a63001762/ayrton-senna-death", 
                                   target="_blank", 
                                   style={"textDecoration": "none", "color": "#dc3545", "fontWeight": "bold"})
                        ]),
                        html.Li([
                            html.A("Monaco Grand Prix Circuit", 
                                   href="https://github.com/bacinger/f1-circuits", 
                                   target="_blank", 
                                   style={"textDecoration": "none", "color": "#dc3545", "fontWeight": "bold"})
                        ]),
                        html.Li([
                            html.A("1984 Monaco Grand Prix Video", 
                                   href="https://youtu.be/lorinQQm_rY?si=XddyACfan8ZUxCUV", 
                                   target="_blank", 
                                   style={"textDecoration": "none", "color": "#dc3545", "fontWeight": "bold"})
                        ]),
                        html.Li([
                            html.A("1990 Monaco Grand Prix Video", 
                                   href="https://youtu.be/auXfAHHNSFo?si=rAXCxEiKlxf_0o3Q", 
                                   target="_blank", 
                                   style={"textDecoration": "none", "color": "#dc3545", "fontWeight": "bold"})
                        ]),
                        html.Li([
                            html.A("Wikipedia - Formula One Fatalities", 
                                   href="https://en.wikipedia.org/wiki/List_of_Formula_One_fatalities", 
                                   target="_blank", 
                                   style={"textDecoration": "none", "color": "#dc3545", "fontWeight": "bold"})
                        ]),
                        html.Li([
                            html.A("Ayrton Senna's Fatal Crash Imola 1994", 
                                   href="https://youtu.be/x9znf-lpg4Q?si=VSWEXF2d0vnt9mii", 
                                   target="_blank", 
                                   style={"textDecoration": "none", "color": "#dc3545", "fontWeight": "bold"})
                        ]),
                    ], style={"fontSize": "1.1rem", "fontFamily": "'Open Sans', sans-serif"})
                ])
            ], className="shadow-lg rounded-4 border-danger")
        ]),
    ], className="mb-5")
    
    ],fluid=True, className="px-5 py-2")


# --- Callbacks / Static Graphs ---
@app.callback(
    Output('wins-season-bar', 'figure'),
    Input('season-range-slider', 'value')
)
def update_wins_season_bar(season_range):
    start_year, end_year = season_range

    senna_wins = df_senna[
        (df_senna['positionOrder'] == 1) &
        (df_senna['year'] >= start_year) &
        (df_senna['year'] <= end_year)
    ]
    
    wins_per_season = senna_wins.groupby('year')['positionOrder'].count().reset_index()
    wins_per_season.columns = ['year', 'Wins']
    wins_per_season['Season'] = wins_per_season['year'].apply(lambda y: f"'{str(y)[-2:]}")
    wins_per_season = wins_per_season[['Season', 'Wins']]
    wins_per_season = wins_per_season.sort_values('Season')

    fig = px.bar(
        wins_per_season,
        x='Season',
        y='Wins',
        text='Wins',
        color_discrete_sequence=['crimson'],
        template='plotly_white'
    )

    fig.update_layout(
        xaxis_title='Season',
        yaxis_title='Number of Wins',
        font=dict(size=14),
        plot_bgcolor='white',
        margin=dict(l=40, r=40, t=40, b=40),
    )

    fig.update_xaxes(type='category', tickangle=0)
    fig.update_yaxes(tick0=0, dtick=1)
    fig.update_traces(textposition='outside', hovertemplate='Season: %{x}<br>Wins: %{y}')

    return fig

@app.callback(
    Output('points-season-bar', 'figure'),
    Input('points-season-slider', 'value')
)
def update_points_season_bar(season_range):
    start_year, end_year = season_range

    # Filter data based on selected range
    filtered_df = df_senna[(df_senna['year'] >= start_year) & (df_senna['year'] <= end_year)]

    # Group and prepare data
    points_per_season = filtered_df.groupby('year')['points'].sum().reset_index()
    points_per_season.columns = ['year', 'Points']
    points_per_season['Season'] = points_per_season['year'].apply(lambda y: f"'{str(y)[-2:]}")
    points_per_season = points_per_season[['Season', 'Points']]

    # Create bar chart
    fig = px.bar(
        points_per_season,
        x='Season',
        y='Points',
        text='Points',
        color_discrete_sequence=['crimson'],
        template='plotly_white'
    )

    # Enhance layout
    fig.update_layout(
        xaxis_title='Season',
        yaxis_title='Total Points',
        font=dict(size=14),
        plot_bgcolor='white',
        margin=dict(l=40, r=40, t=40, b=40),
    )

    fig.update_xaxes(type='category', tickangle=0)
    fig.update_yaxes(tick0=0)
    fig.update_traces(textposition='outside', hovertemplate='Season: %{x}<br>Points: %{y:.1f}')

    return fig

@app.callback(
    Output('senna-pie-chart', 'figure'),
    Input('senna-pie-chart', 'id')
)
def update_pie_chart(_):
    # Categorize finishes
    finishes = {
        'Wins': (df_senna['positionOrder'] == 1).sum(),
        '2nd/3rd (Podiums)': df_senna['positionOrder'].isin([2, 3]).sum(),
        '4th–10th': df_senna['positionOrder'].between(4, 10).sum(),
        'Other / DNF': df_senna['positionOrder'].gt(10).sum()
    }

    pie_df = pd.DataFrame({
        'Result': list(finishes.keys()),
        'Count': list(finishes.values())
    })

    # Generate figure
    fig = px.pie(
        pie_df,
        values='Count',
        names='Result',
        hole=0.35,
        color_discrete_sequence=['#a50026', '#d73027', '#f46d43', '#fdae61'],
        template='plotly_white',
    )

    fig.update_traces(
        textinfo='percent+label',
        textfont_size=16,
        marker=dict(line=dict(color='white', width=2)),
        hovertemplate='%{label}<br>Count: %{value} (%{percent})<extra></extra>'
    )

    fig.update_layout(
        showlegend=False,
        margin=dict(t=20, b=20, l=20, r=20),
    )

    return fig

@app.callback(
    Output('poles-by-track', 'figure'),
    Input('poles-by-track', 'id')
)
def update_poles_by_track(_):
    poles_by_circuit = (
        df_senna[df_senna['grid'] == 1]
        .groupby('name')
        .size()
        .reset_index(name='Pole Positions')
        .sort_values('Pole Positions', ascending=False)
    )

    poles_by_circuit['name'] = poles_by_circuit['name'].str.replace(r'\s*Grand Prix', '', regex=True)

    # Generate bar chart
    fig = px.bar(
        poles_by_circuit,
        x='name',
        y='Pole Positions',
        text='Pole Positions',
        labels={'name': 'Track'},
        color_discrete_sequence=['crimson'],
        template='plotly_white'
    )

    # Enhance layout
    fig.update_layout(
        xaxis_title='Track',
        yaxis_title='Number of Poles',
        xaxis_tickfont_size=12,
        xaxis_tickangle=-45,
        font=dict(size=14),
        plot_bgcolor='white',
        margin=dict(l=20, r=20, t=5, b=40),
    )

    fig.update_yaxes(tick0=0)
    fig.update_traces(textposition='outside', hovertemplate='Season: %{x}<br>Points: %{y:.1f}')

    return fig


@app.callback(
    Output('poles-vs-wins', 'figure'),
    Input('poles-vs-wins', 'id')
)
def update_poles_vs_wins(_):
    poles = df_senna[df_senna['grid'] == 1].groupby('year').size().reset_index(name='poles')
    wins = df_senna[df_senna['positionOrder'] == 1].groupby('year').size().reset_index(name='wins')
    combined = pd.merge(poles, wins, on='year', how='outer').fillna(0)
    combined = combined.sort_values('year')

    fig = px.line(
        combined,
        x='year',
        y=['poles', 'wins'],
        markers=True,
        labels={'value': 'Count', 'variable': 'Stat', 'year': 'Season'},
        template='plotly_white',
        color_discrete_map={'poles': 'crimson', 'wins': 'gold'}
    )

    fig.update_layout(
        margin=dict(t=20, b=40, l=20, r=20),
        legend=dict(title='', font=dict(size=14)),
        xaxis=dict(
            rangeslider=dict(visible=True),
            type='linear',
            tickmode='linear',
            dtick=1,
            title='Season',
            showgrid=True
        ),
        yaxis=dict(
            title='Count',
            showgrid=True,
            zeroline=True
        )
    )

    fig.update_traces(marker=dict(size=8))

    return fig


@app.callback(
    Output('pole-comparison-graph', 'figure'),
    Input('driver-selector', 'value')
)
def update_pole_comparison(selected_drivers):
    selected_ids = drivers[drivers['driverName'].isin(selected_drivers)]['driverId']
    top_data = results[(results['driverId'].isin(selected_ids)) & (results['grid'] == 1)]

    count_data = top_data.groupby('driverId').size().reset_index(name='Poles')
    count_data = count_data.merge(drivers[['driverId', 'driverName']], on='driverId')
    count_data = count_data.sort_values(by='Poles', ascending=False)

    fig = px.bar(
        count_data,
        x='driverName',
        y='Poles',
        color='driverName',
        color_discrete_map={
            'Ayrton Senna': 'crimson',
            'Michael Schumacher': 'gray',
            'Lewis Hamilton': 'blue',
            'Sebastian Vettel': 'orange',
            'Alain Prost': 'green',
            'Niki Lauda': 'purple'
        },
        template='plotly_white',
        labels={'driverName': 'Driver', 'Poles': 'Pole Positions'},
        text='Poles'
    )

    fig.update_traces(textposition='outside')
    fig.update_layout(
        yaxis=dict(title='Number of Pole Positions', dtick=10, showgrid=True),
        font=dict(size=14),
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=False,
    )

    return fig

@app.callback(
    Output('monaco-finishes', 'figure'),
    Input('monaco-year-slider', 'value')
)
def update_monaco_finishes(season_range):
    start_year, end_year = season_range

    # Filter only Monaco races
    monaco_id = circuits[circuits['name'].str.contains("Monaco", case=False)]['circuitId'].unique()
    monaco = df_senna[df_senna['circuitId'].isin(monaco_id)]
    monaco = monaco[(monaco['year'] >= start_year) & (monaco['year'] <= end_year)]

    # Prepare data
    monaco['Season'] = monaco['year'].apply(lambda y: f"'{str(y)[-2:]}")
    monaco = monaco[['Season', 'positionOrder']]

    season_order = monaco.sort_values('Season')['Season'].tolist()

    # Create bar chart
    fig = px.bar(
        monaco,
        x='Season',
        y='positionOrder',
        text='positionOrder',
        color_discrete_sequence=['crimson'],
        template='plotly_white',
        category_orders={'Season': season_order}
    )

    # Enhance layout
    fig.update_layout(
        xaxis_title='Season',
        yaxis_title='Final Position',
        font=dict(size=14),
        plot_bgcolor='white',
        margin=dict(l=20, r=20, t=20, b=40),
    )

    fig.update_yaxes(autorange='reversed', tick0=1, dtick=2)
    fig.update_xaxes(type='category', tickangle=0)
    fig.update_traces(textposition='outside', hovertemplate='Season: %{x}<br>Position: %{y}')

    return fig

@app.callback(
    Output('fatalities-line', 'figure'),
    Input('fatalities-line', 'id')
)
def update_fatalities_line(_):
    fig = px.line(
        fatalities_per_decade,
        x='Decade',
        y='Fatalities',
        markers=True,
        labels={'Decade': 'Decade', 'Fatalities': 'Number of Fatalities'},
        template='plotly_white'
    )

    fig.update_traces(
        line=dict(color='crimson', width=3),
        marker=dict(size=8, symbol='circle'),
        text=fatalities_per_decade['Fatalities'],
        textposition="top center",
        hovertemplate='Decade: %{x}<br>Fatalities: %{y}<extra></extra>'
    )

    fig.update_layout(
        font=dict(size=14),
        margin=dict(l=20, r=20, t=20, b=20),
        yaxis=dict(tick0=0, dtick=1, title='Number of Fatalities'),
        xaxis=dict(title='Decade'),
        plot_bgcolor='white',
        showlegend=False
    )

    return fig


@app.callback(
    Output('fatalities-pie', 'figure'),
    Input('fatalities-pie', 'id')
)
def update_fatalities_pie(_):
    pie_fig = px.pie(
        pie_data,
        names='Period',
        values='Fatalities',
        hole=0.4,
        color_discrete_sequence=["#1b72dd", '#d73027']
    )

    pie_fig.update_traces(
        textinfo='percent+label',
        hovertemplate='%{label}: %{value} fatalities (%{percent})<extra></extra>'
    )

    pie_fig.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        font=dict(size=14),
        showlegend=True,
        legend=dict(font=dict(size=16)),
    )

    return pie_fig

if __name__ == '__main__':
    app.run(debug=True)
