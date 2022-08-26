import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objs as go

def get_colours_for_labels_n(labels=['<$0','$0-20', '$20-40', '$40-60','$60-80','$80-100','$100-150','$150-300','$300-1000','$1000-5000','>$5000'],colour_set='nipy_spectral',notebook=False,fade=False,n=False,colour_shift=0,Fuel_colours=True):
    '''
    Returns a dictionary with unique colours for each lablel
    '''
    import matplotlib
    labels=list(labels)
    
    if colour_shift>0:
        [labels.insert(i, i) for i in range(colour_shift) ]
    if n:
        if len(labels)<n:
            labels.extend(list(range(n-len(labels))))
    print(labels)
    cmap = matplotlib.cm.get_cmap(colour_set,lut=len(labels))
    i=0
    colours={}
    if fade==False:
        fade=256
    for l in labels:
        
        colours[l]='rgb('+str(round(cmap(i)[0]*256))+','+str(round(cmap(i)[1]*256))+','+str(round(cmap(i)[2]*256))+','+str(round(cmap(i)[3]*fade))+')'
        i=i+1
    if Fuel_colours:
        colours['Large Scale Solar'] = 'gold'
        colours['Rooftop Solar'] = 'darkorange'
        colours['Wind'] = 'mediumseagreen'
        colours['Black Coal'] = 'black'
        colours['Brown Coal'] = 'sienna'
        colours['Natural Gas'] = 'grey'
        colours['Natural Gas (OCGT)'] = 'DimGray'
        colours['Natural Gas (Steam)'] = 'slategrey'
        colours['Natural Gas (CCGT)'] = 'Silver'
        colours['Hydro'] = 'SteelBlue'
        colours['Other Fuels'] = 'orange'
        colours['Water'] = colours['Hydro']
        colours['Battery'] = 'orange'
        colours['Coal Seam Methane'] = 'red'

    return colours
   
def plot(df, mode='scatter', bar_mode=None,line_mode='lines',yTitle='',xTitle='',horizontal_legend=True,template='simple_white',colour_set='nipy_spectral',line_shape=None,
         title=None,stackgroup=None,xlim=None,ylim=None, VEPC_image=True, legend_shift=None,n=False,x_tick_interval=False,y_tick_interval=False,colour_shift=0,
         Fuel_colours=True,bargap=None,barline=0,transparent=True,narrow=False,tozero=False,VEPC_Big_image=False,b=20):
    
        fig = go.Figure()

        
        try:
            df=df.to_frame()
        except:
            a=1
        df.columns=df.columns.astype(str)
        columns=df.columns
        if colour_set:
            col=get_colours_for_labels_n(columns,colour_set=colour_set,n=n,colour_shift=colour_shift,Fuel_colours=Fuel_colours)
        
            
        if mode=='bar':
             for trace in list(df.columns):
                fig.add_trace(
                    go.Bar(x=df.index, y=df[trace], name=trace.replace('_',' '),marker=dict(color=col[trace],line=dict(width=barline, color=col[trace])))
                )
                fig.update_layout(barmode=bar_mode)
        elif mode=='hist':
            fig = go.Figure()
            for trace in df.columns:
                fig.add_trace(go.Histogram(x=df[trace],marker=dict(color=col[trace]),name=trace.replace('_',' ')))
            # Overlay both histograms
            if len(df.columns)>1:
                fig.update_layout(barmode='overlay')
                # Reduce opacity to see both histograms
                fig.update_traces(opacity=0.6)
        else:
            for trace in list(df.columns):
                    if colour_set:
                        colour=col[trace]
                    else:
                        colour=None
                    fig.add_trace(
                        go.Scatter(x=df.index, y=df[trace], name=trace.replace('_',' ') , mode=line_mode,line_shape=line_shape,stackgroup=stackgroup, marker=dict(color=colour))
                    )
        fig.update_xaxes(title=xTitle,tickangle=90)
        fig.update_yaxes(title=yTitle)
        #fig.show()
        if horizontal_legend:
            fig.update_layout(legend_orientation="h")
        fig.update_layout(template=template,title=title,legend=dict(y=legend_shift) ,font=dict(color='black'),bargap=bargap,autosize=True)

        fig.update_xaxes(range=xlim)
        fig.update_yaxes(range=ylim)
        
        if x_tick_interval:
            fig.update_layout(
                        xaxis = dict(
                            tickmode = 'linear',
                            tick0 = 0,
                            dtick = x_tick_interval
                        )
                    )
        if y_tick_interval:
            fig.update_layout(
                        yaxis = dict(
                            tickmode = 'linear',
                            tick0 = 0,
                            dtick = y_tick_interval
                        )
                    )
        if VEPC_Big_image:
            fig.add_layout_image(
                dict(
                    source="https://static.wixstatic.com/media/cb01c4_8b6a2bf455364d6980434eb57d584a2e~mv2_d_3213_1275_s_2.jpg",
                    xref="paper", yref="paper",
                    x=0, y=0,
                    sizex=0.4, sizey=0.2,opacity=0.75,
                    xanchor="left", yanchor="bottom"
                )
            )
            VEPC_image=False
            fig.update_yaxes(ticks="inside")
            fig.update_yaxes(spikethickness=0.8,spikemode  = 'across+toaxis')
            fig.update_layout(title_x=0.5,title_y=0.95)
        if VEPC_image:
            fig.add_layout_image(
                dict(
                    source="https://static.wixstatic.com/media/cb01c4_8b6a2bf455364d6980434eb57d584a2e~mv2_d_3213_1275_s_2.jpg",
                    xref="paper", yref="paper",
                    x=0, y=0,
                    sizex=0.18, sizey=0.18,opacity=0.75,
                    xanchor="left", yanchor="bottom"
                )
            )
            
         
        if transparent:
            fig = fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                                             plot_bgcolor='rgba(0,0,0,0)')
        if tozero:
            fig.update_yaxes(rangemode="tozero")
        if narrow==True:
            fig.update_layout(margin=dict(l=20,t=50,r=10,b=b))
        else:

            fig.update_layout(margin=dict(r=20,t=20,b=b))
        return fig
   
def crop_image(filename):
    from PIL import Image, ImageChops

    def trim(im):
        bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
        diff = ImageChops.difference(im, bg)
        diff = ImageChops.add(diff, diff, 2.0, -100)
        bbox = diff.getbbox()
        if bbox:
            return im.crop(bbox)

    im = Image.open(filename)
    im = trim(im)
    im.save(filename)

def plot_POE_any_data(input_data, region='VIC', years=[2018], hide_POE=False, name='', y_title='add title',
                      line_type='mean',
                      columns=True, colour_shift=0, y_range=[None, None], save_folder=None, seasonal=False,
                      weekend_weekday=False, notebook=True,freq=None,dash_alt=False,supress_year=False,rolling=False,legend_shift=None,hide_title=False,n=0):
    '''
    plots the POE For generation scada output,

    This only works for NSW import EXport Change convention for signs for other regions
    '''
   
    import NEM_data_load
    from colour import Color
    def rgba_transparent(colour, ratio=0.2):
        try:
            c = Color(colour).rgb
        except:
            c=list(colour)
        return 'rgba(' + str(c[0]) + ',' + str(c[1]) + ',' + str(c[2]) + ',' + str(ratio) + ')'
    
    input_data['hour_index'] = input_data.index.map(NEM_data_load.hour_of_the_day)
    if freq==None:
        freq=pd.infer_freq(input_data.index)
        input_data['hour_index'] = input_data.index.map(NEM_data_load.hour_of_the_day)
        if freq=='30T':
            x_time = pd.date_range('00:00:00', periods=48, freq="30min")
        elif freq=='5T':
            x_time = pd.date_range('00:00:00', periods=48*6, freq=freq)
    else:
        if freq=='30T':
            x_time = pd.date_range('00:00:00', periods=48, freq="30min")
        elif freq=='5T':
            x_time = pd.date_range('00:00:00', periods=48*6, freq=freq)
    col = plt.rcParams['axes.prop_cycle'].by_key()['color']
    col = col[colour_shift:]
    col.extend(col)
    if columns:
        column_list = [col for col in input_data.columns if col != 'hour_index']
        print(column_list)
    else:
        column_list = ['']
    if seasonal:
        seasons = ['Summer', 'Spring', 'Autumn', 'Winter']
    else:
        seasons = ['']
    if weekend_weekday:
        weekend_weekdays = ['Mon-Fri', 'Sat-Sun']
    else:
        weekend_weekdays = ['']

    input_data_original = input_data.copy()
    for Season in seasons:
        for day_type in weekend_weekdays:
            input_data = input_data_original.copy()
            all_data = []
            c = 0
            num = 0
            dash=None
            for column in column_list:
                for year in years:
                    
                    colour = col[c]

                    if not year == None:
                        yearly_input_data = input_data.loc[str(year)]
                        print(len(yearly_input_data))
                        if columns:
                            col_list = [column, 'hour_index']
                            yearly_input_data = yearly_input_data[col_list]
                        if seasonal == True:
                            Season = Season.replace(', ', '')
                            yearly_input_data = yearly_input_data.loc[
                                yearly_input_data.index.map(NEM_data_load.season) == Season]
                            if ',' not in Season:
                                Season = ', ' + Season
                        if weekend_weekday:
                            print(day_type)
                            if 'Mon-Fri' in day_type:
                                yearly_input_data = yearly_input_data.loc[yearly_input_data.index.dayofweek < 5]
                            elif 'Sat-Sun' in day_type:
                                yearly_input_data = yearly_input_data.loc[yearly_input_data.index.dayofweek >= 5]
                            if ',' not in day_type:
                                day_type = ', ' + day_type
                    else:
                        yearly_input_data = input_data  # .resample('30T').mean()
                    # return yearly_input_data
                    if line_type == 'mean':
                        av_mean = yearly_input_data.groupby(by='hour_index').mean()
                    elif line_type == 'median':
                        av_mean = yearly_input_data.groupby(by='hour_index').quantile(0.5)
                    elif line_type == 'pearson':
                        av_mean = yearly_input_data.groupby(by='hour_index').quantile(0.5)
                        
                    av_90 = yearly_input_data.groupby(by='hour_index').quantile(0.1)
                    av_10 = yearly_input_data.groupby(by='hour_index').quantile(0.9)

                    if hide_POE:
                        av_90 = av_90 * np.nan
                        av_10 = av_10 * np.nan
                        name_poe = column + Season + day_type + ', ' + str(
                                year) 
                    else:
                        if columns:
                            name_poe = column + Season + day_type + ', ' + str(
                                year) + ' (10% POE, ' + line_type + ' & 90% POE)'
                        else:
                            name_poe = str(year) + Season + day_type + ',  (10% POE, ' + line_type + ' & 90% POE)'
                    name_poe = name_poe.replace('_', ' ')
                    if supress_year:
                        name_poe=name_poe.replace(', ' + str(year),'')
                    if hide_POE:
                        
                        fill='none'
                        colour=rgba_transparent(colour, ratio=1)
                        fillcolor=None
                    else:
                        fill='tonexty'
                        fillcolor=rgba_transparent(colour)
                        colour=rgba_transparent(colour, ratio=1)
                    if rolling:
                        av_90=av_90.rolling(window=5).mean()
                        av_10=av_10.rolling(window=5).mean()
                        av_mean=av_mean.rolling(window=5).mean()
                    upper_bound = go.Scatter(
                        name='Upper Bound',
                        x=x_time,
                        y=av_90.values[:, 0],
                        mode='lines',
                        marker=dict(color="#444"),
                        line=dict(width=0.8, dash='dot', color=colour),
                        fillcolor=fillcolor,
                        fill=fill, showlegend=False)

                    trace = go.Scatter(
                        name=name_poe,  # + feature[0].replace('_',' '),
                        x=x_time,
                        y=av_mean.values[:, 0],
                        mode='lines',
                        line=dict(color=colour, shape=None,dash=dash),
                        fillcolor=fillcolor,
                        fill=fill)

                    lower_bound = go.Scatter(
                        name='Lower Bound',
                        x=x_time,
                        y=av_10.values[:, 0],
                        marker=dict(color="#444"),
                        line=dict(width=0.8, dash='dot', color=colour),
                        opacity=.10,
                        mode='lines', showlegend=False)
                    if hide_POE:
                        data = [trace]
                    else:
                        data = [lower_bound, trace, upper_bound]
                    all_data.extend(data)
                    if dash_alt:
                        num=num+1
                           
                        if (num % 2) == 0:
                            c=c+1
                            dash=None
                        else:
                            dash='dot'
                            
                    else:
                        c = c + 1
                    
            name_output = (name + Season + day_type).replace(',,', ',')
            if hide_title==True:
                title_t=None
            else:
                title_t=name_output
            layout = go.Layout(yaxis=
                               dict(title=y_title, range=y_range), xaxis=dict(tickformat='%I:%M %p', type='date'),
                               title=title_t,
                               legend=dict(orientation='h', y=-0.1))

            fig = go.Figure(data=all_data, layout=layout)
            template='simple_white'
            fig.update_layout(template=template,legend=dict(y=legend_shift) ,font=dict(color='black'))
            if hide_POE == True:
                name = name + ' Without POE'

            from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
            if notebook:
                fig.show()  # py.iplot(fig, filename='overlaid histogram')
            if save_folder:
                import os
                if not os.path.exists(save_folder):
                    os.makedirs(save_folder)
                print('Saving Image')
                filename = save_folder + '/' + name_output + '.png'
                fig.write_image(filename, scale=3,width=800.0, height=400.0)
                crop_image(filename)
                filename = save_folder + '/' + name_output + '.html'
                fig.write_html(filename)
    return fig
                         
def save_fig(fig,name_output,save_folder, zip=False, scale=3, width=600 * 1.5, height=250 * 1.5):
                import os
                if not os.path.exists(save_folder):
                    os.makedirs(save_folder)
                print('Saving Image')
                filename = save_folder + '/' + name_output + '.png'
                fig.write_image(filename, scale=scale, width=width, height=height)
                crop_image(filename)
                filename = save_folder + '/' + name_output + '.html'
                fig.write_html(filename)
                if zip:
                    save_zip(directory_name = save_folder, zip_name=None)
