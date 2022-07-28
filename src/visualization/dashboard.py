import pandas as pd
import numpy as np

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output,State
import dash_daq as daq
import dash_bootstrap_components as dbc

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import os
from datetime import date
from collections import defaultdict



def calc_doubling_rate(N_0, t, T_d):
    return N_0 * np.power(2, t/T_d)

def run_dashboard():

    ## Fetch all data
    df_input_large = pd.read_csv('../data/processed/COVID_final_set.csv', sep=';')
    df_input_daily = pd.read_csv('../data/processed/COVID_final_daily_set.csv', sep=';')
    df_SIR_data = pd.read_csv('../data/processed/COVID_SIR_Model_Data.csv', sep=';')
    df_analyse = pd.read_csv('../data/processed/COVID_full_flat_table.csv', sep=';')
    df_global_latest_stats = pd.read_csv('../data/processed/global_latest_stats.csv', sep=";")
    global_stats = pd.DataFrame(df_global_latest_stats[['population', 'confirmed', 'deaths', 'recovered', 'active']].sum()).T.astype("int64")
    global_stats.columns = ['Total population', 'Total confirmed', ' Total deaths', 'Total recovered', 'Total active']

    ## Filter SIR data
    df_SIR_data = df_SIR_data.loc[:, (df_SIR_data != 0).any(axis=0)]


    css = [
        'https://codepen.io/chriddyp/pen/bWLwgP.css',
        {
            'href': 'https://stackpath.bootstrapcdn.com/bootstrap/5.1.3/css/bootstrap.min.css',
            'rel': 'stylesheet',
            'integrity': 'sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO',
            'crossorigin': 'anonymous'
        }
    ]
    app = dash.Dash(external_stylesheets=[css])


    app.layout = html.Div([

        dcc.Markdown('''
        # COVID-19 Dashboard and SIR Modelling
        ''',style={'text-align':'center','border-style': 'solid'}),


        html.Br(),html.Br(),html.Br(),


        html.Div([
            dcc.Markdown('''
                ## Global Statistics
                ''',style={'text-align':'center'}),

            dash.dash_table.DataTable(
                data = global_stats.to_dict('records'),
                columns = [{"name": i, 
                            "id": i, 
                            'type': 'numeric',
                            'format' : dash.dash_table.Format.Format().group(True)
                           } for i in global_stats.columns],
                style_cell={
                    'textAlign': 'center',
                    'fontSize':17
                },
                style_header={
                    'backgroundColor': 'rgb(30, 30, 30)',
                    'color': 'white',
                    #'fontWeight': 'bold'
                },
                style_data={
                    'backgroundColor': 'rgb(50, 50, 50)',
                    'color': 'white',
                    #'fontWeight': 'bold'
                },
            ),

            dcc.Markdown('''
                ***Select which case values to visualize:***
                ''',style={'text-align':'left'}),
            dcc.RadioItems(
                options=[
                    {'label': 'Confirmed', 'value': 'confirmed'},
                    {'label': 'Deaths', 'value': 'deaths'},
                    {'label': 'Recovered', 'value': 'recovered'},
                    {'label': 'Active', 'value': 'active'},
                ],
                value='confirmed',
                id='global_variable',
                labelStyle={'display': 'inline-block'}
            ),

            dcc.Markdown('''
                ***Select whether to show absolute values, or the proportion of population:***
                ''',style={'text-align':'left'}),
            dcc.RadioItems(
                options=[
                    {'label': 'Absolute values', 'value': ''},
                    {'label': 'Proportion of Population', 'value': '_ratio'},
                ],
                value='',
                id='global_type',
                labelStyle={'display': 'inline-block'}
            ),

            dcc.Graph(id='global_map'),

        ],
        ),


        html.Br(),html.Br(),html.Br(),


        dbc.Row([
            dbc.Col(md=5, children=[

                dcc.Markdown('''
                ## Statistics by Country
                ''',style={'text-align':'center'}),
                dcc.Markdown('''
                ***Select one country:***
                ''',style={'text-align':'left'}),

                dcc.Dropdown(
                    id='country_drop_down_stats',
                    options=[ {'label': each,'value':each} for each in df_input_large['country'].unique()],
                    value='Germany',
                    multi=False,
                    style=dict(
                        width='50%',
                        verticalAlign="left"
                    )
                ),
                html.Br(),
                html.Div([
                    dcc.Tabs(id='tabs-example', value='tab-1', children=[
                        dcc.Tab(label='Cummulative', value='tab-1', children=[
                            html.Div([
                                html.Br(),
                                dbc.Row([
                                    dbc.Col(md=3, children=[
                                    dcc.Markdown('''
                                    ***Scale Modes:***
                                    ''',style={'text-align':'left'}),
                                    ]),
                                    dbc.Col(md=4, children=[
                                        dcc.RadioItems(
                                            options=[
                                                {'label': 'Linear', 'value': 'linear'},
                                                {'label': 'Logarithmic', 'value': 'log'},

                                            ],
                                            value='linear',
                                            id='scale_type',
                                            labelStyle={'display': 'inline-block'}
                                        ),
                                    ]),
                                    dcc.Markdown('''
                                    ***Select date range:***
                                    ''',style={'text-align':'left'}),
                                    dcc.DatePickerRange(
                                        id='date-range-1',
                                        start_date = pd.to_datetime(df_input_large['date']).min().date(),
                                        end_date = pd.to_datetime(df_input_large['date']).max().date(),
                                        min_date_allowed = pd.to_datetime(df_input_large['date']).min().date(),
                                        max_date_allowed = pd.to_datetime(df_input_large['date']).max().date(),
                                        display_format='DD-MMM-YYYY'
                                    ),
                                ])

                            ]),
                            dcc.Graph( id='multi_graph'),

                        ]),
                        dcc.Tab(label='Daily', value='tab-2', children=[
                            html.Div([
                                html.Br(),
                                dbc.Row([
                                    dbc.Col(md=3, children=[
                                    dcc.Markdown('''
                                    ***Scale Modes:***
                                    ''',style={'text-align':'left'}),
                                    ]),
                                    dbc.Col(md=4, children=[
                                        dcc.RadioItems(
                                            options=[
                                                {'label': 'Linear', 'value': 'linear'},
                                                {'label': 'Logarithmic', 'value': 'log'},

                                            ],
                                            value='linear',
                                            id='scale_type2',
                                            labelStyle={'display': 'inline-block'}
                                        ),
                                    ]),
                                    dcc.Markdown('''
                                    ***Select date range:***
                                    ''',style={'text-align':'left'}),
                                    dcc.DatePickerRange(
                                        id='date-range-2',
                                        start_date = pd.to_datetime(df_input_large['date']).min().date(),
                                        end_date = pd.to_datetime(df_input_large['date']).max().date(),
                                        min_date_allowed = pd.to_datetime(df_input_large['date']).min().date(),
                                        max_date_allowed = pd.to_datetime(df_input_large['date']).max().date(),
                                        display_format='DD-MMM-YYYY'
                                    ),
                                ])

                            ]),

                            dcc.Graph(id = 'multi_graph_daily'),
                        ]),

                    ]),

                ]),

            ]),

        ]),


        html.Br(),html.Br(),html.Br(),


        html.Div([
            dcc.Markdown('''
                ## Compare countries with Confirmed (smoothed) Cases and Doubling Rate
                ''',style={'text-align':'center'}),

            dcc.Markdown('''
                ***Select one or more countries:***
                ''',style={'text-align':'left'}),

            dcc.Dropdown(
                id='country_drop_down',
                options=[ {'label': each,'value':each} for each in df_input_large['country'].unique()],
                value=['US', 'Germany', 'India'], # which are pre-selected
                multi=True,
                style=dict(
                            width='60%',
                            verticalAlign="left"
                        )
            ),

            dcc.Markdown('''
                ***Scale Modes:***
                ''', style={'text-align':'left'}),
            dcc.RadioItems(
                options=[
                    {'label': 'Linear', 'value': 'linear'},
                    {'label': 'Logarithmic', 'value': 'log'},
                ],
                value='log',
                id='scale_type3',
                labelStyle={'display': 'inline-block'}
            ),

            dcc.Markdown('''
            ***Select number of days for doubling to plot:***
            ''',style={'text-align':'left'}),
            daq.NumericInput(
                id='doubling-days',
                min=0,
                max=1000,
                value = 30,
                size = 100
            ),

            dcc.Markdown('''
            ***Initial population for doubling:***
            ''',style={'text-align':'left'}),
            daq.NumericInput(
                id='doubling-init',
                min=0,
                max=10000,
                value = 100,
                size = 100
            ),

            dcc.Markdown('''
            ***Select date range:***
            ''',style={'text-align':'left'}),
            dcc.DatePickerRange(
                id='date-range-3',
                start_date = pd.to_datetime(df_input_large['date']).min().date(),
                end_date = pd.to_datetime(df_input_large['date']).max().date(),
                min_date_allowed = pd.to_datetime(df_input_large['date']).min().date(),
                max_date_allowed = pd.to_datetime(df_input_large['date']).max().date(),
                display_format='DD-MMM-YYYY'
            ),

            dcc.Graph(id='main_window_DR'),

        ],
        ),


        html.Br(),html.Br(),html.Br(),


        html.Div([

            dcc.Markdown('''
            ## SIR Modelling
            ''',style={'text-align':'center'}),

            dcc.Markdown('''
                ***Select one country:***
                ''',style={'text-align':'left'}),
            dcc.Dropdown(
                id='country_drop_down_sir',
                options=[ {'label': each, 'value':each} for each in list(df_SIR_data.columns) ],
                value='Germany', # which are pre-selected
                multi=False,
                style=dict(
                            width='60%',
                            verticalAlign="middle"
                        )
            ),

            dcc.Markdown('''
                ***Scale Modes:***
                ''', style={'text-align':'left'}),
            dcc.RadioItems(
                options=[
                    {'label': 'Linear', 'value': 'linear'},
                    {'label': 'Logarithmic', 'value': 'log'},
                ],
                value='log',
                id='scale_type4',
                labelStyle={'display': 'inline-block'}
            ),

            html.Br(),
            html.Div([
                dcc.Graph( id='sir_chart'),
            ], 
            ),

        ],),

        html.Br(),html.Br(),html.Br(),


    ])


    #####################################
    ##########
    ########## ALL Callbacks
    ##########
    #####################################




    @app.callback(
        Output('global_map', 'figure'),
        [Input('global_type', 'value'),
         Input('global_variable', 'value'),

        ]
    )
    def update_global_map(global_type, global_variable):

        to_show = global_variable + global_type

        scale_variable = {
            "confirmed": 10000,
            "deaths": 500,
            "recovered": 10000,
            "active": 10000
        }
        scale_type = defaultdict(lambda: 1, 
                                 _ratio=50000000)

        scale = scale_variable[global_variable]/scale_type[global_type]

        if "ratio" in global_type:
            text_to_show = df_global_latest_stats['country']+": "+df_global_latest_stats[to_show].astype(str)+" -- Population: "+df_global_latest_stats['population'].astype(int).astype(str)
        else:    
            text_to_show = df_global_latest_stats['country']+": "+df_global_latest_stats[to_show].astype(int).astype(str)+" -- Population: "+df_global_latest_stats['population'].astype(int).astype(str)

        fig = go.Figure()

        fig.add_trace(go.Scattergeo(
            lon = df_global_latest_stats['Long'],
            lat = df_global_latest_stats['Lat'],
            text = text_to_show,
            marker = dict(
                # size = df_global_latest_stats['population']/1000000,
                # color = df_global_latest_stats[to_show],
                color = df_global_latest_stats['population'],
                size = df_global_latest_stats[to_show] / scale,
                line_color='rgb(40,40,40)',
                line_width=0.5,
                sizemode = 'area',
                showscale = True,
                colorbar={"title": 'Population'}
            ),
        ))
        fig.update_geos(
            showcountries=True, countrycolor="Black",
        )

        fig.update_layout(
            width = 1250,
            height = 650,
            margin=dict(l=50, r=50, t=50, b=50),
            geo = dict(
                landcolor = 'rgb(217, 217, 217)',
            )
        )

        return fig




    @app.callback(
        Output('multi_graph', 'figure'),
        [Input('country_drop_down_stats', 'value'),
         Input('scale_type', 'value'),
         Input('date-range-1', 'start_date'),
         Input('date-range-1', 'end_date'),
        ]
    )
    def update_cummulative_stacked_plot(country, scale_type, start_date, end_date):

        df_plot = df_input_large[(df_input_large['country'] == country) & 
                                 (pd.to_datetime(df_input_large.date) >= pd.to_datetime(start_date)) &
                                 (pd.to_datetime(df_input_large.date) <= pd.to_datetime(end_date))
                                ]
        df_plot = df_plot[['date','state','country','confirmed','confirmed_filtered','deaths',"recovered"]].groupby(['country','date']).agg(np.sum).reset_index()


        fig=make_subplots(rows=3, cols=1,
                          subplot_titles=("Total Confirmed", "Total Recovered", "Total Deaths", "Total Active"),
                          shared_xaxes=False, 
                          vertical_spacing=0.1,
        )
        fig.add_trace(go.Scatter(
                            x=df_plot.date,
                            y=df_plot['confirmed'],
                            mode='markers+lines',
                            opacity=0.9,
                            fill='tozeroy',
                            name="Total Confirmed",
                      ), row=1,col=1
        )
        fig.add_trace(go.Scatter(
                            x=df_plot.date,
                            y=df_plot['recovered'],
                            mode='markers+lines',
                            opacity=0.9,
                            fill='tozeroy',
                            name="Total Recovered",
                      ), row=2,col=1
        )
        fig.add_trace(go.Scatter(
                            x=df_plot.date,
                            y=df_plot['deaths'],
                            mode='markers+lines',
                            opacity=0.9,
                            fill='tozeroy',
                            name="Total Deaths",
                      ), row=3,col=1
        )

        fig.update_xaxes(type="date",
                        tickangle=-45,
                        nticks=20,
                        tickfont=dict(size=14,color="#7f7f7f"), 
                        row=1, col=1)
        fig.update_xaxes(type="date",
                        tickangle=-45,
                        nticks=20,
                        tickfont=dict(size=14,color="#7f7f7f"), 
                        row=2, col=1)
        fig.update_xaxes(type="date",
                        tickangle=-45,
                        nticks=20,
                        tickfont=dict(size=14,color="#7f7f7f"), 
                        row=3, col=1)

        fig.update_yaxes(type=scale_type, row=1, col=1)
        fig.update_yaxes(type=scale_type, row=2, col=1)
        fig.update_yaxes(type=scale_type, row=3, col=1)

        fig.update_layout(dict(
            width=1250,
            height=1200,
            margin=dict(l=50, r=50, t=50, b=50),
        ))

        return fig



    @app.callback(
        Output('multi_graph_daily', 'figure'),
        [Input('country_drop_down_stats', 'value'),
         Input('scale_type2', 'value'),
         Input('date-range-2', 'start_date'),
         Input('date-range-2', 'end_date'),
        ]
    )
    def update_daily_stacked_plot(country, scale_type, start_date, end_date):

        df_plot = df_input_daily[(df_input_daily['country'] == country) & 
                                 (pd.to_datetime(df_input_daily.date) >= pd.to_datetime(start_date)) &
                                 (pd.to_datetime(df_input_daily.date) <= pd.to_datetime(end_date))
                                ]
        df_plot_active = df_input_large[(df_input_large['country'] == country) & 
                                        (pd.to_datetime(df_input_large.date) >= pd.to_datetime(start_date)) &
                                        (pd.to_datetime(df_input_large.date) <= pd.to_datetime(end_date))
                                       ]


        fig=make_subplots(rows=4, cols=1,
                    subplot_titles=("Daily Confirmed", "Daily Recovered", "Daily Deaths", "Daily Active"),
                    shared_xaxes=False, 
                    vertical_spacing=0.1,
        )
        fig.add_trace(go.Bar(x=df_plot.date,
                             y=df_plot['daily_confirmed'],
                             name="Daily Confirmed"
                     ), row=1,col=1
        )
        fig.add_trace(go.Bar(x=df_plot.date,
                             y=df_plot['daily_recovered'],
                             name="Daily Recovered"
                     ), row=2,col=1
        )
        fig.add_trace(go.Bar(x=df_plot.date,
                             y=df_plot['daily_deaths'],
                             name="Daily Deaths"
                     ), row=3,col=1
        )
        fig.add_trace(go.Bar(
                            x=df_plot.date,
                            y=df_plot_active['confirmed'] - (df_plot_active['recovered'] + df_plot_active['deaths']),
                     ), row=4,col=1
        )



        fig.update_xaxes(type="date", row=1, col=1)
        fig.update_xaxes(type="date", row=2, col=1)
        fig.update_xaxes(type="date", row=3, col=1)
        fig.update_xaxes(type="date", row=4, col=1)

        fig.update_yaxes(type=scale_type, row=1, col=1)
        fig.update_yaxes(type=scale_type, row=2, col=1)
        fig.update_yaxes(type=scale_type, row=2, col=1)
        fig.update_yaxes(type=scale_type, row=3, col=1)

        fig.update_layout(dict (
            width=1250,
            height=1200,
            margin=dict(l=50, r=50, t=50, b=50),
        ))
        return fig



    @app.callback(
        Output('main_window_DR', 'figure'),
        [
            Input('country_drop_down', 'value'),
            Input('scale_type3', 'value'),
            Input('doubling-days', 'value'),
            Input('doubling-init', 'value'),
            Input('date-range-3', 'start_date'),
            Input('date-range-3', 'end_date'),
        ]
        )
    def update_confirmed_doublingRate_plot(country_list, scale_type, doubling_days, doubling_init, start_date, end_date):

        traces = []
        fig = go.Figure()

        max_days = 0
        date_plot = []

        for each in country_list:

            df_plot = df_input_large[(df_input_large['country'] == each) & 
                                     (df_input_large['confirmed_filtered'] >= doubling_init) & 
                                     (pd.to_datetime(df_input_large.date) >= pd.to_datetime(start_date)) &
                                     (pd.to_datetime(df_input_large.date) <= pd.to_datetime(end_date))
                                    ]
            df_plot = df_plot[['state','country','confirmed_filtered','date']].groupby(['country','date']).agg(np.mean).reset_index()

            if max_days < df_plot.shape[0]:
                max_days = df_plot.shape[0]
                date_plot = df_plot.date

            fig.add_trace(go.Scatter(dict(
                    x = df_plot.date,
                    y = df_plot['confirmed_filtered'],
                    mode = 'markers+lines',
                    opacity = 0.9,
                    name = each,
                )
            ))



        if (doubling_days>0) & (doubling_init>0):

            fig.add_trace(go.Scatter(dict(
                    x = date_plot,
                    y = calc_doubling_rate(doubling_init, np.arange(max_days), doubling_days),
                    mode = 'markers+lines',
                    opacity = 0.9,
                    name = "Doubling",
                )
            ))

        fig.update_layout(dict(
            width = 1150,
            height = 800,
            xaxis = {
                'title':'Timeline',
                'tickangle':-45,
                'nticks':20,
                'tickfont':dict(size=14,color="#7f7f7f"),
            },
            yaxis={
                'type':scale_type,
            },
            margin=dict(l=50, r=50, t=50, b=50),
        ))
        return fig



    @app.callback(
        Output('sir_chart', 'figure'),
        [Input('country_drop_down_sir', 'value'),
         Input('scale_type4', 'value'),
        ]
    )
    def update_SIR_model(country, scale_type):
        traces = []
        fig =go.Figure()

        country_data = df_analyse[country][35:150]
        ydata = np.array(country_data)
        fitted = np.array(df_SIR_data[country])

        fig.add_trace(go.Scatter(
            x = df_analyse['date'][35:150],
            y = ydata,
            mode = 'markers+lines',
            name = country+str(' - Truth'),
            opacity = 0.9
        ))
        fig.add_trace(go.Scatter(
            x = df_analyse['date'][35:150],
            y = fitted,
            mode = 'markers+lines',
            name = country + str(' - Simulation'),
            opacity = 0.9
        ))

        fig.update_layout(dict(
                width = 1250,
                height = 750,
                xaxis = {
                    'title': 'Days', #'Fit of SIR model for '+str(each)+' cases',
                    'tickangle': -45,
                    'nticks' : 20,
                    'tickfont' : dict(size = 14, color = '#7F7F7A')
                },
                yaxis = {
                    'title': 'Population Infected',
                    'type': scale_type
                },
                margin=dict(l=50, r=50, t=50, b=50)
            ))        
        return fig

    app.run_server(debug=True, use_reloader=False)
