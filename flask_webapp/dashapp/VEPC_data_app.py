# Import required libraries
import itertools
import pickle
import dash
import pandas as pd
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html
import os
import pandas as pd
import urllib
import plotly.graph_objects as go
from datetime import datetime as dt
from flask_webapp.dashapp.plot_functions import *

import dash_bootstrap_components as dbc
from dash import html
from dash.dependencies import Input, Output, State
import ast

thirty_minute_text="A maximum of 30 days of 30-minute data will be displayed in the figures. The full time period data is accessible through the download button. A maximum of one region can be selected."
interconnectors=['N-Q-MNSP1', 'NSW1-QLD1', 'T-V-MNSP1', 'V-S-MNSP1', 'V-SA','VIC1-NSW1']
footer='© 2020. Victoria Energy Policy Centre, Victoria University, Melbourne, Australia.'

region_names = {'All regions': 'All Regions',
                       'VIC': 'Victoria',
                       'NSW': 'New South Wales',
                       'QLD': 'Queensland',
                       'SA': 'South Australia',
                       'TAS': 'Tasmania'}

button_gen_style = {
    "float": 'right',
    'text-transform': 'none'
}

button_style = {
    'color':'#FFFFFF',#font
    'backgroundColor': '#0E3E9B',
}

def create_modal(data_type='VWAP'):
    modal=dcc.ConfirmDialogProvider(
            children=html.Button(
                'Info',style={'backgroundColor': 'seagreen','color':'#FF9928'}
            ),
            id='danger-danger',
            message='This show the volume weighted average price for the selected statio\n Data Souce: AEMO NEMWEB'
    )
    return modal

def get_tech():
    return pd.read_csv('flask_webapp/dashapp/NEM_data/tech.csv',index_col=0)

def dictafy(data_list,replace_states=True):
    res=[]
    if len(data_list)>0:
        try:
            data_list.sort()
        except:
            data_list=data_list.sort_values()
    for i in data_list:
        if replace_states:
            lab=i.replace('VIC','Victoria').replace('NSW','New South Wales').replace('TAS','Tasmania').replace('SA','South Australia').replace('QLD','Queensland')
        else:
            lab=i
        res.append({"label":lab, "value": i})
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
        f = open('flask_webapp/dashapp/station_new_figures_highest_P.pickle', "rb")
    elif type=='FCAS':
        f = open('flask_webapp/dashapp/FCAS.pickle', "rb")
    elif type=='regional':    
        f = open('flask_webapp/dashapp/Regional.pickle', "rb")
    figures = pickle.load(f)
        
    return figures

def MW_scale(d, scale):
    for c in d.columns:
        d[c] = scale * d[c]
    return d

def get_data(fig,station):
    all_dff=[]
    try:
        for d in fig['data']:
            index=d['x']
            data=d['y']
            name=d['name']
            dff=pd.DataFrame(index=index,data=data,columns=[name]).tz_localize(None)
            all_dff.append(dff)
        all_dff=pd.concat(all_dff,axis=1)
        all_dff.columns=station+' - '+all_dff.columns 
    except:
         return pd.DataFrame(index=['No data available'])
    return all_dff

def create_download_button(ID):
    return html.A(
            dbc.Button("Download Data", id=ID+"_mean-button", outline=True, color="secondary"),#,style=button_style),
            #href="https://plot.ly/dash/pricing/",
            id='download-link_'+ID,
            download=Info_data.loc[ID,'figure']+".csv",
            href="",
            key=ID,
            target="_blank"
          )

def create_graph_container(ID,columns='six'):
    return html.Div([dcc.Loading(
                id="loading-"+ID,
                children=[html.Div([html.H5(Info_data.loc[ID,'figure']),dcc.Graph(id=ID)])],className=columns+" columns",
                type="circle"),html.Div([generate_modal(ID),create_download_button(ID)],className="buttons-display")],className="pretty_container "+columns+" columns")

# Create generator Tab
def create_generator_tab(regions,station_end_date):
    type='gen'
    return [html.Div(
            [
                 # add Selection panel
                html.Div(
                    [html.Div(html.P(dcc.Markdown(tab_data.loc['Generators','text']),className="control_label"), className='pretty_container_info') ,
                        #html.P(dcc.Markdown(tab_data.loc['gen','text']), className="control_label"),
                        html.H5(dcc.Markdown("**Data Select**"), className="control_label"),
                     html.Div([
                        html.P(dcc.Markdown("**1) Select Regions:**"), className="control_label"),
                        dcc.Dropdown(
                            id="generator_region",
                            options=regions,
                            value=["All regions"],multi=True,
                            #labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        ), 

                        html.P(dcc.Markdown("**2) Select fuel types:**"), className="control_label"),
                        dcc.Dropdown(
                            id="fuel_type",
                            options=fuel_types,
                            value=["Battery Storage"],multi=True,
                            #labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        ),
                         html.P(dcc.Markdown("**3) Select station:**"), className="control_label"),
                         dcc.Dropdown(
                             id='opt-dropdown',
                             value=['Hornsdale Power Reserve (Generation)'], multi=True,
                         ), ], id="station_sel",
                         className=""),
                         dcc.RadioItems(
                             id="scheduled_type",
                             options=classification_types,
                             value='Scheduled/Semi-Scheduled',
                             labelStyle={"display": "inline-block"},
                             className="dcc_control",
                         ),
                         html.P(dcc.Markdown("**4) Select date range and data frequency:**"), className="control_label"),
                         dcc.DatePickerRange(
                             id='station-date-range',
                             min_date_allowed=dt(2012, 1, 1),
                             max_date_allowed=dt(2023, 1, 1),
                             initial_visible_month=dt(2012, 1, 1),
                             start_date=dt(2018, 1, 1).date(),
                             end_date=station_end_date.date(),
                             display_format='DD/MM/YYYY',
                         ),
                         dcc.Dropdown(
                             id="freq",
                             options=[{'label': 'Daily', 'value': 'd'},
                                      {'label': 'Weekly', 'value': 'w'},
                                      {'label': 'Monthly', 'value': 'MS'},
                                      {'label': 'Quarterly', 'value': 'Q'},
                                      {'label': 'Annually', 'value': 'ys'}],
                             value="d",
                             # labelStyle={"display": "inline-block"},
                             className="dcc_control",
                         ),
                         html.P(dcc.Markdown("**5) Select units:**"),
                                className="control_label"),

                         dcc.RadioItems(
                             id="Generator_Energy_type",
                             options=[{'label': 'Total Energy (MWh)', 'value': True},
                                      {'label': 'Average Power (MW)', 'value': False}, ],
                             value=False,
                             #labelStyle={"display": "inline-block"},
                             className="Generator_Energy_type",
                         ),


                        #html.P(dcc.Markdown("**Select station:**"), className="control_label"),



                         html.Div([html.Button(
                             "Load Data", id=type + '_generate', style=button_gen_style
                         ), ], style={'padding': 20}),

                    ],
                    className="pretty_container four columns",
                    id="cross-filter-options_S",
                ),
                # add Station summary
                html.Div(
                        #Station title
                        [html.Div([html.H3(id='station_name',style={'text-align': 'center'}),
                                  dcc.Loading(
                                        id="loading-spinner_gen",
                                        children=[html.Div([html.P()])],
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
                                    [html.P(dcc.Markdown("**Maximum Capacity**"),style={"color": "darkgreen",'text-align': 'center'}),
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
                            className="flex-display",
                        ),

                         html.Div(
                             [html.Div(
                                  [dcc.Loading(
                                      id="loading-" + type + "-dispatch",
                                      children=[html.Div([html.H5(Info_data.loc['scada', 'figure']),
                                                          dcc.Graph(id='scada')]),
                                                html.Div(
                                                    [generate_modal('scada'),
                                                     create_download_button('scada')],
                                                    className="buttons-display")],
                                      type="circle")],
                                  id="scada_GraphContainer",
                                  className="pretty_container",
                              ),
                              ],
                             id="right-columns-" + type,
                             #className="eight columns",
                             className="flex-display",
                         ),
                    ],
                    id="right-column_gens_22",
                    className="eight columns",
                ),
            ],
            className="flex-display",
        ),
        html.Div(
            [create_graph_container('cfactor'), create_graph_container('NEM_bids')],
            className="flex-display",
        ),
        html.Div(
            [create_graph_container('max_avil'), create_graph_container('pricesetting_freq')],
            className="flex-display",
        ),
        html.Div(
            [create_graph_container('min_demand'),create_graph_container('pricesetting')],
            className="flex-display",
        ),
        #html.Div(
        #    [create_graph_container('VWAP')],
        #    className="flex-display",
        #),
        html.Br(),
        html.Div(footer, style={'clear':'both'},className='footer')

    ]

def create_interconnector_tab(interconnectors, regional_end_date):
    type='interconnector'
    return [html.Div(
        [
            # add Selection panel
            html.Div(
                [html.Div(html.P(dcc.Markdown(tab_data.loc['interconnectors','text']),className="control_label"), className='pretty_container_info') ,
                    html.P(dcc.Markdown("**Select Region:**"), className="control_label"),
                    dcc.Dropdown(
                        id=type+"-region-select",
                        options=dictafy(interconnectors, replace_states=False),
                        value="VIC1-NSW1",
                        className="dcc_control",
                    ),
                    html.P(dcc.Markdown("**Select date range:**"), className="control_label"),
                    dcc.DatePickerRange(
                        id=type+'-date-range',
                        min_date_allowed=dt(2012, 1, 1),
                        max_date_allowed=dt(2023, 1, 1),
                        initial_visible_month=dt(2012, 1, 1),
                        start_date=dt(2016, 1, 1).date(),
                        end_date=regional_end_date.date(),
                        display_format='DD/MM/YYYY',
                    ),
                    html.P(dcc.Markdown("**Select data frequency:**"), className="control_label"),
                    dcc.Dropdown(
                        id="freq_"+type,
                        options=[{'label': '30-minute', 'value': '30T'},
                                 {'label': 'Daily', 'value': 'd'},
                                 {'label': 'Weekly', 'value': 'w'},
                                 {'label': 'Monthly', 'value': 'MS'},
                                 {'label': 'Quarterly', 'value': 'Q'},
                                 {'label': 'Annually', 'value': 'ys'}],
                        value="w",
                        className="dcc_control",
                    ),
                    #html.Hr(),[
                    html.Div([html.Button(
                        "Load Data", id=type + '_generate', style=button_gen_style
                    ), ], style={'padding': 20}),

                    html.Div([dbc.Alert(
                        thirty_minute_text,
                        color="primary",
                        id=type + "-alert-fade",
                        dismissable=True,
                        is_open=True,
                    ), ], style={'padding': 40}),
                ],
                className="pretty_container four columns",
                id="cross-filter-options-"+type,
            ),

            # add region summary
            html.Div(
                [html.Div([html.H3(id="Region_"+type, style={'text-align': 'center'}),
                           dcc.Loading(
                               id="loading-spinner-"+type,
                               children=[html.Div([html.P(id="spinner_interconnector")])],
                               type="default",
                           )], id=type+"_title",
                          className="pretty_container"),
                 html.Div(
                     [dcc.Loading(
                         id="loading-"+type+"-dispatch",
                         children=[html.Div([html.H5(Info_data.loc['interconnector_flow','figure']), dcc.Graph(id='interconnector_flow')]),
                                   html.Div(
                                       [generate_modal('interconnector_flow'), create_download_button('interconnector_flow')],
                                       className="buttons-display")],
                         type="circle")],
                     id="interconnector_flow_GraphContainer",
                     className="pretty_container",
                 ),
                 ],
                id="right-column-"+type,
                className="eight columns",
            ),
        ],
        className="flex-display",
    ),
    html.Br(),
    html.Div([footer,], style={'clear': 'both'}, className='footer')
    ]

def create_widget(fig):
    #type='widget'
    #button = dbc.Button("Block button", color="primary", block=True)
    return [dcc.Graph(figure=fig,style = {'height': '80vh', 'padding':0, 'border':0}),
                      html.A(dbc.Button('>> Launch VEPC NEM Dashboard',  size="lg",outline=False, color='info',style={'padding':0, 'margin':0,'max-width':'90%','display': 'block', 'margin-left': 'auto', 'margin-right': 'auto','font-weight': 'bold','text-transform': 'none'}),

                                        #style={'text - transform': 'lowercase','color':'white','background-image': 'linear-gradient(#000046, #1CB5E0)',
                        #'box-shadow': '0 8px 16px 0 rgba(0,0,0,0.2), 0 6px 20px 0 rgba(0,0,0,0.19)',

                       # 'font-size': '3vh'}),style = {'height': '10vh','align': 'center'},#071F4E
    href='https://nemdashboard.com.au/regional', target='_blank',style= {'text-decoration': 'none', 'margin-left': 'auto','padding':0}),
         html.P(dcc.Markdown("A free online resource for Australian energy data."),
                 style={'text-align': 'center', 'padding': 0, 'border': 0})
    ]

# Renewable Tab
def create_Renewable_tab(regions, regional_end_date):
    type='renewable'
    return [html.Div(
        [
            # add Selection panel
            html.Div(
                [
                    html.Div(html.P(dcc.Markdown(tab_data.loc['renewable', 'text']),className="control_label"), className='pretty_container_info') ,
                    html.P(dcc.Markdown("**Select Region:**"), className="control_label"),
                    dcc.Dropdown(
                        id=type+"-region-select",
                        options=regions,
                        value="VIC",
                        # labelStyle={"display": "inline-block"},
                        className="dcc_control",
                    ),
                    html.P(dcc.Markdown("**Select date range:**"), className="control_label"),
                    dcc.DatePickerRange(
                        id=type+'-date-range',
                        min_date_allowed=dt(2012, 1, 1),
                        max_date_allowed=dt(2023, 1, 1),
                        initial_visible_month=dt(2012, 1, 1),
                        start_date=dt(2016, 1, 1).date(),
                        end_date=regional_end_date.date(),
                        display_format='DD/MM/YYYY',
                    ),
                    html.P(dcc.Markdown("**Select data frequency:**"), className="control_label"),
                    dcc.Dropdown(
                        id="freq_"+type,
                        options=[{'label': '30-minute', 'value': '30T'},
                                 {'label': 'Daily', 'value': 'd'},
                                 {'label': 'Weekly', 'value': 'w'},
                                 {'label': 'Monthly', 'value': 'MS'},
                                 {'label': 'Quarterly', 'value': 'Q'},
                                 {'label': 'Annually', 'value': 'ys'}],
                        value="w",
                        className="dcc_control",
                    ),
                    #html.Hr(),[
                    html.Div([html.Button(
                        "Load Data", id=type + '_generate', style=button_gen_style
                    ), ], style={'padding': 20}),

                    html.Div([dbc.Alert(
                        thirty_minute_text,
                        color="primary",
                        id=type + "-alert-fade",
                        dismissable=True,
                        is_open=True,
                    ), ], style={'padding': 40}),
                ],
                className="pretty_container four columns",
                id="cross-filter-options-"+type,
            ),

            # add region summary
            html.Div(
                [html.Div([html.H3(id="Region_"+type, style={'text-align': 'center'}),
                           dcc.Loading(
                               id="loading-spinner-"+type,
                               children=[html.Div([html.P(id="spinner_renewable")])],
                               type="default",
                           )], id=type+"_title",
                          className="pretty_container"),
                 html.Div(
                     [dcc.Loading(
                         id="loading-"+type+"-dispatch",
                         children=[html.Div([html.H5(Info_data.loc['renewables','figure']), dcc.Graph(id='renewables')]),
                                   ],
                         type="circle"),html.Div([generate_modal('renewables'), create_download_button('renewables')],className="buttons-display")],
                     id="renewables_GraphContainer",
                     className="pretty_container",
                 ),
                 ],
                id="right-column-"+type,
                className="eight columns",
            ),
        ],
        className="flex-display",
    ),

        html.Div(
            [create_graph_container('residual_demand'), create_graph_container('percent_demand')],
            className="flex-display",
        ),
        html.Div(
            [create_graph_container('MVWAP')],
            className="flex-display",
        ),
        html.Br(),
        html.Div(footer, style={'clear': 'both'}, className='footer')
    ]

# Create Region Tab

# Reg
def create_region_tab(regions,regional_end_date):
        type='regional'
        return [html.Div(
            [
                 # add Selection panel
                html.Div(
                    [
                        html.Div(html.P(dcc.Markdown(tab_data.loc['regional', 'text']), className="control_label"),
                                 className='pretty_container_info'),
                        html.P(dcc.Markdown("**Select Regions:**"), className="control_label"),
                        dcc.Dropdown(
                            id="regional-region-select",
                            multi=True,
                            options=regions,
                            value=["VIC"],
                            #labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        ),
                        html.P(dcc.Markdown("**Select date range:**"), className="control_label"),
                        dcc.DatePickerRange(
                            id='regional-date-range',
                            min_date_allowed=dt(2012, 1, 1),
                            max_date_allowed=dt(2023, 1, 1),
                            initial_visible_month=dt(2012, 1, 1),
                            start_date=dt(2016, 1, 1).date(),
                            end_date=regional_end_date.date(),
                            display_format='DD/MM/YYYY',
                        ),
                        #dcc.Loading(id="loading-1", children=[html.Div(id="loading-output-1")], type="default"),
                        html.P(dcc.Markdown("**Select data frequency:**"), className="control_label"),
                        dcc.Dropdown(
                            id="freq_regional",
                            options=[{'label': '30-Minute', 'value': '30T'},
                                    {'label': 'Daily', 'value': 'd'},
                                    {'label': 'Weekly', 'value': 'w'},
                                     {'label': 'Monthly', 'value': 'MS'},
                                     {'label': 'Quarterly', 'value': 'Q'},
                                     {'label': 'Annually', 'value': 'ys'}],
                            value="w",
                            #labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        ),
                        html.P(dcc.Markdown("**Select units:**"),
                               className="control_label"),
                        dcc.RadioItems(
                            id="Regional_Energy_type",
                            options=[{'label': 'Total Energy (MWh)', 'value': True},
                                     {'label': 'Average Power (MW)', 'value': False}],
                            value=False,
                            # labelStyle={"display": "inline-block"},
                            className="Regional_Energy_type",
                        ),
                        html.Div([html.Button(
                            "Load Data", id=type + '_generate', style=button_gen_style
                        ), ], style={'padding': 20}),

                        html.Div([dbc.Alert(
                            thirty_minute_text,
                            color="primary",
                            id=type+"-alert-fade",
                            dismissable=True,
                            is_open=True,
                        ), ], style={'padding': 40}),
                        #dcc.Graph(id="map")
                    ],
                    className="pretty_container four columns",
                    id="cross-filter-options-region",
                ),
                # add region summary
                html.Div(
                        #Station title
                        [html.Div([html.H3(id='Region',style={'text-align': 'center'}),
                                  dcc.Loading(
                                        id="loading-spinner-regional",
                                        children=[html.Div([html.P(id="spinner_region")])],
                                        type="default",
                                    )],id="region_title",
                            className="pretty_container"),
                        html.Div(
                            [dcc.Loading(
                            id="loading-region-dispatch",
                            children=[html.Div([html.H5('Fuel Mix'),dcc.Graph(id='fuel_mix_mean')])],
                            type="circle"),html.Div([generate_modal('fuel_mix_mean'),create_download_button('fuel_mix_mean')],className="buttons-display")],
                            id="fuel_mix_meanGraphContainer",
                            className="pretty_container",
                        ),
                    ],
                    id="right-column-regional",
                    className="eight columns",
                ),
            ],
            className="flex-display",
        ),
       
        html.Div(
            [create_graph_container('price'),create_graph_container('consumption')  ],
            className="flex-display",
        ),
        html.Div(
                [create_graph_container('consumption_min'), create_graph_container('consumption_max')],
                className="flex-display",
            ),
        html.Div(
            [create_graph_container('avil'),create_graph_container('interconector')  ],
            className="flex-display",
        ),
            html.Br(style={'clear': 'both'}),
            html.Div(footer, style={'clear': 'both'}, className='footer')
        ]

# Create tabs
tabs_styles = {
    'backgroundColor':'#FF9928'
    #'height': '44px'
}

tab_style = {
    'borderBottom': '1px solid ##fefcfe',
    'padding': '6px',
    'color':'##fefcfe',#font
    'font-size': '100%',
    'backgroundColor': '#071F4E',
}

tab_selected_style = {
    'borderTop': '1px solid ##fefcfe',
    'borderBottom': '1px solid ##fefcfe',
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

# Modal information
Info_data=pd.read_excel('flask_webapp/dashapp/data/dashboard_description.xlsx').set_index('var')
Info_data['y_mwh']=Info_data['y_mwh'].fillna(Info_data['y'])
tab_data=pd.read_excel('flask_webapp/dashapp/data/dashboard_description.xlsx',sheet_name='tab').set_index('Tab').dropna()

def generate_modal(ID,button="Information"):
    header=Info_data.loc[ID,'figure']
    text=Info_data.loc[ID,'Info'].split('\n')
    all_link_text=[]
    style = {'padding': '20px'}
    for txt in text:
        if len(txt)>0:
            txt = txt.split('##')
            txt=[t.replace('”','"').replace('’',"'").replace('’',"'").replace('‘',"'") for t in txt]
            refs = [ast.literal_eval(i) for i in txt if i[0] == '[']
            txt = [i for i in txt if i[0] != '[']
            import dash_bootstrap_components as dbc
            from dash import html
            from dash import dcc

            style_p={}
            link_text = []

            i=1
            for t in txt:
                if i==1:
                    if t[-1] != ' ':
                        t=t+' '
                    link_text.append(t)
                else:
                    if t[0]!=' ':
                        t =' '+ t
                    if t[-1] != ' ':
                        t=t+' '
                    link_text.append(t)
                i=i+1
                if len(refs) > 0:
                    link_text.append(html.A(refs[0][0], href=refs[0][1],target='_blank'))
                    refs.pop(0)

            if len(link_text) != 0:
                link_text = html.P(link_text)
                all_link_text.append(link_text)
                all_link_text.append(html.Br())

    all_link_text = html.Div(all_link_text, style=style)

    modal = html.Div(
    [
        dbc.Button(button, id=ID+"_open", outline=True, color='secondary'),#,style=button_style),
        dbc.Modal(
            [
                dbc.ModalHeader(header),
                all_link_text,
                #dbc.ModalBody(text),
                dbc.ModalFooter(
                    dbc.Button("Close", id=ID+"_close", className="ml-auto")
                ),
            ],
            id=ID+"_modal",
            scrollable=True,
            size="lg",
        ),
    ]
    )
    return modal

def create_modal_callback(ID,app):
    ID_modal=ID+"_modal"
    ID_open=ID+"_open"
    ID_close=ID+"_close"
    @app.callback(
        Output(ID_modal, "is_open"),
        [Input(ID_open, "n_clicks"), Input(ID_close, "n_clicks")],
        [State(ID_modal, "is_open")],
    )
    def toggle_modal(n1, n2, is_open):
        if n1 or n2:
            return not is_open
        return is_open

# Create FCAS Tab

# Download Callbacks
def create_regional_downloads(ID, app,type='regional'):
    @app.callback(
        dash.dependencies.Output('download-link_' + ID, 'href'),
        [Input(type+'_generate','n_clicks')],
        [State('download-link_' + ID, "key"),
         State("regional-region-select", "value"),
         State("freq_"+type, "value"),
         State(type+'-date-range', 'start_date'),
         State(type+'-date-range', 'end_date'),
         State("Regional_Energy_type", "value") ])
    def update_download_link(clicks,variable, region, freq, start_date, end_date,Regional_Energy_type):
        # variable=ID_DL_link.split('_')[2]
        title='y'
        if variable == 'fuel_mix_mean':
            if freq != '30T':
                dff = regional_fuel_mix_d[region][regional_fuel_mix_d[region].iloc[-1].dropna().index]
                if Regional_Energy_type and ID in ['fuel_mix_mean', 'consumption', 'interconector']:
                    scale_MWh = dff.iloc[:, 0].resample(freq).count() * 24


                dff=dff.resample( freq).mean().loc[start_date:end_date]

                if Regional_Energy_type and ID in ['fuel_mix_mean', 'consumption', 'interconector']:
                    scale_MWh = scale_MWh.reindex(dff.index)
                    dff = MW_scale(dff, scale_MWh)
                    title = 'y_mwh'
                else:
                    title = 'y'

                # Bux fix. Ben Willey. 8 Aug 22
                if ID == "consumption_max":
                    dff=dff.resample(freq).max().loc[start_date:end_date]

                if ID == "consumption_min":
                    dff=dff.resample(freq).min().loc[start_date:end_date]
                
            else:

                dff = regional_fuel_mix_30T[region][regional_fuel_mix_d[region].iloc[-1].dropna().index]

                dff=dff.loc[start_date:end_date].tz_localize(None)

        else:
            if variable=='interconector':
                variable= ['Interconnector_Export', 'Interconnector_Import']

            if freq != '30T':

                if ID!='interconector':
                    #dff=pd.DataFrame()

                    dff=regional_data_d.loc[:,regional_data_d.columns.get_level_values(1)==ID][region].droplevel(1,axis=1)

                    if Regional_Energy_type and ID in ['fuel_mix_mean', 'consumption', 'interconector']:
                        scale_MWh = dff.iloc[:, 0].resample(freq).count() * 24
                    dff = dff.resample(freq).mean().loc[start_date:end_date].tz_localize(None)

                    if Regional_Energy_type and ID in ['fuel_mix_mean', 'consumption', 'interconector']:
                        scale_MWh = scale_MWh.reindex(dff.index)

                        dff = MW_scale(dff, scale_MWh)
                        title = 'y_mwh'
                    else:
                        title='y'


                else:
                    dff = pd.DataFrame()
            else:
                region=region[0]

                dff = regional_data_30T[region][variable].loc[start_date:end_date].tz_localize(None)
        csv_string = pd.concat([dff],axis=1,keys=[Info_data.loc[ID,title]]).to_csv(encoding='utf-8')
        csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
        return csv_string

def create_renewables_downloads(ID, app,type='renewable'):
    @app.callback(
        dash.dependencies.Output('download-link_' + ID, 'href'),
        [Input(type + '_generate', 'n_clicks')],
        [State('download-link_' + ID, "key"),
         State(type+"-region-select", "value"),
         State("freq_"+type, "value"),
         State(type+'-date-range', 'start_date'),
         State(type+'-date-range', 'end_date')])
    def update_download_link(clicks,variable, region, freq, start_date, end_date):
        if freq != '30T':
            dff = renewable_data_d[region][variable].resample(freq).mean().loc[start_date:end_date]
        else:
            if ID=='residual_demand':
                dff = pd.concat(
                    [renewable_data_d[region]['min_residual_demand']['residual_demand'].resample(freq).min().loc[
                     start_date:end_date],
                     renewable_data_d[region]['residual_demand']['residual_demand'].resample(freq).mean().loc[
                     start_date:end_date],
                     renewable_data_d[region]['max_residual_demand']['residual_demand'].resample(freq).max().loc[
                     start_date:end_date],
                     ], axis=1,
                    keys=['Minimum residual_demand', 'Average residual demand', 'Maximum residual_demand'])
            else:
                dff = renewable_data_30T[region][variable].loc[start_date:end_date]
        csv_string = pd.concat([dff.tz_localize(None)],axis=1,keys=[Info_data.loc[ID,'y']]).to_csv(encoding='utf-8')
        csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
        return csv_string

def create_interconnector_downloads(ID, app,type='interconnector'):
    @app.callback(
        Output('download-link_' + ID, 'href'),
        [Input(type + '_generate', 'n_clicks')],
        [State('download-link_' + ID, "key"),
         State(type+"-region-select", "value"),
         State("freq_"+type, "value"),
         State(type+'-date-range', 'start_date'),
         State(type+'-date-range', 'end_date')])
    def update_download_link(clicks,variable, interconnector, freq, start_date, end_date):
        if interconnector=='interconnnector_flow':
            interconnector='interconnector'
        if freq != '30T':
            dff = interconnector_data_d[interconnector].resample(freq).mean().loc[start_date:end_date]
        else:
            dff = interconnector_data_30T[interconnector].loc[start_date:end_date]
        csv_string = pd.concat([dff.tz_localize(None)],axis=1,keys=[Info_data.loc[ID,'y']]).to_csv(encoding='utf-8')
        csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
        return csv_string

def create_generator_downloads(ID, app, type_='gen'):
    @app.callback(
        Output('download-link_' + ID, 'href'),
        [Input(type_ + '_generate', 'n_clicks')],
        [State("opt-dropdown", "value"),
               State("freq", "value"),
               State('station-date-range', 'start_date'),
               State('station-date-range', 'end_date'),
               State("Generator_Energy_type", "value")]
    )
    def update_download_link(clicks, station, freq, start_date, end_date, Generator_Energy_type):
        data = gen_data_d[ID]
        station_org=station.copy()

        for s in station_org:
            if s in data.columns:
                station_check=True
            else:
                station.remove(s)

        if len(station)==0:
            station_check=False

        if station_check:
            if ID == 'cfactor':
                c = []
                n = []
                for s in station:
                    # handles two callide power stations
                    if s == 'Callide Power Station':
                        shift_station = 1
                    else:
                        shift_station = 0
                    capacity = int(grouped_tech.droplevel([0, 1, 2]).loc[s, 'Max Cap (MW)'].iloc[shift_station]) * 1 / 100
                    if (', Wind' in s) | (', Solar' in s) | ('VIC, Brown' in s):
                        capacity = 0
                    c.append(gen_data_d['scada'][s] / capacity)
                    n.append(s + ' ( calculated using ' + str(int(capacity * 100)) + ' MW)')
                    dff = pd.concat(c, axis=1, keys=n).resample(freq).mean().loc[start_date:end_date]
                    csv_string = pd.concat([dff.tz_localize(None)], axis=1, keys=[Info_data.loc[ID, 'y']]).to_csv(
                        encoding='utf-8')
            else:
                if freq != '30T':
                    if ID=='min_demand':
                        dff = data[station].resample(freq).min().loc[start_date:end_date]
                    else:
                        dff = data[station].resample(freq).mean().loc[start_date:end_date]
                else:
                    dff = data[station].loc[start_date:end_date]

                if (Generator_Energy_type) and (ID == 'scada'):
                    days=data.loc[:,'Bayswater Power Station'].resample('d').mean().resample(freq).count()*24
                    da = data[station].resample(freq).mean().loc[start_date:end_date].copy()
                    for s in station:
                        da[s] = da[s] * days
                    csv_string = pd.concat([da.tz_localize(None)], axis=1, keys=['Total Energy (MWh)']).to_csv(
                        encoding='utf-8')
                else:
                    csv_string = pd.concat([dff.tz_localize(None)], axis=1, keys=[Info_data.loc[ID, 'y']]).to_csv(
                        encoding='utf-8')
            csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
        else:

            for s in station_org:
                if s==station_org[0]:
                    station_name=s
                else:
                    station_name=station_name+'/'+s

            dff=pd.DataFrame(index=['No data availble for '+station_name])
            csv_string = 'No data availble for '+station_name
            csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
        return csv_string

# Global data
fuel_stations={}
tech = pd.read_csv('flask_webapp/dashapp/NEM Registration and Exemption List_Mar 2021.csv'
                         ).set_index('DUID')
tech = tech.loc[~tech.index.duplicated(keep='first')]
tech = tech.loc[~tech.index.duplicated(keep='first')]
tech.loc[tech['Dispatch Type']=='Load','Station Name'] =tech.loc[tech['Dispatch Type']=='Load','Station Name']+' (Load)'
tech.loc[(tech['Fuel Source - Primary']=='Battery storage')&(tech['Dispatch Type']!='Load'),'Station Name']=tech.loc[(tech['Fuel Source - Primary']=='Battery storage')&(tech['Dispatch Type']!='Load'),'Station Name']+' (Generation)'
tech.loc[(tech['Technology Type - Primary']=='Storage'),'Fuel Source - Descriptor']='Battery Storage'
tech.loc[tech['Fuel Source - Descriptor']=='-','Fuel Source - Descriptor']='Loads'
tech['n']=tech['Technology Type - Descriptor'].replace({'Open Cycle Gas turbines (OCGT)':'OCGT','Combined Cycle Gas Turbine (CCGT)':'CCGT',
'Steam Sub-Critical':'Thermal','Compression Reciprocating Engine':'Engines','Spark Ignition Reciprocating Engine':'Engines'})
tech['Fuel Source - Descriptor']=tech['Fuel Source - Descriptor'].str.replace('Water','Hydro').str.replace(' / Fuel Oil','').str.replace(' / Diesel','').str.replace('-','Other').str.replace(' Solar','Solar').str.replace('Solar ','Solar')
#tech_fuels=tech.loc[]
tech.loc[tech['Fuel Source - Descriptor']=='Natural Gas','Fuel Source - Descriptor']=tech.loc[tech['Fuel Source - Descriptor']=='Natural Gas','Fuel Source - Descriptor']+', '+tech.loc[tech['Fuel Source - Descriptor']=='Natural Gas','n']
tech_fuels=tech.copy()
tech_fuels['Station Name']=tech_fuels['Region'].str[:-1]+', '+tech_fuels['Fuel Source - Descriptor']
tech_fuels['Participant']=tech_fuels['Region'].str[:-1]
tech_fuels['Classification']='Scheduled'
tech=pd.concat([tech,tech_fuels])

tech['Reg Cap (MW)']=tech['Reg Cap (MW)'].str.replace('-','0').astype(float)
tech['Max Cap (MW)']=tech['Max Cap (MW)'].str.replace('-','0').astype(float)
tech.Region=tech.Region.str[:-1]
tech.loc[tech['Classification']=='Scheduled','Classification']='sz'
tech['Classification']=tech['Classification'].str.replace('Semi-Scheduled','Scheduled/Semi-Scheduled').str.replace('sz','Scheduled/Semi-Scheduled')
grouped_tech=tech.groupby(['Region','Fuel Source - Descriptor','Classification','Station Name']).first()
grouped_tech.loc[grouped_tech.index.get_level_values(1).isin(['Black Coal','Brown Coal','Water','Natural Gas','Diesel','Solar','Wind'])]

tech['Physical Unit No.']=tech['Physical Unit No.'].str.split('-').str.get(1).fillna(1)
tech['Physical Unit No.']=tech['Physical Unit No.'].str.split(',').str.get(1).fillna(1)
tech['Physical Unit No.']=tech['Physical Unit No.'].str.split(' ').str.get(1).fillna(1).astype(int)

grouped_tech_sum=tech.groupby(['Region','Fuel Source - Descriptor','Classification','Station Name']).sum()
grouped_tech_sum.loc[grouped_tech_sum.index.get_level_values(1).isin(['Black Coal','Brown Coal','Water','Natural Gas','Diesel','Solar','Wind'])]

grouped_tech['Reg Cap (MW)']=grouped_tech_sum['Reg Cap (MW)']
grouped_tech['Max Cap (MW)']=grouped_tech_sum['Max Cap (MW)']
grouped_tech['Physical Unit No.']=grouped_tech_sum['Physical Unit No.']
grouped_tech['fuel_type']=grouped_tech.index.get_level_values(0)

lat_lon=pd.read_csv('flask_webapp/dashapp/MajorPowerStations_v2.csv').set_index('NAME')
lat_lon['lat_lon']=lat_lon[['LATITUDE','LONGITUDE']].values.tolist()
lat_lon.index=lat_lon.index.str.split().str.get(0)
lat_lon = lat_lon.loc[~lat_lon.index.duplicated(keep='first')]
grouped_tech['lat_lon']=grouped_tech.index.get_level_values(1).str.split().str.get(0).map(lat_lon['lat_lon'])

classification_types=dictafy(grouped_tech.index.get_level_values(2).unique())
regions=dictafy(['All regions','VIC','NSW','QLD','SA','TAS'])

grouped_tech_all=grouped_tech.copy().reset_index()
grouped_tech_all['Region']='All regions'

grouped_tech_all=grouped_tech_all.set_index(['Region','Fuel Source - Descriptor','Classification','Station Name'])
grouped_tech_all
grouped_tech=pd.concat([grouped_tech,grouped_tech_all])

## Add an all fuels option

regionss = ['All regions', 'VIC', 'NSW', 'QLD', 'SA', 'TAS']
grouped_tech = grouped_tech.reset_index().set_index('Region')

all_fuels = [grouped_tech]
for region in regionss:
    r = grouped_tech.loc[region]
    r.loc[:,'Fuel Source - Descriptor'] = 'All fuel types'
    all_fuels.append(r)

grouped_tech = pd.concat(all_fuels, axis=0).reset_index().set_index(
    ['Region', 'Fuel Source - Descriptor', 'Classification', 'Station Name'])#.sort_index(ascending=False)
fuel_types=dictafy(grouped_tech.index.get_level_values(1).unique())

#### MWh conversion datasets:

for reg in grouped_tech.index.get_level_values(0).unique():
    for ind in grouped_tech.index.get_level_values(1).unique():
        for clas in grouped_tech.index.get_level_values(2).unique():
            try:
                fuel_stations[(reg,ind,clas)]=dictafy(grouped_tech.loc[(reg,ind,clas)].index.to_list())
            except:
                fuel_stations[(reg,ind,clas)]=[{'label': 'No '+clas+' '+ind+' in '+reg, 'value': None}]
    years=[str(y) for y in range(2012,2021)]

local=False

# Datasets
if os.environ.get('LOCAL_LAPTOP'):
    regional_data_30T = pd.read_parquet('flask_webapp/dashapp/data/plot_data/regional_data_30T.parquet')
    regional_data_d = pd.read_parquet('flask_webapp/dashapp/data/plot_data/regional_data_d.parquet')
    regional_fuel_mix_30T = pd.read_parquet('flask_webapp/dashapp/data/plot_data/regional_fuel_mix_d.parquet')
    regional_fuel_mix_d = pd.read_parquet('flask_webapp/dashapp/data/plot_data/regional_fuel_mix_d.parquet')
    renewable_data_30T=pd.read_parquet('flask_webapp/dashapp/data/plot_data/renewable_data_d.parquet').tz_localize(None)
    renewable_data_d=pd.read_parquet('flask_webapp/dashapp/data/plot_data/renewable_data_d.parquet').tz_localize(None)
    interconnector_data_30T = pd.read_parquet('flask_webapp/dashapp/data/plot_data/interconnector_data_d.parquet')
    interconnector_data_d = pd.read_parquet('flask_webapp/dashapp/data/plot_data/interconnector_data_d.parquet')


    #generator tab
    pricesetting_freq_d = pd.read_parquet('flask_webapp/dashapp/data/plot_data/generators/pricesetting_freq_d.parquet')
    pricesetting_d = pd.read_parquet('flask_webapp/dashapp/data/plot_data/generators/pricesetting_d.parquet')
    max_avil_d = pd.read_parquet('flask_webapp/dashapp/data/plot_data/generators/max_avil_d.parquet')
    cfactor_d = pd.read_parquet('flask_webapp/dashapp/data/plot_data/generators/cfactor_d.parquet')
    scada_d = pd.read_parquet('flask_webapp/dashapp/data/plot_data/generators/scada_d.parquet')
    NEM_bids_d = pd.read_parquet('flask_webapp/dashapp/data/plot_data/generators/NEM_bids_d.parquet')
    VWAP_d = pd.read_parquet('flask_webapp/dashapp/data/plot_data/generators/VWAP_d.parquet')
    min_demand_d = pd.read_parquet('flask_webapp/dashapp/data/plot_data/generators/min_demand_d.parquet')

    widget_data = regional_data_d.loc[:, regional_data_d.columns.get_level_values(1) == 'price'].droplevel(1,
                                                                                                           axis=1).drop(
        'All regions', axis=1).dropna()
    month = widget_data.index[-1].strftime('%b')
    widget_data = widget_data.groupby(widget_data.index.year).mean().loc[2014:]
    widget_data = widget_data[widget_data.iloc[-2].sort_values().index]
    if month != 'Jan':
        widget_data = widget_data.rename(
            index={widget_data.index[-1]: str(widget_data.index[-1]) + '<br>Jan to ' + month})
    else:
        widget_data = widget_data.rename(index={widget_data.index[-1]: str(widget_data.index[-1]) + '<br>' + month})
    widget_data.index = '⠀' + widget_data.index.astype(str)

# Interconnector_data_30T.parquet
else:
    print('loading files from google cloud storage',end='')
    import gcsfs
    fs = gcsfs.GCSFileSystem(token='flask_webapp/dashapp/assets/Storage Economics-03fc43fb9956.json')#
    path='gcs://vepc_data_bucket/App_data_files/'
    widget_data = pd.read_parquet(path + 'widget_data.parquet', filesystem=fs)
    regional_data_d = pd.read_parquet(path+'regional_data_d.parquet',filesystem=fs)
    regional_data_30T = pd.read_parquet(path+'regional_data_30T.parquet',filesystem=fs)
    regional_fuel_mix_30T = pd.read_parquet(path+'regional_fuel_mix_30T.parquet',filesystem=fs)
    regional_fuel_mix_d = pd.read_parquet(path+'regional_fuel_mix_d.parquet',filesystem=fs)
    renewable_data_30T=pd.read_parquet(path+'renewable_data_30T.parquet',filesystem=fs).tz_localize(None)
    renewable_data_d=pd.read_parquet(path+'renewable_data_d.parquet',filesystem=fs).tz_localize(None)
    interconnector_data_30T = pd.read_parquet(path + 'interconnector_data_30T.parquet', filesystem=fs)
    interconnector_data_d = pd.read_parquet(path + 'interconnector_data_d.parquet', filesystem=fs)

    pricesetting_freq_d = pd.read_parquet(path+'generators/pricesetting_freq_d.parquet', filesystem=fs)
    pricesetting_d = pd.read_parquet(path+'generators/pricesetting_d.parquet', filesystem=fs)
    max_avil_d = pd.read_parquet(path+'generators/max_avil_d.parquet', filesystem=fs)
    cfactor_d = pd.read_parquet(path+'generators/cfactor_d.parquet', filesystem=fs)
    scada_d = pd.read_parquet(path+'generators/scada_d.parquet', filesystem=fs)
    VWAP_d = pd.read_parquet(path + 'generators/VWAP_d.parquet', filesystem=fs)
    NEM_bids_d = pd.read_parquet(path+'generators/NEM_bids_d.parquet', filesystem=fs)
    min_demand_d = pd.read_parquet(path+'generators/min_demand_d.parquet', filesystem=fs)
    
# Rename generation and load in bids to match app names
cols=NEM_bids_d.columns.get_level_values(0)
rename={}
for i in (cols.unique()).values[(cols.unique()).str.contains('(Load)')]:
    rename[i]=i.replace('(Load) ','')+' (Load)'
for i in (cols.unique()).values[(cols.unique()).str.contains('(Generation)')]:
    if 'Temp' not in i:
        rename[i]=i.replace('(Generation) ','')+' (Generation)'
NEM_bids_d=NEM_bids_d.rename(columns=rename, level=0)

regional_end_date=regional_data_30T.index[-1]
regional_fuel_mix_30T=regional_fuel_mix_30T.rename(columns={'Water':'Hydro'})
regional_fuel_mix_d=regional_fuel_mix_d.rename(columns={'Water':'Hydro'})

# Generator data
gen=['scada','cfactor','NEM_bids','max_avil','pricesetting_freq', 'pricesetting','VWAP','min_demand']
gen_data_d={'min_demand':min_demand_d,'VWAP':VWAP_d,'pricesetting_freq':pricesetting_freq_d, 'pricesetting':pricesetting_d, 'max_avil':max_avil_d, 'cfactor':cfactor_d, 'scada':scada_d, 'NEM_bids':NEM_bids_d}
gen_data_col={'pricesetting_freq':0, 'pricesetting':1, 'max_avil':2, 'cfactor':3, 'scada':4, 'NEM_bids':0,'VWAP':5,'min_demand':6}

def get_dash_tab(server,tab='Regional NEM',url='/regional/'):
    #### Get app data:
    empty_station_figure = empty_station_figure = go.Figure(data=[go.Table(header=dict(font=dict(size=14, color='black'),fill_color='#FF9928',values=['No data is available for this station.']),
                     )]).to_dict()

    regions=dictafy(['All regions','VIC','NSW','QLD','SA','TAS'])

    if tab=='NEM Generators':
        regional_figures=None
        #figures['Vales Point B Power Station']=figures['Vales Point "B" Power Station']
        station_end_date=pricesetting_freq_d.index[-1]

    ########
    app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],external_stylesheets=[dbc.themes.BOOTSTRAP,'flask_webapp/dashapp/assets/styles.css'],
        server=server,url_base_pathname=url)
    app.title=tab.replace(' ','_')
    # Create global chart template
    mapbox_access_token = "pk.eyJ1IjoiamFja2x1byIsImEiOiJjajNlcnh3MzEwMHZtMzNueGw3NWw5ZXF5In0.fk8k06T96Ml9CLGgKmk81w"

    # add laybout functions to layout

    if tab=='Regional NEM':
        layout=create_region_tab(regions,regional_end_date)
        figures = None
    elif tab=='Renewable Summary':
        layout=create_Renewable_tab(regions,regional_end_date)
        figures = None
    elif tab=='NEM Generators':
        layout=create_generator_tab(regions,regional_end_date)

    elif tab=='NEM FCAS Markets':
        layout=create_FCAS_tab()
    elif tab=='Gas Markets':
        layout=create_dev_tab()
    elif tab=='interconnector':
        layout=create_interconnector_tab(interconnectors,regional_end_date)
        figures = None
    elif tab=='widget':
        #widget_data.index[-1]=widget_data.index[-1][:-1]
        fig=plot(widget_data.iloc[2:],   title='Demand Weighted Average Price ($/MWh)',colour_shift=0, b=0,
                 yTitle=None,transparent=False,narrow=True,horizontal_legend=False, ylim=[0,130], tozero=True,line_mode='lines+markers',
                 VEPC_Big_image=True,y_tick_interval=30)
        layout=create_widget(fig)

    if tab=='widget':
        app.layout = html.Div(layout, id=tab,
                              style={"height": "100vh",  'backgroundColor': '#fefcfe', 'margin': 0,
                                     "padding": 0}
                              )

    else:
        app.layout = html.Div(layout, id=tab,
                              style={"height": "100%", 'width': "100%", 'backgroundColor': '#fefcfe', 'margin': 0,
                                     "padding": 0}
                              )

    if tab=='NEM Generators':
        type='gen'
        @app.callback(
            dash.dependencies.Output('opt-dropdown', 'options'),
            [   Input('generator_region', 'value'),
                Input('fuel_type', 'value'),
            Input('scheduled_type', 'value')]
        )
        def update_date_dropdown(region,fuel_type,clas):
            i=([fuel_stations[(r,f,clas)] for r in region for f in fuel_type])
            i=list(itertools.chain.from_iterable(i))
            return i

        @app.callback(
            Output("station", "children"),
            [Input(type + '_generate', 'n_clicks')],
            [ State("opt-dropdown", "value")]
        )
        def get_technology_type(clicks,station):
            return station

        @app.callback(
            Output("station_name", "children"),
            [Input(type + '_generate', 'n_clicks')],
            [ State("opt-dropdown", "value")]
        )
        def get_technology_type(clicks,station):
            for s in station:
                if s==station[0]:
                    name = s
                else:
                    name= name + ' / ' + s
            return name

        @app.callback(
            [Output("region", "children"),
            Output("capacity", "children"),
            Output("technology_type", "children"),
            Output("participant", "children"),
            Output("units", "children"),
            Output("fuel_type_r", "children")],
            [Input(type + '_generate', 'n_clicks')],
            [State('opt-dropdown', 'value'),
             State('fuel_type', 'value')
            ]
        )
        def get_technology_type(clicks, station,fuel_type):
            s=station.copy()
            for station in s:
                if station == 'Callide Power Station':
                    n = 1
                else:
                    n = 0

                if station==s[0]:
                    technology_type = grouped_tech.droplevel([0,1,2]).loc[station,'Technology Type - Descriptor'].iloc[0]
                    fuel_type = fuel_type #grouped_tech.reset_index().set_index('Station Name').loc[station,'fuel_type'].iloc[0]
                    region = grouped_tech.reset_index().set_index('Station Name').loc[station,'Region'].iloc[0].replace('1','')
                    capacity = str(int(grouped_tech.droplevel([0,1,2]).loc[station,'Max Cap (MW)'].iloc[n]))+' MW'
                    participant = grouped_tech.droplevel([0,1,2]).loc[station,'Participant'].iloc[0].split()[0]
                    units = grouped_tech.droplevel([0,1,2]).loc[station,'Physical Unit No.'].iloc[0]
                else:
                    region = region+' / '+ grouped_tech.reset_index().set_index('Station Name').loc[station,'Region'].iloc[0].replace('1','')
                    capacity = capacity + ' / ' + \
                                str(int(grouped_tech.droplevel([0,1,2]).loc[station,'Max Cap (MW)'].iloc[0]))+' MW'
                    units = str(units)+' / ' + str(grouped_tech.droplevel([0, 1, 2]).loc[station, 'Physical Unit No.'].iloc[0])
                    participant = participant +' / ' + grouped_tech.droplevel([0, 1, 2]).loc[station, 'Participant'].iloc[0].split()[0]
                    technology_type = technology_type +' / ' + \
                    grouped_tech.droplevel([0, 1, 2]).loc[station, 'Technology Type - Descriptor'].iloc[0]

            return [region,capacity,technology_type,participant,units,fuel_type]

        def get_gen_figure(ID,app):
            type='gen'
            @app.callback(
                Output(ID, "figure"),
                [Input(type + '_generate', 'n_clicks')],
                [State("opt-dropdown", "value"),
                 State("freq", "value"),
                 State('station-date-range', 'start_date'),
                 State('station-date-range', 'end_date'),State('fuel_type', 'value'),
                       State('Generator_Energy_type', 'value')
                       ],
            )
            def get_app_station_figures(clicks,station, freq, start_date, end_date,fuel_type,Generator_Energy_type):


                station_org=station.copy()
                barline=0
                bar_mode='stack'
                bar_mode = None
                if freq in ['ys','Q']:
                    mode='bar'
                    bar_gap=0.1
                else:
                    mode='line'
                    bar_gap=0
                if ID=='NEM_bids':
                    barline=1,
                    mode='bar'
                    bar_mode='stack'
                data=gen_data_d[ID]

                for s in station_org:
                    if s in data.columns:
                        station_check = True
                    else:
                        station.remove(s)
                if len(station) == 0:
                    station_check = False
                multiple_stations = isinstance(station, list)
                if len(station)>1:
                    colour_shift=0
                else:
                    colour_shift=gen_data_col[ID]

                if station_check:
                    if ID == 'NEM_bids':
                        labels = ['<$0', '$0-20', '$20-40', '$40-60', '$60-80', '$80-100', '$100-150', '$150-300',
                                  '$300-1000', '$1000-5000', '>$5000']
                        data=data[station]
                        if multiple_stations:
                            data=data.groupby(level=1, axis=1).sum()
                        fig = plot(data.reindex(labels,axis=1).resample(freq).mean().loc[start_date:end_date],
                                   yTitle=Info_data.loc[ID, 'y'],
                                   line_shape='hv', VEPC_image=True, bargap=bar_gap, legend_shift=-0.3,
                                   colour_set='tab10',
                                   colour_shift=0, mode=mode, barline=0.1, bar_mode=bar_mode)
                    elif ID=='cfactor':
                        c=[]
                        n=[]
                        for s in station:
                            # handles two callide power stations
                            if s == 'Callide Power Station':
                                shift_station = 1
                            else:
                                shift_station = 0
                            capacity=int(grouped_tech.droplevel([0,1,2]).loc[s,'Max Cap (MW)'].iloc[shift_station])* 1 / 100
                            if (', Wind' in s) | (', Solar' in s) |  ('VIC, Brown' in s):
                                capacity=0
                            c.append(gen_data_d['scada'][s] / capacity)
                            n.append(s+' ('+str(int(capacity*100))+' MW)')
                            plot_data=pd.concat(c,axis=1,keys=n)

                        fig = plot(plot_data.resample(freq).mean().loc[start_date:end_date],
                                       yTitle=Info_data.loc[ID, 'y'],
                                       line_shape='hv', VEPC_image=True, bargap=bar_gap, legend_shift=-0.25,
                                       colour_set='Dark2',mode=mode,
                                       colour_shift=colour_shift, n=8, barline=barline)
                    else:
                        if (Generator_Energy_type) and (ID=='scada'):
                            days=data.loc[:,'Bayswater Power Station'].resample('d').mean().resample(freq).count()*24
                            da=data[station].resample(freq).mean().loc[start_date:end_date].copy()
                            for s in station:
                                da[s]=da[s]*days

                            fig = plot(da,
                                       yTitle='Total energy generation (MWh)',
                                       line_shape='hv', VEPC_image=True, bargap=bar_gap, legend_shift=-0.25,
                                       colour_set='Dark2',
                                       colour_shift=colour_shift, n=8, mode=mode, barline=barline, bar_mode=bar_mode)
                        else:
                            fig = plot(data[station].resample(freq).mean().loc[start_date:end_date],
                                       yTitle=Info_data.loc[ID, 'y'],
                                       line_shape='hv', VEPC_image=True, bargap=bar_gap, legend_shift=-0.25,
                                       colour_set='Dark2',
                                       colour_shift=colour_shift, n=8, mode=mode, barline=barline, bar_mode=bar_mode)

                else:
                    for s in station_org:
                        if s == station_org[0]:
                            station_name = s
                        else:
                            station_name = station_name + '/' + s
                    fig= go.Figure(data=[go.Table(header=dict(font=dict(size=14, color='black'),fill_color='#FF9928',
                                                                                     values=['No data is available for '+station_name+'.']),)])

                spinner=''
                return fig.to_dict()
        for ID in gen:
            get_gen_figure(ID,app)
            create_generator_downloads(ID, app)
            create_modal_callback(ID, app)


    if tab=='Regional NEM':
        type='regional'

        @app.callback(
            Output(type+"-alert-fade", "is_open"),
            [Input("freq_regional", "value"),
            Input('regional-date-range', 'start_date'),
            Input('regional-date-range', 'end_date')],
        )
        def toggle_alert_no_fade(freq,start_date,end_date):
            if freq=='30T':
                if (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days > 30:
                    return True
            return False

        @app.callback(
            Output("Region", "children"),
            [ Input("regional-region-select", "value")]
        )

        def get_technology_type(Region):
            regions={'All regions':'All Regions',
                    'VIC':'Victoria',
                    'NSW': 'New South Wales',
                    'QLD':'Queensland',
                    'SA':'South Australia',
                    'TAS':'Tasmania'}
            for r in Region:
                if r==Region[0]:
                    re=regions[r]
                else:
                    re=re+' / '+regions[r]
            return re


        @app.callback(
            [Output('fuel_mix_mean', "figure"),
            Output('price', "figure"),
            Output('avil', "figure"),
            Output('consumption', "figure"),
            Output('interconector', "figure"),
            Output('consumption_min', "figure"),
            Output('consumption_max', "figure"),
            Output('spinner_region', "children") ],
            [Input(type+'_generate', 'n_clicks')],
            [State("regional-region-select", "value"),
            State("freq_regional", "value"),
            State('regional-date-range', 'start_date'),
            State('regional-date-range', 'end_date'),
            State("Regional_Energy_type", "value") ]
        )
        def get_region_app_figures(clicks,region, freq, start_date, end_date, Regional_Energy_type):

            if freq != '30T':

                if pd.to_datetime(end_date) > regional_fuel_mix_d.index[-1].tz_localize(None):
                    end_date = regional_fuel_mix_d.index[-1]

                if freq in ['ys','Q']:
                    mode='bar'
                    bar_gap=0.1
                else:
                    mode='line'
                    bar_gap=0
                d = regional_fuel_mix_d[region].droplevel(0, axis=1).copy()
                d=d.groupby(d.columns, axis=1).sum()
                order=[o for o in d.columns.sort_values() if o in d.iloc[-1].dropna().index]

                if Regional_Energy_type:
                    scale_MWh = d.iloc[:,0].resample(freq).count()*24
                d=d.resample(freq).mean().loc[start_date:end_date,order]

                if Regional_Energy_type:
                    scale_MWh=scale_MWh.reindex(d.index)
                    d=MW_scale(d, scale_MWh )
                    title='y_mwh'
                else:
                    title='y'

                fuel_mix_mean = plot(d, yTitle=Info_data.loc['fuel_mix_mean', title], mode='bar',
                    bar_mode='stack', VEPC_image=True, bargap=bar_gap, barline=2,legend_shift=-0.25, colour_set='Dark2', colour_shift=1)
                ip = regional_data_d.loc[:, regional_data_d.columns.get_level_values(1) == 'Interconnector_Import'][
                    region].droplevel(0, axis=1)
                ip.columns = ip.columns + ' (' + region + ')'
                ex = regional_data_d.loc[:, regional_data_d.columns.get_level_values(1) == 'Interconnector_Export'][
                    region].droplevel(0, axis=1)
                ex.columns = ex.columns + ' (' + region + ')'
                d = pd.concat([ip, ex], axis=1)
                if Regional_Energy_type:
                    d=MW_scale(d, scale_MWh )
                interconector = plot(
                    d.resample(
                        freq).mean().loc[start_date:end_date], mode=mode, bar_mode=None, colour_set='Dark2',
                    yTitle=Info_data.loc['interconector', title], bargap=bar_gap, barline=0,line_shape='hv')

                d=regional_data_d.loc[:,regional_data_d.columns.get_level_values(1)=='price'][region].droplevel(1,axis=1).loc[start_date:end_date].resample(freq).mean()
                d=d.rename(columns=region_names)
                price = plot(d,
                             yTitle=Info_data.loc['price', 'y'],
                             line_shape='hv', VEPC_image=True, bargap=bar_gap, legend_shift=-0.25, colour_set='Dark2',
                             colour_shift=0, n=8, mode=mode,barline=0,)
                d=regional_data_d.loc[:,regional_data_d.columns.get_level_values(1)=='avil'][region].droplevel(1,axis=1).loc[start_date:end_date].resample(freq).mean()
                d = d.rename(columns=region_names)
                avil = plot(d,
                            yTitle=Info_data.loc['avil', 'y'], line_shape='hv', VEPC_image=True, bargap=bar_gap,
                            legend_shift=-0.25, colour_set='Dark2', colour_shift=0, n=8, mode=mode,barline=0,)
                d=regional_data_d.loc[:,regional_data_d.columns.get_level_values(1)=='consumption'][region].droplevel(1,axis=1).loc[start_date:end_date].resample(freq).mean()
                d = d.rename(columns=region_names)
                if Regional_Energy_type:
                    d = MW_scale(d, scale_MWh)
                consumption = plot(
                    d,
                    yTitle=Info_data.loc['consumption', title], line_shape='hv', VEPC_image=True, bargap=bar_gap,
                    legend_shift=-0.25, colour_set='Dark2', colour_shift=0, n=8, mode=mode,barline=0,)
                d=regional_data_d.loc[:,regional_data_d.columns.get_level_values(1)=='consumption_min'][region].droplevel(1,axis=1).loc[start_date:end_date].resample(freq).min()
                d = d.rename(columns=region_names)
                consumption_min = plot(
                    d,
                    yTitle=Info_data.loc['consumption_min', title], line_shape='hv', VEPC_image=True, bargap=bar_gap,
                    legend_shift=-0.25, colour_set='Dark2', colour_shift=0, n=8, mode=mode, barline=0, )
                d = regional_data_d.loc[:, regional_data_d.columns.get_level_values(1) == 'consumption_max'][
                        region].droplevel(1, axis=1).loc[start_date:end_date].resample(freq).max()
                d = d.rename(columns=region_names)
                consumption_max = plot(
                    d,
                    yTitle=Info_data.loc['consumption_max', title], line_shape='hv', VEPC_image=True, bargap=bar_gap,
                    legend_shift=-0.25, colour_set='Dark2', colour_shift=0, n=8, mode=mode, barline=0, )


            else:

                region = region[0]
                if (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days > 30:
                    start_date = pd.to_datetime(end_date) - pd.DateOffset(days=30)
                if pd.to_datetime(end_date) > regional_fuel_mix_30T.index[-1].tz_localize(None):
                    end_date = regional_fuel_mix_30T.index[-1]
                order = [o for o in regional_fuel_mix_30T[region].columns.sort_values() if o in regional_fuel_mix_30T[region].iloc[-1].dropna().index]
                fuel_mix_mean = plot(
                    regional_fuel_mix_30T[region][regional_fuel_mix_d[region].iloc[-1].dropna().index].loc[start_date:end_date,order],
                    yTitle=Info_data.loc['fuel_mix_mean', 'y'], mode='bar', bar_mode='stack', VEPC_image=True, bargap=0,
                    legend_shift=-0.25, colour_set='Dark2', colour_shift=1)

                price = plot(regional_data_30T[region]['price'].loc[start_date:end_date],
                             yTitle=Info_data.loc['price', 'y'], line_shape='hv', VEPC_image=True, bargap=0,
                             legend_shift=-0.25, colour_set='Dark2', colour_shift=0, n=8)
                avil = plot(regional_data_30T[region]['avil'].loc[start_date:end_date],
                            yTitle=Info_data.loc['avil', 'y'], line_shape='hv', VEPC_image=True, bargap=0,
                            legend_shift=-0.25, colour_set='Dark2', colour_shift=0, n=8)
                interconector = plot(regional_data_30T[region][['Interconnector_Export', 'Interconnector_Import']].loc[
                                         start_date: end_date], mode='bar', bar_mode='relative', colour_set='Dark2',
                                     yTitle=Info_data.loc['interconector', 'y'], bargap=0, barline=2)
                consumption = plot(regional_data_30T[region]['consumption'].loc[start_date:end_date],
                                   yTitle=Info_data.loc['consumption', 'y'], line_shape='hv', VEPC_image=True, bargap=0,
                                   legend_shift=-0.25, colour_set='Dark2', colour_shift=0, n=8)
                d = regional_data_d.loc[:, regional_data_d.columns.get_level_values(1) == 'consumption_min'][
                        [region]].droplevel(1, axis=1).loc[start_date:end_date]

                consumption_min = plot(
                    d,
                    yTitle=Info_data.loc['consumption_min', 'y'], line_shape='hv', VEPC_image=True, bargap=0,
                    legend_shift=-0.25, colour_set='Dark2', colour_shift=0, n=8,  barline=0, )
                d = regional_data_d.loc[:, regional_data_d.columns.get_level_values(1) == 'consumption_max'][
                        [region]].droplevel(1, axis=1).loc[start_date:end_date]
                consumption_max = plot(
                    d,
                    yTitle=Info_data.loc['consumption_max', 'y'], line_shape='hv', VEPC_image=True, bargap=0,
                    legend_shift=-0.25, colour_set='Dark2', colour_shift=0, n=8, barline=0, )
            spinner_region = ''
            return [fuel_mix_mean.to_dict(), price.to_dict(), avil.to_dict(), consumption.to_dict(),interconector.to_dict(),consumption_min.to_dict(),consumption_max.to_dict(),  spinner_region]

        for ID in ['fuel_mix_mean', 'price', 'consumption', 'avil', 'interconector','consumption_min','consumption_max']:#Info_data.index:
            create_modal_callback(ID,app)
            create_regional_downloads(ID, app)

    elif tab == 'Renewable Summary':
        type='renewable'

        @app.callback(
            Output(type + "-alert-fade", "is_open"),
            [Input("freq_"+type, "value"),
             Input(type+'-date-range', 'start_date'),
             Input(type+'-date-range', 'end_date')],
        )
        def toggle_alert_no_fade(freq, start_date, end_date):
            if freq == '30T':
                if (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days > 30:
                    return True
            return False

        @app.callback(
            Output("Region_"+type, "children"),
            [Input(type+"-region-select", "value")]
        )
        def get_technology_type(Region):
            regions = {'All regions': 'All Regions',
                       'VIC': 'Victoria',
                       'NSW': 'New South Wales',
                       'QLD': 'Queensland',
                       'SA': 'South Australia',
                       'TAS': 'Tasmania'}
            return regions[Region]


        @app.callback(
            [Output('percent_demand', "figure"),
             Output('renewables', "figure"),
             Output('MVWAP', "figure"),
             Output('residual_demand', "figure"),
            Output('spinner_renewable', "children")],
            Input(type + '_generate', 'n_clicks'),
            [State(type+"-region-select", "value"),
             State("freq_"+type, "value"),
             State(type+"-date-range", 'start_date'),
             State(type+"-date-range", 'end_date')
             ],
        )
        def get_renewable_app_figures(clicks,region, freq, start_date, end_date):
            # start_date=str(start_date)
            # end_date=str(end_date)
            if freq != '30T':
                if pd.to_datetime(end_date) > renewable_data_d.index[-1].tz_localize(None):
                    end_date = renewable_data_d.index[-1]

                if freq in ['ys', 'Q']:
                    mode = 'bar'
                    bar_gap = 0.1
                else:
                    mode = 'line'
                    bar_gap = 0

                percent_demand = plot(
                    renewable_data_d[region]['percent_demand'].loc[start_date:end_date].resample(freq).mean(),
                    yTitle=Info_data.loc['percent_demand', 'y'],
                    mode='bar',
                    bar_mode='stack', VEPC_image=True, bargap=bar_gap, barline=3, legend_shift=-0.25, colour_set='Dark2',
                    colour_shift=1)

                renewables = plot(
                    renewable_data_d[region]['renewables'].loc[start_date:end_date].resample(freq).mean(),
                    yTitle=Info_data.loc['renewables', 'y'],
                    mode='bar',
                    bar_mode='stack', VEPC_image=True, bargap=bar_gap, barline=3, legend_shift=-0.25, colour_set='Dark2',
                    colour_shift=1)

                MVWAP = plot(renewable_data_d[region]['MVWAP'].resample(freq).mean().loc[start_date:end_date],
                             yTitle=Info_data.loc['MVWAP', 'y'],
                             line_shape='hv', VEPC_image=True, bargap=bar_gap, legend_shift=-0.25,
                             colour_set='Dark2',
                             colour_shift=1, n=8, mode=mode, barline=0, )
                d=pd.concat([renewable_data_d[region]['min_residual_demand']['residual_demand'].resample(freq).min().loc[
                           start_date:end_date],
                           renewable_data_d[region]['residual_demand']['residual_demand'].resample(freq).mean().loc[
                           start_date:end_date],
                           renewable_data_d[region]['max_residual_demand']['residual_demand'].resample(freq).max().loc[
                           start_date:end_date],
                           ], axis=1,
                          keys=['Minimum residual_demand', 'Average residual demand', 'Maximum residual_demand'])

                residual_demand = plot(
                    d.resample(freq).mean().loc[start_date:end_date],
                    yTitle=Info_data.loc['residual_demand', 'y'],
                    line_shape='hv', VEPC_image=True, bargap=bar_gap, legend_shift=-0.25,
                    colour_set='Dark2',
                    colour_shift=1, n=8, mode=None, barline=0)

            else:
                if (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days > 30:
                    start_date = pd.to_datetime(end_date) - pd.DateOffset(days=30)

                if pd.to_datetime(end_date) > renewable_data_30T.index[-1].tz_localize(None):
                    end_date = renewable_data_30T.index[-1]

                percent_demand = plot(renewable_data_30T[region]['percent_demand'].loc[start_date:end_date],
                                      yTitle=Info_data.loc['percent_demand', 'y'],
                                      mode='bar',
                                      bar_mode='stack', VEPC_image=True, bargap=0, barline=3, legend_shift=-0.25,
                                      colour_set='Dark2',
                                      colour_shift=1)

                renewables = plot(renewable_data_30T[region]['renewables'].loc[start_date:end_date],
                                  yTitle=Info_data.loc['renewables', 'y'],
                                  mode='bar',
                                  bar_mode='stack', VEPC_image=True, bargap=0, barline=3, legend_shift=-0.25,
                                  colour_set='Dark2',
                                  colour_shift=1)

                MVWAP = plot(renewable_data_30T[region]['MVWAP'].loc[start_date:end_date],
                             yTitle=Info_data.loc['MVWAP', 'y'],
                             line_shape='hv', VEPC_image=True,  legend_shift=-0.25,
                             colour_set='Dark2',
                             colour_shift=1, n=8, barline=0, )
                residual_demand = plot(renewable_data_30T[region]['residual_demand'].loc[start_date:end_date],
                                       yTitle=Info_data.loc['residual_demand', 'y'],
                                       line_shape='hv', VEPC_image=True,  legend_shift=-0.25,
                                       colour_set='Dark2',
                                       colour_shift=1, n=8, barline=0)
            spinner = ''
            return [percent_demand.to_dict(), renewables.to_dict(), MVWAP.to_dict(), residual_demand.to_dict(),
                    spinner]

        for ID in ['percent_demand', 'renewables', 'MVWAP', 'residual_demand']:
            create_modal_callback(ID, app)
            create_renewables_downloads(ID, app, type='renewable')
    elif tab == 'interconnector':
        type = 'interconnector'
        create_interconnector_downloads('interconnector_flow', app, type='interconnector')
        create_modal_callback('interconnector_flow', app)

        @app.callback(
            Output("Region_" + type, "children"),
            [Input(type + "-region-select", "value")]
        )
        def get_technology_type(Region):
            return Region



        @app.callback(
            Output(type + "-alert-fade", "is_open"),
            [Input("freq_" + type, "value"),
             Input(type + '-date-range', 'start_date'),
             Input(type + '-date-range', 'end_date')],
        )
        def toggle_alert_no_fade(freq, start_date, end_date):
            if freq == '30T':
                if (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days > 30:
                    return True
            return False

        @app.callback(
            [Output('interconnector_flow', "figure"),
             Output('spinner_interconnector', "children")],
            [Input(type + '_generate', 'n_clicks')],
            [State(type + "-region-select", "value"),
                   State("freq_" + type, "value"),
                   State(type + "-date-range", 'start_date'),
                   State(type + "-date-range", 'end_date')
                   ],
        )
        def get_interconnector_app_figures(clicks, interconnector, freq, start_date, end_date):
            if freq != '30T':
                if pd.to_datetime(end_date) > renewable_data_d.index[-1].tz_localize(None):
                    end_date = renewable_data_d.index[-1]

                if freq in ['ys', 'Q']:
                    #mode = 'bar'
                    bar_gap = 0.1
                else:
                    #mode = 'line'
                    bar_gap = 0
                interconnector_flow = plot(
                    interconnector_data_d[interconnector][['Reverse Flow','Forward Flow']].loc[start_date:end_date].resample(freq).mean(),
                    yTitle=Info_data.loc['interconnector_flow', 'y'],
                    mode='bar',
                    bar_mode='relative', VEPC_image=True, bargap=bar_gap, barline=2, legend_shift=-0.25,
                    colour_set='Dark2',
                    colour_shift=2)

            else:
                if (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days > 30:
                    start_date = pd.to_datetime(end_date) - pd.DateOffset(days=30)

                if pd.to_datetime(end_date) > renewable_data_30T.index[-1].tz_localize(None):
                    end_date = renewable_data_30T.index[-1]

                interconnector_flow = plot(interconnector_data_30T[interconnector][['EXPORTLIMIT', 'METEREDMWFLOW','IMPORTLIMIT']].loc[start_date:end_date],
                                      yTitle=Info_data.loc['interconnector_flow', 'y'],
                                      bar_mode=None, VEPC_image=True, bargap=0, barline=2, legend_shift=-0.25,
                                      colour_set='Dark2',
                                      colour_shift=3,n=8)


            spinner = ''
            return [interconnector_flow.to_dict(), spinner]

        for ID in ['percent_demand', 'renewables', 'MVWAP', 'residual_demand']:
            create_modal_callback(ID, app)
            create_renewables_downloads(ID, app, type='renewable')
    
    return app.server