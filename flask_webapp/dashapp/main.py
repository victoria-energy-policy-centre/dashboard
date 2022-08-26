# Import required libraries
import pickle
import dash
import pandas as pd
from dash.dependencies import Input, Output
from dash import dcc
from dash import html
import pandas as pd
import urllib
from flask import Flask
import plotly.graph_objects as go
import copy

# Setup app data 
def get_tech():
    return pd.read_csv('NEM_data/tech.csv',index_col=0)

def dictafy(data_list):
    res=[]
    for i in data_list:
        res.append({"label":i, "value": i})
    return res

def get_station_figures_old(station):
    station=station.replace('"','').replace('/','').replace('#','')
    with open(r'App_Figures/'+station+'.pickle', "rb") as input_file:
        station_figures = pickle.load(input_file)
    return station_figures

def save_dict_figures(figures):
    new_figures={}
    for station in figures.keys():
        station_figs=figures[station]
        new_station={}
        for t in station_figs.keys():
            if station_figs[t] !=None:
                new_station[t]=station_figs[t].to_dict()
            else:
                new_station[t]=None
        new_figures[station]=new_station
    return new_figures

def load_figures(type='station'):
    if type=='station':
        f = open('station_new_figures_highest_P.pickle', "rb")
    elif type=='FCAS':
        f = open('FCAS.pickle', "rb")
    elif type=='regional':    
        f = open('Regional.pickle', "rb")
    figures = pickle.load(f)
        
    return figures

def get_station_figures(station):
    station=station.replace('"','').replace('/','').replace('#','')
    station_figures=figures[station]
    return station_figures

def get_region_figures(region):
   
    region_figures=regional_figures[region]
    return region_figures

def get_FCAS_figures(region):
    FCAS_figures_r=FCAS_figures[region]
    return FCAS_figures_r

def get_data(fig,station):
    all_dff=[]
    for d in fig['data']:
        index=d['x']
        data=d['y']
        name=d['name']
        dff=pd.DataFrame(index=index,data=data,columns=[name]).tz_localize(None)
        all_dff.append(dff)
    all_dff=pd.concat(all_dff,axis=1)
    all_dff.columns=station+' - '+all_dff.columns 
    return all_dff

def resample_fig(figa,freq='Q',mode='mean'):

    for d in figa['data']:
            index=d['x']
            data=d['y']
            name=d['name']
            if mode=='mean':
                dff=pd.Series(index=index,data=data).tz_localize(None).resample(freq).mean()
            elif mode=='sum':
                dff=pd.Series(index=index,data=data).tz_localize(None).resample(freq).sum()
            
            d['x'] = dff.index
            d['y'] = dff.values
    return figa

# Create title Tab
def create_title():
     return [
        dcc.Store(id="aggregate_data"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        html.Div(
            [
                ## Add image
                html.Div(
                    [html.A([
                        html.Img(
                            src=app.get_asset_url("VEPC-transp.png"),
                            id="VEPC-Image",
                            style={
                                "height": "110px",
                                "width": "auto",
                                "margin-bottom": "10px",
                            },
                        )
                        
                    ],target='_blank',
                        href="https://www.vepc.org.au/"
                    ),
                        
                    ],
                   
                ),html.Br(),
                ## add title
                html.Div(
                    [
                        html.Div(
                            [
                                
                                html.H3(
                                    dcc.Markdown("**VEPC Data Dashboard (BETA)**"), style={"margin-top": "0px"}
                                )
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                ),
                # add VU Image 
                html.Div(
                    [## add VU image
                        #html.A(html.Img(
                        #    src=app.get_asset_url("1200px-Victoria_University.svg.png"),
                        #    id="VU-Image",
                         #   style={
                         #       "height": "70px",
                         #       "width": "auto",
                         #       "margin-bottom": "10px",
                         #   },
                        #)
                        #)
                    ],
                    className="one-third column",
                    id="button",
                ),
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px"},
        ),
       ## add generator tab
    ]

# Create generator Tab
def create_generator_tab():
        years=[str(y) for y in range(2012,2021)]
        return [html.Div(
            [
                 # add Selection panel
                html.Div(
                    [
                                               
                        html.P(dcc.Markdown("**Select fuel type:**"), className="control_label"),
                        dcc.RadioItems(
                            id="fuel_type",
                            options=fuel_types,
                            value="Black Coal",
                            labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        ),
                        html.P(dcc.Markdown("**Select station:**"), className="control_label"),
                        dcc.Dropdown(
                                    id='opt-dropdown',
                                    value='Bayswater Power Station'
                                    ),
                        #dcc.Loading(id="loading-1", children=[html.Div(id="loading-output-1")], type="default"),
                        html.P(dcc.Markdown("**Select data frequency:**"), className="control_label"),
                        dcc.RadioItems(
                            id="freq",
                            options=[{'label': 'Weekly', 'value': 'w'},
                                     {'label': 'Monthly', 'value': 'MS'},
                                     {'label': 'Quarterly', 'value': 'Q'},
                                     {'label': 'Annually', 'value': 'YS'}],
                            value="w",
                            labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        ),    
                        dcc.Graph(id="map")
                    ],
                    className="pretty_container four columns",
                    id="cross-filter-options",
                ),
                # add Station summary
                html.Div(
                        #Station title
                        [html.Div([html.H3(id='station',style={'text-align': 'center'}
                                   
                                ),
                                  dcc.Loading(
                                        id="loading-spinner",
                                        children=[html.Div([html.P(id="spinner")])],
                                        type="default",
                                    )],id="station_title",
                            className="pretty_container"),
                        
                         # Mini containers
                        ## markdown help http://commonmark.org/help
                        html.Div(
                            [
                                html.Div(
                                    [html.P(dcc.Markdown("**Region**"), style={"color": "dodgerblue",'text-align': 'center'}),
                                     html.H6(id="region", style={'text-align': 'center'}) ],
                                    id="region_view",
                                    className="mini_container",
                                ),
                                
                                html.Div(
                                    [html.P(dcc.Markdown("**Fuel type**"),style={"color": "forestgreen",'text-align': 'center'}),
                                     html.H6(id="fuel_type_r", style={'text-align': 'center'})],
                                    id="Fuel_type_view",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.P(dcc.Markdown("**Technology type**"),style={"color": "orangered",'text-align': 'center'}),
                                     html.H6(id="technology_type", style={'text-align': 'center'})],
                                    id="technology_type_view",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.P(dcc.Markdown("**Capacity**"),style={"color": "darkgreen",'text-align': 'center'}),
                                     html.H6(id="capacity", style={'text-align': 'center'})],
                                    id="capacity_view",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.P(dcc.Markdown("**Units**"),style={"color": "firebrick",'text-align': 'center'}),
                                     html.H6(id="units", style={'text-align': 'center'})],
                                    id="unit_view",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [ html.P(dcc.Markdown("**Owner**"),style={"color": "darkgoldenrod",'text-align': 'center'}),
                                     html.H6(id="participant", style={'text-align': 'center'})],
                                    id="participant_view",
                                    className="mini_container",
                                ),
                                ],
                            id="info2-container",
                            className="row flex-display",
                        ),
                        
                         
                        html.Div(
                            [dcc.Loading(
                            id="loading-dispatch",
                            children=[html.Div([html.H5('Generator Dispatch'),dcc.Graph(id='dispatch')]),
                                     html.A(
                                        html.Button("Download Data", id="dispatch-button"),
                                        #href="https://plot.ly/dash/pricing/",
                                        id='download-link_dispatch',
                                        download="Dispatch_data.csv",
                                        href="",
                                        key='dispatch',
                                        target="_blank"
                                      )],
                            type="circle")],
                            id="countGraphContainer",
                            className="pretty_container",
                        ),
                    ],
                    id="right-column",
                    className="eight columns",
                ),
            ],
            className="row flex-display",
        ),
       
        html.Div(
            [dcc.Loading(
                id="loading-time_bid",
                children=[html.Div([html.H5('Energy Market Bids'),dcc.Graph(id='time_bids')]),
                          html.A(
                            html.Button("Download Data", id="time_bids-button"),
                            #href="https://plot.ly/dash/pricing/",
                            id='download-link_time_bids',
                            download="Generator_bids.csv",
                            href="",
                            key='pricesetting',
                            target="_blank"
                          )
                         ],className="pretty_container six columns",
                type="circle"),

                dcc.Loading(
                id="loading-POE",
                children=[html.Div([html.H5('Daily Bid Profile'),
                         html.Div([html.P(dcc.Markdown("**Select year:**"), className="control_label"),
                        dcc.RadioItems(
                            id="year-select",
                            options=dictafy(years),
                            value='2019',
                            labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        )]),dcc.Graph(id='POE')])
                         ],className="pretty_container six columns",
                type="circle"),
                 
            ],
            className="row flex-display",
        ),
    
        html.Div(
            [ dcc.Loading(
            id="loading-VWAP",
            children=[html.Div([html.H5('Volume Weighted Average Price'),dcc.Graph(id='VWAP')]),
                     html.A(
                            html.Button("Download Data", id="VWAP-button"),
                            #href="https://plot.ly/dash/pricing/",
                            id='download-link_VWAP',
                            download="VWAP.csv",
                            href="",
                            key='VWAP',
                            target="_blank"
                          )
                     ],className="pretty_container six columns",
            type="circle"),
             dcc.Loading(
            id="pricesetting-VWAP",
            children=[html.Div([html.H5('Average Price when Setting the Market Clearing Price'),dcc.Graph(id='pricesetting'),
                          html.A(
                            html.Button("Download Data", id="pricesetting-button"),
                            #href="https://plot.ly/dash/pricing/",
                            id='download-link_pricesetting',
                            download="Price when pricesetting.csv",
                            href="",
                            key='pricesetting',
                            target="_blank"
                          )
                               ])],className="pretty_container six columns",
            type="circle")

            ],
            className="row flex-display",
        ),
                
        html.Div(
            [ dcc.Loading(
            id="loading-pricesetting_freq",
            children=[html.Div([html.H5('Frequency setting the market price in local region'),dcc.Graph(id='pricesetting_freq')]),
                     html.A(
                            html.Button("Download Data", id="pricesetting_freq-button"),
                            #href="https://plot.ly/dash/pricing/",
                            id='download-link_pricesetting_freq',
                            download="pricesetting_freq.csv",
                            href="",
                            key='pricesetting_freq',
                            target="_blank"
                          )
                     ],className="pretty_container six columns",
            type="circle"),
             dcc.Loading(
            id="loading-None",
            children=[html.Div([html.H5(''),#dcc.Graph(id=None),
                          #html.A(
                          #  html.Button("Download Data", id="None-button"),
                          #  #href="https://plot.ly/dash/pricing/",
                          #  id=None,#'download-link_interconector',
                          #  download="interconector.csv",
                          #  href="",
                          #  key='pricesetting',
                          #  target="_blank"
                          #)
                               ])],className="pretty_container six columns",
            type="circle")

            ],
            className="row flex-display",
        )
               ]

# Create Region Tab
def create_region_tab():
        
        return [html.Div(
            [
                 # add Selection panel
                html.Div(
                    [
                                               
                        html.P(dcc.Markdown("**Select Region:**"), className="control_label"),
                        dcc.RadioItems(
                            id="region-select",
                            options=regions,
                            value="VIC",
                            labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        ),

                        #dcc.Loading(id="loading-1", children=[html.Div(id="loading-output-1")], type="default"),
                        html.P(dcc.Markdown("**Select data frequency:**"), className="control_label"),
                        dcc.RadioItems(
                            id="freq_regional",
                            options=[{'label': 'Weekly', 'value': 'w'},
                                     {'label': 'Monthly', 'value': 'MS'},
                                     {'label': 'Quarterly', 'value': 'Q'},
                                     {'label': 'Annually', 'value': 'YS'}],
                            value="w",
                            labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        ),    
                        #dcc.Graph(id="map")
                    ],
                    className="pretty_container four columns",
                    id="cross-filter-options-region",
                ),
                # add region summary
                html.Div(
                        #Station title
                        [html.Div([html.H3(id='Region',style={'text-align': 'center'}
                                   
                                ),
                                  dcc.Loading(
                                        id="loading-spinner-regional",
                                        children=[html.Div([html.P(id="spinner_region")])],
                                        type="default",
                                    )],id="region_title",
                            className="pretty_container"),
                        
                         # Mini containers
                        ## markdown help http://commonmark.org/help
                         
                        html.Div(
                            [dcc.Loading(
                            id="loading-region-dispatch",
                            children=[html.Div([html.H5('Regional Fuel Mix'),dcc.Graph(id='fuel_mix_mean')]),
                                     html.A(
                                        html.Button("Download Data", id="fuel_mix_mean-button"),
                                        #href="https://plot.ly/dash/pricing/",
                                        id='download-link_fuel_mix_mean',
                                        download="fuel_mix_mean.csv",
                                        href="",
                                        key='dispatch',
                                        target="_blank"
                                      )],
                            type="circle")],
                            id="fuel_mix_meanGraphContainer",
                            className="pretty_container",
                        ),
                    ],
                    id="right-column-regional",
                    className="eight columns",
                ),
            ],
            className="row flex-display",
        ),
       
        html.Div(
            [dcc.Loading(
                id="loading-price",
                children=[html.Div([html.H5('Regional Wholesale Price'),dcc.Graph(id='price')]),
                          html.A(
                            html.Button("Download Data", id="price-button"),
                            #href="https://plot.ly/dash/pricing/",
                            id='download-link_price',
                            download="price.csv",
                            href="",
                            key='pricesetting',
                            target="_blank"
                          )
                         ],className="pretty_container six columns",
                type="circle"),
             dcc.Loading(
                id="loading-consumption",
                children=[html.Div([html.H5('Regional Consumption'),dcc.Graph(id='consumption')]),
                          html.A(
                            html.Button("Download Data", id="consumption-button"),
                            #href="https://plot.ly/dash/pricing/",
                            id='download-link_consumption',
                            download="consumption.csv",
                            href="",
                            key='pricesetting',
                            target="_blank"
                          )
                         ],className="pretty_container six columns",
                type="circle"),
    
            ],
            className="row flex-display",
        ),
    
        html.Div(
            [ dcc.Loading(
            id="loading-avil",
            children=[html.Div([html.H5('Total Regional Available Capacity'),dcc.Graph(id='avil')]),
                     html.A(
                            html.Button("Download Data", id="avil-button"),
                            #href="https://plot.ly/dash/pricing/",
                            id='download-link_avil',
                            download="avil.csv",
                            href="",
                            key='VWAP',
                            target="_blank"
                          )
                     ],className="pretty_container six columns",
            type="circle"),
             dcc.Loading(
            id="loading-interconector",
            children=[html.Div([html.H5('Interconnector flow'),dcc.Graph(id='interconector'),
                          html.A(
                            html.Button("Download Data", id="interconector-button"),
                            #href="https://plot.ly/dash/pricing/",
                            id='download-link_interconector',
                            download="interconector.csv",
                            href="",
                            key='pricesetting',
                            target="_blank"
                          )
                               ])],className="pretty_container six columns",
            type="circle")

            ],
            className="row flex-display",
        )]

# Create tabs (global variables)
tabs_styles = {
    'backgroundColor':'#FF9928'
    #'height': '44px'
}

tab_style = {
    'borderBottom': '1px solid #FFFFFF',
    'padding': '6px',
    'color':'#FFFFFF',#font
    'font-size': '100%',
    'backgroundColor': '#071F4E',
}

tab_selected_style = {
    'borderTop': '1px solid #FFFFFF',
    'borderBottom': '1px solid #FFFFFF',
    'backgroundColor': '#0E3E9B', #tabcolour
    'color': '#FF9928',#set font colour
    'padding': '6px',
}

def create_tabs(tabs):
    value=[t for t in tabs.keys()][0]
    return    [dcc.Tabs(id='main_tabs', value=value, style=tabs_styles,
            children=[ dcc.Tab(label=tab, value=tab,children=tabs[tab],style=tab_style,selected_style=tab_selected_style) for tab in tabs.keys()])]

def create_tab_contents(id_name='main_tab_content'):
    return [html.Div(id=id_name)]

# Temp Tab
def create_dev_tab():
    return [html.Div([

            html.H3(
                dcc.Markdown("**Page currently under development**"), style={"margin-top": "0px"}
                )])]

# Create FCAS Tab
def create_FCAS_tab():
    return [html.Div(
        [
            # add Selection panel
            html.Div(
                [

                    html.P(dcc.Markdown("**Select Region:**"), className="control_label"),
                    dcc.RadioItems(
                        id="region_FCAS-select",
                        options=regions,
                        value="VIC",
                        labelStyle={"display": "inline-block"},
                        className="dcc_control",
                    ),

                    # dcc.Loading(id="loading-1", children=[html.Div(id="loading-output-1")], type="default"),
                    html.P(dcc.Markdown("**Select data frequency:**"), className="control_label"),
                    dcc.RadioItems(
                        id="freq_regional_FCAS",
                        options=[{'label': 'Weekly', 'value': 'w'},
                                 {'label': 'Monthly', 'value': 'MS'},
                                 {'label': 'Quarterly', 'value': 'Q'},
                                 {'label': 'Annually', 'value': 'YS'}],
                        value="w",
                        labelStyle={"display": "inline-block"},
                        className="dcc_control",
                    ),
                    # dcc.Graph(id="map")
                ],
                className="pretty_container four columns",
                id="cross-filter-options-region_FCAS",
            ),
            # add Station summary
            html.Div(
                # Station title
                [html.Div([html.H3(id='Region_FCAS', style={'text-align': 'center'}

                                   ),
                           dcc.Loading(
                               id="loading-spinner-region_FCAS",
                               children=[html.Div([html.P(id="spinner_region_FCAS")])],
                               type="default",
                           )], id="region_FCAS_title",
                          className="pretty_container"),

                 # Mini containers
                 ## markdown help http://commonmark.org/help

                 html.Div(
                     [dcc.Loading(
                         id="loading-region_FCAS-dispatch",
                         children=[html.Div([html.H5('RAISE6SEC Price and Available Capacity'), dcc.Graph(id='RAISE6SEC')]),
                                   html.A(
                                       html.Button("Download Data", id="RAISE6SEC-button"),
                                       # href="https://plot.ly/dash/pricing/",
                                       id='download-link_RAISE6SEC',
                                       download="RAISE6SEC.csv",
                                       href="",
                                       key='RAISE6SEC_setting',
                                       target="_blank"
                                   )],
                         type="circle")],
                     id="RAISE6SECGraphContainer",
                     className="pretty_container",
                 ),
                 ],
                id="right-column-region_FCAS",
                className="eight columns",
            ),
        ],
        className="row flex-display",
    ),

        html.Div(
            [dcc.Loading(
                id="loading-RAISE60SEC",
                children=[html.Div([html.H5('RAISE60SEC Price and Available Capacity'), dcc.Graph(id='RAISE60SEC')]),
                          html.A(
                              html.Button("Download Data", id="RAISE60SEC-button"),
                              # href="https://plot.ly/dash/pricing/",
                              id='download-link_RAISE60SEC',
                              download="RAISE60SEC.csv",
                              href="",
                              key='RAISE60SECsetting',
                              target="_blank"
                          )
                          ], className="pretty_container six columns",
                type="circle"),
                dcc.Loading(
                    id="loading-RAISE5MIN",
                    children=[html.Div([html.H5('RAISE5MIN Price and Available Capacity'), dcc.Graph(id='RAISE5MIN')]),
                              html.A(
                                  html.Button("Download Data", id="RAISE5MIN-button"),
                                  # href="https://plot.ly/dash/pricing/",
                                  id='download-link_RAISE5MIN',
                                  download="RAISE5MIN.csv",
                                  href="",
                                  key='RAISE60SECsetting',
                                  target="_blank"
                              )
                              ], className="pretty_container six columns",
                    type="circle"),

            ],
            className="row flex-display",
        ),

        html.Div(
            [dcc.Loading(
                id="LOWER6SEC_loading",
                children=[html.Div([html.H5('LOWER6SEC Price and Available Capacity'), dcc.Graph(id='LOWER6SEC')]),
                          html.A(
                              html.Button("Download Data", id="LOWER6SEC-button"),
                              # href="https://plot.ly/dash/pricing/",
                              id='download-link_LOWER6SEC',
                              download="LOWER6SEC.csv",
                              href="",
                              key='LOWER6SEC',
                              target="_blank"
                          )
                          ], className="pretty_container six columns",
                type="circle"),
                dcc.Loading(
                    id="loading-LOWER60SEC",
                    children=[html.Div([html.H5('LOWER60SEC Price and Available Capacity'), dcc.Graph(id='LOWER60SEC'),
                                        html.A(
                                            html.Button("Download Data", id="LOWER60SEC-button"),
                                            # href="https://plot.ly/dash/pricing/",
                                            id='download-link_LOWER60SEC',
                                            download="LOWER60SEC.csv",
                                            href="",
                                            key='RAISE60SECsetting',
                                            target="_blank"
                                        )
                                        ])], className="pretty_container six columns",
                    type="circle")

            ],
            className="row flex-display",
        ),
        html.Div(
            [dcc.Loading(
                id="LOWER5MIN_loading",
                children=[html.Div([html.H5('LOWER5MIN Price and Available Capacity'), dcc.Graph(id='LOWER5MIN')]),
                          html.A(
                              html.Button("Download Data", id="LOWER5MIN-button"),
                              # href="https://plot.ly/dash/pricing/",
                              id='download-link_LOWER5MIN',
                              download="LOWER5MIN.csv",
                              href="",
                              key='LOWER5MINsetting',
                              target="_blank"
                          )
                          ], className="pretty_container six columns",
                type="circle")

            ],
            className="row flex-display",
        )]

fuel_stations={}

tech = pd.read_csv('NEM Registration and Exemption List_Oct 2019.csv').set_index('DUID')
tech = tech.loc[~tech.index.duplicated(keep='first')]
tech['Fuel Source - Descriptor']=tech['Fuel Source - Descriptor'].str.replace(' / Fuel Oil','').str.replace(' / Diesel','')
tech['Reg Cap (MW)']=tech['Reg Cap (MW)'].str.replace('-','0').astype(float)
grouped_tech=tech.groupby(['Fuel Source - Descriptor','Station Name']).first().loc[['Black Coal','Brown Coal','Water','Natural Gas','Diesel','Solar','Wind']]
tech['Physical Unit No.']=tech['Physical Unit No.'].str.split('-').str.get(1).fillna(1)
tech['Physical Unit No.']=tech['Physical Unit No.'].str.split(',').str.get(1).fillna(1)
tech['Physical Unit No.']=tech['Physical Unit No.'].str.split(' ').str.get(1).fillna(1).astype(int)

grouped_tech_sum=tech.groupby(['Fuel Source - Descriptor','Station Name']).sum().loc[['Black Coal','Brown Coal','Water','Natural Gas','Diesel','Solar','Wind']]

grouped_tech['Reg Cap (MW)']=grouped_tech_sum['Reg Cap (MW)']
grouped_tech['Physical Unit No.']=grouped_tech_sum['Physical Unit No.']
grouped_tech['fuel_type']=grouped_tech.index.get_level_values(0)

lat_lon=pd.read_csv('data/MajorPowerStations_v2.csv').set_index('NAME')
lat_lon['lat_lon']=lat_lon[['LATITUDE','LONGITUDE']].values.tolist()
lat_lon.index=lat_lon.index.str.split().str.get(0)
lat_lon = lat_lon.loc[~lat_lon.index.duplicated(keep='first')]
grouped_tech['lat_lon']=grouped_tech.index.get_level_values(1).str.split().str.get(0).map(lat_lon['lat_lon'])

fuel_types=dictafy(grouped_tech.index.get_level_values(0).unique())
regions=dictafy(['VIC','NSW','QLD','SA','TAS'])

for ind in grouped_tech.index.get_level_values(0).unique():
    fuel_stations[ind]=dictafy(grouped_tech.loc[ind].index.to_list())

    import pickle 

figures=load_figures('station')
regional_figures=load_figures('regional')
FCAS_figures=load_figures('FCAS')

figures['Vales Point B Power Station']=figures['Vales Point "B" Power Station']

# VEPC APP
server = Flask(__name__)

VALID_USERNAME_PASSWORD_PAIRS = {
    'VEPC-User': 'keepingthelightson',
    'Bruce': 'Mountain',
    'Steven': 'Percy'
}

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],server = server
)

app.title='VEPC Dashboard'

# Create global chart template
mapbox_access_token = "pk.eyJ1IjoiamFja2x1byIsImEiOiJjajNlcnh3MzEwMHZtMzNueGw3NWw5ZXF5In0.fk8k06T96Ml9CLGgKmk81w"

# Add laybout functions to layout
tab_titles=['Regional NEM','Renewable Summary','NEM Generators','NEM FCAS Markets','Gas Markets']
tabs={}

tabs[tab_titles[0]]=create_region_tab()
tabs[tab_titles[1]]=create_dev_tab()
tabs[tab_titles[2]]=create_generator_tab()
tabs[tab_titles[3]]=create_FCAS_tab()
tabs[tab_titles[4]]=create_dev_tab()

layout=[]
layout.extend(create_title())
layout.extend(create_tabs(tabs=tabs))
layout.extend(create_tab_contents(id_name='main_tab_content'))

# Create Layout
app.layout = html.Div( layout,     id="mainContainer",
    style={"height": "100%",'backgroundColor':'#FFFFFF','margin': 0,"display": "flex", "flex-direction": "column"},
)

@app.callback(
    dash.dependencies.Output('opt-dropdown', 'options'),
    [dash.dependencies.Input('fuel_type', 'value')]
)

def update_date_dropdown(fuel_type):
    return fuel_stations[fuel_type]

@app.callback(
    Output("station", "children"),
    [ Input("opt-dropdown", "value")]
)

def get_technology_type(station):
    return station

@app.callback(
    Output("Region_FCAS", "children"),
    [ Input("region_FCAS-select", "value")]
)

def get_technology_type(station):
    return station

@app.callback(
    Output("Region", "children"),
    [ Input("region-select", "value")]
)

def get_technology_type(Region):
    regions={'VIC':'Victoria',
            'NSW': 'New South Wales',
            'QLD':'Queensland',
            'SA':'South Australia',
            'TAS':'Tasmania'}
    return regions[Region]

@app.callback(
    [Output("region", "children"),
    Output("capacity", "children"),
    Output("technology_type", "children"),
    Output("participant", "children"),
    Output("units", "children"),
    Output("fuel_type_r", "children")],
    [  Input("fuel_type", "value"),
        Input("opt-dropdown", "value")],
)

def get_technology_type(fuel, station):
    
    technology_type = grouped_tech.loc[(fuel,station),'Technology Type - Descriptor']
    fuel_type = grouped_tech.loc[(fuel,station),'fuel_type']
    region = grouped_tech.loc[(fuel,station),'Region'].replace('1','')
    capacity = str(int(grouped_tech.loc[(fuel,station),'Reg Cap (MW)']))+' MW'
    participant = grouped_tech.loc[(fuel,station),'Participant'].split()[0]
    units = grouped_tech.loc[(fuel,station),'Physical Unit No.']

    return [region,capacity,technology_type,participant,units,fuel_type]

@app.callback(
    
    Output("map", "figure"),
    [Input("fuel_type", "value"),
     Input("opt-dropdown", "value")]
)

def get_map(fuel, station):
    import plotly.graph_objects as go
    try:
        mapbox_access_token = 'pk.eyJ1Ijoic3BlcjU5ODkiLCJhIjoiY2s4cGR1bXhlMDIwNjNncno5b2FvM3c0cCJ9.o1YxNh6bBd7qqAlKodVQgw'
        lat_long = grouped_tech.loc[(fuel,station),'lat_lon']
        name=station
        fig = go.Figure(go.Scattermapbox(
                lat=[lat_long[0]],
                lon=[lat_long[1]],
                #mode='markers',
                name=name,
                mode ="markers+text",
                textposition="middle right" ,
                #text = ,
                marker=go.scattermapbox.Marker(
                    size=8
                ),
                text=[station],
            ))

        fig.update_layout(
            margin = dict(l = 0, r = 0, t = 0, b = 0),
            hovermode='closest',
            mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=0,
                center=go.layout.mapbox.Center(
                    lat=lat_long[0],
                    lon=lat_long[1]
                ),
                pitch=0,
                zoom=4
            )
        )
    except:
        fig=None
    return fig

@app.callback(
    [Output('RAISE6SEC', "figure"),
    Output('RAISE60SEC', "figure"),
    Output('RAISE5MIN', "figure"),
    Output('LOWER6SEC', "figure"),
    Output('LOWER60SEC', "figure"),
    Output('LOWER5MIN', "figure"),
    Output('spinner_region_FCAS', "children") ],
    [ Input("region_FCAS-select", "value"),
        Input("freq_regional_FCAS", "value")
        ],
)
def get_FCAS_app_figures(region,freq):
    empty=None
    region_figures=get_FCAS_figures(region)
    RAISE6SEC=go.Figure(region_figures['RAISE6SEC price+avil'])
    if freq !='w':
        RAISE6SEC=resample_fig(copy.deepcopy(RAISE6SEC),freq=freq,mode='mean')

    # fuel_mix_mean_percentage
    RAISE60SEC=go.Figure(region_figures['RAISE60SEC price+avil'])
    if freq !='w':
        RAISE60SEC=resample_fig(copy.deepcopy(RAISE60SEC),freq=freq,mode='mean')

    #'price'
    RAISE5MIN=go.Figure(region_figures['RAISE5MIN price+avil'])
    if freq !='w':
        RAISE5MIN=resample_fig(copy.deepcopy(RAISE5MIN),freq=freq,mode='mean')

    #'avil'
    LOWER6SEC=go.Figure(region_figures['LOWER6SEC price+avil'])
    if freq !='w':
        LOWER6SEC=resample_fig(copy.deepcopy(LOWER6SEC),freq=freq,mode='mean')

    # 'consumption'
    LOWER60SEC=go.Figure(region_figures['LOWER60SEC price+avil'])
    if freq !='w':
        LOWER60SEC=resample_fig(copy.deepcopy(LOWER60SEC),freq=freq,mode='sum')

    #'demand_avil'
    LOWER5MIN=go.Figure(region_figures['LOWER5MIN price+avil'])
    if freq !='w':
        LOWER5MIN=resample_fig(copy.deepcopy(LOWER5MIN),freq=freq,mode='mean')

    #'interconector'
    spinner_region_FCAS=''

    #return ['fuel_mix_mean', 'fuel_mix_mean_percentage', 'price', 'avil', 'consumption', 'demand_avil', 'interconector']
    return [RAISE6SEC, RAISE60SEC, RAISE5MIN, LOWER6SEC, LOWER60SEC, LOWER5MIN, spinner_region_FCAS]

@app.callback(
    [Output('fuel_mix_mean', "figure"),
    Output('price', "figure"),
    Output('avil', "figure"),
    Output('consumption', "figure"),
    Output('interconector', "figure"),
    Output('spinner_region', "children") ],
    [ Input("region-select", "value"),
        Input("freq_regional", "value")
        ],
)
def get_region_app_figures(region,freq):
    empty=None
    try:
        region_figures=get_region_figures(region)
    except:
        region_figures=None
    #fuel_mix_mean
    try:
        fuel_mix_mean=region_figures['fuel_mix_mean']
        if freq !='w':
            fuel_mix_mean=resample_fig(copy.deepcopy(fuel_mix_mean),freq=freq,mode='mean')
    except:
        fuel_mix_mean = empty

    #   fuel_mix_mean_percentage
    fuel_mix_mean_percentage = empty 
    #'price'
    try:
        price=region_figures['price']
        if freq !='w':
            price=resample_fig(copy.deepcopy(price),freq=freq,mode='mean')
    except:
        price = empty 
    #'avil'
    try:
        avil=region_figures['avil']
        if freq !='w':
            avil=resample_fig(copy.deepcopy(avil),freq=freq,mode='mean')
    except:
        avil = empty 
    # 'consumption'
    try:
        consumption=region_figures['consumption']
        if freq !='w':
            consumption=resample_fig(copy.deepcopy(consumption),freq=freq,mode='sum')
    except:
        consumption = empty 
    #'demand_avil'
    try:
        demand_avil=region_figures['demand_avil']
        if freq !='w':
            demand_avil=resample_fig(copy.deepcopy(demand_avil),freq=freq,mode='mean')
    except:
        demand_avil = empty 
    #'interconector'
    try:
        interconector=region_figures['interconector']
        if freq !='w':
            interconector=resample_fig(copy.deepcopy(interconector),freq=freq,mode='mean')
    except:
        interconector = empty 

    spinner_region=''

    #return ['fuel_mix_mean', 'fuel_mix_mean_percentage', 'price', 'avil', 'consumption', 'demand_avil', 'interconector']
    return [fuel_mix_mean,price, avil, consumption,  interconector,spinner_region]

# Download Callbacks
@app.callback(
    
    [Output("time_bids", "figure"),
    Output("POE", "figure"),
    Output("dispatch", "figure"),
    Output("VWAP", "figure"),
    Output("pricesetting", "figure"),
    Output("pricesetting_freq", "figure"),
    Output("spinner", "children")],
    [ Input("opt-dropdown", "value"),
      Input("year-select", "value"),
      Input("freq", "value")
     ],
)

def get_app_station_figures(station, year,freq):
    empty=None
    if 'Vales' in station:
        station='Vales Point "B" Power Station'
    try:
        station_figures=get_station_figures(station)
    except:
        station_figures=None
    try:
        POE=station_figures[year]
        
        if POE==None:
            time_bids = empty
    except:
        POE = empty 
  

    try:
        time_bids = station_figures['time_bids']
        if freq !='w':
            time_bids=resample_fig(copy.deepcopy(time_bids),freq=freq,mode='mean')
       
        if time_bids==None:
            time_bids = empty
    except:
        time_bids = empty

    try:    
        dispatch=station_figures['dispatch']
        if freq !='w':
            dispatch=resample_fig(copy.deepcopy(dispatch),freq=freq,mode='mean')
        
        #fig.update_yaxes(automargin=True)
        if dispatch==None:
            dispatch = empty
        
    except:
        dispatch = empty
    try:
        VWAP=station_figures['VWAP']
        if freq !='w':
            VWAP=resample_fig(copy.deepcopy(VWAP),freq=freq,mode='mean')
        
        if VWAP==None:
            VWAP = empty
    except:
        VWAP = empty
    try:
        pricesetting=station_figures['pricesetting']
        if freq !='w':
            
            pricesetting=resample_fig(copy.deepcopy(pricesetting),freq=freq,mode='mean')
       
        if pricesetting==None:
            pricesetting = empty
    except:
        pricesetting_freq = empty
    try:
        pricesetting_freq=station_figures['pricesetting_freq']
        if freq !='w':
            
            pricesetting_freq=resample_fig(copy.deepcopy(pricesetting_freq),freq=freq,mode='mean')
       
        if pricesetting_freq==None:
            pricesetting_freq = empty
    except:
        pricesetting_freq = empty
    #return dispatch
    spinner=''
    try: 
        return [time_bids,POE,dispatch,VWAP,pricesetting,pricesetting_freq,spinner]
    except:
        return [None,None,None,None,None,None,None]

# Download Callbacks
#RAISE6SEC
@app.callback(
    dash.dependencies.Output('download-link_RAISE6SEC', 'href'),
    [Input("region_FCAS-select", "value")])
def update_download_link(station):
    variable='RAISE6SEC price+avil'
    fig=get_FCAS_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

#RAISE60SEC
@app.callback(
    dash.dependencies.Output('download-link_RAISE60SEC', 'href'),
    [Input("region_FCAS-select", "value")])
def update_download_link(station):
    variable='RAISE60SEC price+avil'
    fig=get_FCAS_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

#RAISE5MIN
@app.callback(
    dash.dependencies.Output('download-link_RAISE5MIN', 'href'),
    [Input("region_FCAS-select", "value")])
def update_download_link(station):
    variable='RAISE5MIN price+avil'
    fig=get_FCAS_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

#LOWER6SEC
@app.callback(
    dash.dependencies.Output('download-link_LOWER6SEC', 'href'),
    [Input("region_FCAS-select", "value")])
def update_download_link(station):
    variable='LOWER6SEC price+avil'
    fig=get_FCAS_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

#LOWER5MIN
@app.callback(
    dash.dependencies.Output('download-link_LOWER5MIN', 'href'),
    [Input("region_FCAS-select", "value")])
def update_download_link(station):
    variable='LOWER5MIN price+avil'
    fig=get_FCAS_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

#LOWER60SEC
@app.callback(
    dash.dependencies.Output('download-link_LOWER60SEC', 'href'),
    [Input("region_FCAS-select", "value")])
def update_download_link(station):
    variable='LOWER60SEC price+avil'
    fig=get_FCAS_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

# The update_download_function is overriden after each callback below. 
def update_download_link(station):
    variable='fuel_mix_mean'
    fig=get_region_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

def update_download_link(station):
    variable='price'
    fig=get_region_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

def update_download_link(station):
    variable='avil'
    fig=get_region_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

def update_download_link(station):
    variable='consumption'
    fig=get_region_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

def update_download_link(station):
    variable='interconector'
    fig=get_region_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

def update_download_link(station):
    if 'Vales' in station:
        station='Vales Point "B" Power Station'
    variable='dispatch'
    fig=get_station_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

def update_download_link(station):
    if 'Vales' in station:
        station='Vales Point "B" Power Station'
    variable='VWAP'
    fig=get_station_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

def update_download_link(station):
    if 'Vales' in station:
        station='Vales Point "B" Power Station'
    variable='pricesetting'
    fig=get_station_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

def update_download_link(station):
    if 'Vales' in station:
        station='Vales Point "B" Power Station'
    variable='pricesetting_freq'
    fig=get_station_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

def update_download_link(station):
    if 'Vales' in station:
        station='Vales Point "B" Power Station'
    variable='time_bids'
    fig=get_station_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

# Callbacks

# Price
@app.callback(
    dash.dependencies.Output('download-link_fuel_mix_mean', 'href'),
    [Input("region-select", "value")])
def update_download_link(station):
    variable='fuel_mix_mean'
    fig=get_region_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

# Price
@app.callback(
    dash.dependencies.Output('download-link_price', 'href'),
    [Input("region-select", "value")])
def update_download_link(station):
    variable='price'
    fig=get_region_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

# Avil
@app.callback(
    dash.dependencies.Output('download-link_avil', 'href'),
    [Input("region-select", "value")])
def update_download_link(station):
    variable='avil'
    fig=get_region_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

# Consumption
@app.callback(
    dash.dependencies.Output('download-link_consumption', 'href'),
    [Input("region-select", "value")])
def update_download_link(station):
    variable='consumption'
    fig=get_region_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string


# Interconnector
@app.callback(
    dash.dependencies.Output('download-link_interconector', 'href'),
    [Input("region-select", "value")])
def update_download_link(station):
    variable='interconector'
    fig=get_region_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

# Dispatch
@app.callback(
    dash.dependencies.Output('download-link_dispatch', 'href'),
    [Input("opt-dropdown", "value")])
def update_download_link(station):
    if 'Vales' in station:
        station='Vales Point "B" Power Station'
    variable='dispatch'
    fig=get_station_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string


# VWAP
@app.callback(
    dash.dependencies.Output('download-link_VWAP', 'href'),
    [Input("opt-dropdown", "value")])
def update_download_link(station):
    if 'Vales' in station:
        station='Vales Point "B" Power Station'
    variable='VWAP'
    fig=get_station_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

# Pricesetting
@app.callback(
    dash.dependencies.Output('download-link_pricesetting', 'href'),
    [Input("opt-dropdown", "value")])
def update_download_link(station):
    if 'Vales' in station:
        station='Vales Point "B" Power Station'
    variable='pricesetting'
    fig=get_station_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

# Pricesetting_freq
@app.callback(
    dash.dependencies.Output('download-link_pricesetting_freq', 'href'),
    [Input("opt-dropdown", "value")])
def update_download_link(station):
    if 'Vales' in station:
        station='Vales Point "B" Power Station'
    variable='pricesetting_freq'
    fig=get_station_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

# Time_bids
@app.callback(
    dash.dependencies.Output('download-link_time_bids', 'href'),
    [Input("opt-dropdown", "value")])
def update_download_link(station):
    if 'Vales' in station:
        station='Vales Point "B" Power Station'
    variable='time_bids'
    fig=get_station_figures(station)[variable]
    dff=get_data(fig,station)
    csv_string = dff.to_csv(encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

# Main
if __name__ == "__main__":
    app.run_server(debug = False, port="8050")