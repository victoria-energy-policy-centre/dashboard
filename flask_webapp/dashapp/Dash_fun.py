from datetime import datetime, timedelta
import dash_html_components as html
import pandas as pd
import os
import pickle

def save_object(obj, session_id, name):
    os.makedirs('Dir_Store', exist_ok=True)
    file = 'Dir_Store/{}_{}'.format(session_id, name)
    pickle.dump(obj, open(file, 'wb'))
    
def load_object(session_id, name):
    file = 'Dir_Store/{}_{}'.format(session_id, name)
    obj = pickle.load(open(file, 'rb'))
    os.remove(file)
    return obj

def clean_Dir_Store():
    if os.path.isdir('Dir_Store'):
        file_list = pd.Series('Dir_Store/' + i for i in os.listdir('Dir_Store'))
        mt = file_list.apply(lambda x: datetime.fromtimestamp(os.path.getmtime(x))).astype(str)
        for i in file_list[mt < str(datetime.now() - timedelta(hours = 3))]: os.remove(i)
        
def apply_layout_with_auth(dash_app, layout):
    def serve_layout():
        session_id = "test"
        return html.Div([
            html.Div(session_id, id='test', style={'display': 'none'}),
            layout
        ])
    
    dash_app.config.suppress_callback_exceptions = True
    dash_app.layout = serve_layout
