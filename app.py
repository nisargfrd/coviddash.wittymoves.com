from flask import Flask, redirect, render_template
import urllib.request
import pandas as pd
import plotly.offline as pyo
import json
import plotly
import plotly.graph_objects as go
import math
import numpy as np
import os
import time
from datetime import date
# To merge geojson data and cases data:
import geopandas as gpd

# To create custom maps:
import folium

# To fetch District level data link:
from bs4 import BeautifulSoup
import re
import requests

# pyo.init_notebook_mode()

app = Flask(__name__)
app.debug = True


# Load Data:
#my_path='/home/ubuntu/CovidApp/COVID_19_Flask/'
my_path='/run/media/nisarg/Drive2/AWS - Nisarg Covid Instance/Elastic_IP/CovidApp/COVID_19_Flask/'
def load_wiki_data():
    ## Set Working Directory:
    os.chdir(my_path)

    df_wiki = pd.read_csv("output/covid-wiki-data.csv")
    df_wiki.fillna("0", inplace=True)
    df_wiki['Recovered'] = df_wiki['Recovered'].fillna(0.0).astype(float).astype(int)
    
    return df_wiki

def load_india_data():
    ## Set Working Directory:
    os.chdir(my_path)

    df_india = pd.read_csv('output/India_confirmed_cases.csv')
    df_india.fillna("0", inplace=True)
    gps=gpd.read_file("output/Updated_Geojson_data.geojson")
    
    return df_india, gps

def load_global_conf_data():
    ## Set Working Directory:
    os.chdir(my_path)
    
    df_conf = pd.read_csv("output/group-covid-Confirmed.csv")
    
    return df_conf 

def load_global_death_data():
    ## Set Working Directory:
    os.chdir(my_path)
    
    df_death = pd.read_csv("output/group-covid-Death.csv")
    
    return df_death 

def load_global_recover_data():
    ## Set Working Directory:
    os.chdir(my_path)
    
    df_recovered = pd.read_csv("output/group-covid-Recovered.csv")
    
    return df_recovered


## Plotting Confirmed cases:

def world_map():
    
    df_wiki=load_wiki_data()
    
    # Generate a list for color gradient display
    colorList = []
    color=[]
    remaining=0
    
    for comfirmed, recovered, deaths in zip(df_wiki["Confirmed_Cases"], df_wiki["Recovered"].fillna(0), df_wiki["Deaths"]):
        remaining = int(comfirmed) - int(deaths) - int(recovered)
        colorList.append(math.ceil(remaining))
    
    df_wiki['Active']=colorList

    del remaining
    df_remain = pd.DataFrame({'Remaining':np.array(colorList)})

    [color.append('#d7191c') if i>0 else '#1a9622' for i in colorList]

    # To deal with negative values:
    tmp1=df_remain.copy()
    l=[]
    [l.append(i) if i>0 else l.append(0) for i in tmp1['Remaining'].values]

    fig = go.Figure(data=go.Scattergeo(
            lon = df_wiki['Long'],
            lat = df_wiki['Lat'],
            #text = df_conf['Province/State'].fillna("")+df_conf['Country/Region']+"</br>"+"Confirmed Cases: "+df_conf.iloc[:,-1].astype(str)+"</br>Death Cases: "+df_death.iloc[:,-1].astype(str)+"</br>Recovered Cases: "+df_recovered.iloc[:,-1].astype(str)+"</br>Remaining Cases: "+df_remain.iloc[:,-1].astype(str),
            text = df_wiki['Locations']+"</br>"+"Confirmed Cases: "+df_wiki['Confirmed_Cases'].astype(str)+"</br>Death Cases: "+df_wiki['Deaths'].astype(str)+"</br>Recovered Cases: "+df_wiki['Recovered'].astype(str)+"</br>Active Cases: "+df_remain.iloc[:,-1].astype(str),
            mode = 'markers',
            #showlegend=True,

            #marker_color = df_conf.iloc[:,-1],
            marker=go.scattergeo.Marker(
                #color=['#d7191c' if i>0 else '#1a9622' for i in colorList],
                #colorscale = 'Magenta',
                cmin = 0,
                color = df_remain.iloc[:,-1],
                cmax = (df_remain.iloc[:,-1].max()),
                colorbar_title="Active Patients:",

                colorbar=dict(lenmode='pixels', len=300),

                #size=[i**(1/3) for i in df_conf.iloc[:,-1]],
                size=[i**(1/3) for i in l],
                sizemin=1,
                sizemode='area',
                sizeref=2.*max([math.sqrt(i) for i in l])/(100.**2)
                        #org 2.*max([math.sqrt(max(i,0)) for i in df_conf.iloc[:,-1]])/(100.**2)
                        #2.*max([math.sqrt(max(i,0)) for i in df_conf.iloc[:,-1]])/(100.**2)
            )
            ))

    fig.update_layout(
            #title = '<b>CORONAVIRUS Spread</b>',
            #paper_bgcolor='#cbd2d3',
            autosize=True,
            #width=800,
            #height=500,
            margin=dict(
                l=10,
                r=10,
                b=10,
                t=75,
                pad=0
                ),
            geo = go.layout.Geo(
                #bgcolor='#cbd2d3',
                resolution=110,
                scope='world',
                showland = True,
                countrywidth = 0.5,
                subunitwidth = 0.5,
                showsubunits = True,
                showcountries = True,
                showframe=True,
                #subunitcolor = "rgb(225, 225, 0)",
                projection = dict(
                type = 'orthographic',
                #scale=1
                #scale=1
                ),
                lonaxis_range = [ -400.0, 400.0 ], # Y-axis
                lataxis_range = [ -400.0, 400.0 ], # X-axis
                #center=dict(lon=78.66,
                #            lat=22.35)
            )

        )
    
    del df_remain

    pyo.plot(fig,filename = 'output/World.html', auto_open=False)
    
    return fig, df_wiki.drop(["Lat","Long"], axis=1)


## Plotting India Specific Case Data:

def india_map():
    
    df_india, gps = load_india_data()
    
    # Bins for the confirmed cases:
    bins=[0,1,100,501,1001,3001]
    my_map3 = folium.Map(#location = [22.9734, 78.6569],
                         location = [19.7515, 75.7139],
                         max_zoom=8,
                         min_zoom=3,
                         zoom_start = 4,
                         #width=700,
                         #height=450
                        )

    folium.Choropleth(
        geo_data=gps,
        data=df_india,
        name='Total cases in India (including Foreign National)',
        columns=['State/UT', 'Total Confirmed cases (including Foreign National)'],
        key_on='feature.properties.NAME',
        bins=bins,
        fill_color='YlGn',
        fill_opacity=1,
        legend_name='Confirmed Cases',
        highlight=True
    ).add_to(my_map3).geojson.add_child(folium.GeoJsonTooltip(
        fields=['NAME','Total Confirmed cases (including Foreign National)','Cured/Discharged/Migrated','Death'],
        aliases=['State/UT','Confirmed Cases','Recovered Cases','Death Cases'], 
        localize=True
        )
    )

    df_india["Active"]=df_india['Total Confirmed cases (including Foreign National)']-df_india['Cured/Discharged/Migrated']-df_india['Death']

    #title_html = '''
    #    <h4 align="center" style="font-size:17px"><b>Total cases in India (including Foreign National)</b></h4>
    #    <h6 align="center" style="font-size:13px"><i>Hover over the State/UT to check the respective case counts</i></h6>'''
    #my_map3.get_root().html.add_child(folium.Element(title_html))
    
    my_map3.save('output/India.html')
    my_map3.save('templates/India.html')
    return my_map3, df_india


## Line plot for total confirmed cases for 20 most affected Countries in last 3 days:

def most_affected_20():

    df_gc = load_global_conf_data()
    
    df_gc = df_gc.sort_values(by=df_gc.columns[-1],ascending=False)

    bar_fig = go.Figure()

    bar_fig.add_trace(go.Bar(
        x=df_gc["Country/Region"][:20].values,
        y=df_gc.iloc[:,-1].values,
        #mode = 'lines+markers',
        name = df_gc.columns[-1],
        marker_color='rgb(55, 83, 109)'
        ))

    bar_fig.add_trace(go.Bar(
        x=df_gc["Country/Region"][:20].values,
        y=df_gc.iloc[:,-2].values,
        #mode = 'lines+markers',
        name = df_gc.columns[-2],
        marker_color='rgb(26, 118, 255)'
        ))

    bar_fig.add_trace(go.Bar(
        x=df_gc["Country/Region"][:20].values,
        y=df_gc.iloc[:,-3].values,
        #mode = 'lines+markers',
        name = df_gc.columns[-3],
        marker_color='rgb(0, 175, 90)'
        ))

    bar_fig.update_layout(
        title='<b>Total Confirmed cases</b>',
        # width=680,
        # height=500,
        xaxis=dict(
            title='Top 20 countries with most confirmed cases',
            titlefont_size=14,
            tickfont_size=12,
            tickangle = -45
        ),
        yaxis=dict(
            title='Confirmed Cases (In thousands)',
            titlefont_size=14,
            tickfont_size=12,
        ),
        legend=dict(
            #x=0.9,
            #y=0.9,
            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)'
        ),

        barmode='group',
        bargap=0.15, # gap between bars of adjacent location coordinates.
        bargroupgap=0.1 # gap between bars of the same location coordinate.
    )

    pyo.plot(bar_fig, filename="output/Top_20_Conf_Cases.html", auto_open=False)
    return bar_fig


## Line plot for total death cases for top 20 Countries in last 3 days:

def most_death_20():
    
    #df_gd = df_death.groupby('Country/Region')[df_death.columns[4:]].sum().reset_index()
    df_gd = load_global_death_data()
    df_gd = df_gd.sort_values(by=df_gd.columns[-1],ascending=False)

    bar_fig3 = go.Figure()

    bar_fig3.add_trace(go.Bar(
        x=df_gd["Country/Region"][:20].values,
        y=df_gd.iloc[:,-1].values,
        #mode = 'lines+markers',
        name = df_gd.columns[-1],
        marker_color='rgb(220,20,60)'
        ))

    bar_fig3.add_trace(go.Bar(
        x=df_gd["Country/Region"][:20].values,
        y=df_gd.iloc[:,-2].values,
        #mode = 'lines+markers',
        name = df_gd.columns[-2],
        marker_color='rgb(178,34,34)'
        ))

    bar_fig3.add_trace(go.Bar(
        x=df_gd["Country/Region"][:20].values,
        y=df_gd.iloc[:,-3].values,
        #mode = 'lines+markers',
        name = df_gd.columns[-3],
        marker_color='rgb(219,112,147)'
        ))

    bar_fig3.update_layout(
        title='<b>Total Death cases</b>',
        # width=680,
        # height=500,
        xaxis=dict(
            title='20 countries with most Death cases',
            titlefont_size=14,
            tickfont_size=12,
            tickangle=-45
        ),
        yaxis=dict(
            title='Death Cases (In thousands)',
            titlefont_size=14,
            tickfont_size=12,
        ),
        legend=dict(
            #x=0.9,
            #y=0.9,
            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)'
        ),

        barmode='group',
        bargap=0.15, # gap between bars of adjacent location coordinates.
        bargroupgap=0.1 # gap between bars of the same location coordinate.
    )

    pyo.plot(bar_fig3, filename="output/Top_20_Death_Cases.html", auto_open=False)
    return bar_fig3


## Line plot for total recovery cases for top 20 Countries in last 3 days:

def most_recover_20():
    
    df_gr = load_global_recover_data()
    df_gr = df_gr.sort_values(by=df_gr.columns[-1],ascending=False)

    bar_fig5 = go.Figure()

    bar_fig5.add_trace(go.Bar(
        x=df_gr["Country/Region"][:20].values,
        y=df_gr.iloc[:,-1].values,
        #mode = 'lines+markers',
        name = df_gr.columns[-1],
        marker_color='rgb(137,178,174)'
        ))

    bar_fig5.add_trace(go.Bar(
        x=df_gr["Country/Region"][:20].values,
        y=df_gr.iloc[:,-2].values,
        #mode = 'lines+markers',
        name = df_gr.columns[-2],
        marker_color='rgb(91,129,142)'
        ))

    bar_fig5.add_trace(go.Bar(
        x=df_gr["Country/Region"][:20].values,
        y=df_gr.iloc[:,-3].values,
        #mode = 'lines+markers',
        name = df_gr.columns[-3],
        marker_color='rgb(35,66,87)'
        ))

    bar_fig5.update_layout(
        title='<b>Total Recovered cases</b>',
        # width=680,
        # height=500,
        xaxis=dict(
            title='20 countries with most Recovered cases',
            titlefont_size=14,
            tickfont_size=12,
            tickangle=-45
        ),
        yaxis=dict(
            title='Recovered Cases (In thousands)',
            titlefont_size=14,
            tickfont_size=12,
        ),
        legend=dict(
            #x=0.9,
            #y=0.9,
            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)',
            #title = 'hi'
        ),
        barmode='group',
        bargap=0.15, # gap between bars of adjacent location coordinates.
        bargroupgap=0.1 # gap between bars of the same location coordinate.
    )

    pyo.plot(bar_fig5, filename="output/Top_20_Recovered_Cases.html", auto_open=False)
    return bar_fig5


## Line plot for total confirmed cases in India:

def india_conf():
    
    df_gc = load_global_conf_data()
    
    df_gc = df_gc.sort_values(by=df_gc.columns[-1],ascending=False)

    bar_fig2 = go.Figure()

    bar_fig2.add_trace(go.Scatter(
        x=df_gc[df_gc["Country/Region"]=='India'].iloc[:,1:].columns,
        y=df_gc[df_gc["Country/Region"]=='India'].iloc[:,1:].sum(),
        mode = 'lines+markers',
        name = "<b>Growth rate (Linear)</b>",
        marker_color='rgb(55, 83, 109)',
        fill= 'tozeroy',
        showlegend=True
        ))

    bar_fig2.update_layout(
        #title='<b>Total confirmed cases: India</b>',
        legend_orientation="h",
        # width=680,
        # height=500,
        xaxis=dict(
            title='Date (mm/dd/yy)',
            titlefont_size=14,
            tickfont_size=12,
            tickangle=-45
        ),
        yaxis=dict(
            title='Confirmed Cases',
            titlefont_size=14,
            tickfont_size=12,
        ),
        legend=dict(
            #x=0.2,
            #y=0.9,
            x=0,
            y=1.2,

            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)'
        )
    )

    pyo.plot(bar_fig2, filename="output/India_Conf_Cases.html", auto_open=False)
    return bar_fig2


## Line plot for total death cases in India:

def india_death():

    df_gd = load_global_death_data()
    df_gd = df_gd.sort_values(by=df_gd.columns[-1],ascending=False)

    bar_fig4 = go.Figure()

    bar_fig4.add_trace(go.Scatter(
        x=df_gd[df_gd["Country/Region"]=='India'].iloc[:,1:].columns,
        y=df_gd[df_gd["Country/Region"]=='India'].iloc[:,1:].sum(),
        mode = 'lines+markers',
        name = "<b>Death rate (Linear)</b>",
        marker_color='rgb(205,92,92)',
        fill= 'tozeroy',
        showlegend=True
        ))

    bar_fig4.update_layout(
        #title='<b>Total Death cases: India</b>',
        legend_orientation="h",
        # width=680,
        # height=500,
        xaxis=dict(
            title='Date (mm/dd/yy)',
            titlefont_size=14,
            tickfont_size=12,
            tickangle=-45
        ),
        yaxis=dict(
            title='Death Cases',
            titlefont_size=14,
            tickfont_size=12,
        ),
        legend=dict(
            #x=0.2,
            #y=0.9,
            x=0,
            y=1.2,

            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)'
        )
    )

    pyo.plot(bar_fig4, filename="output/India_Death_Cases.html", auto_open=False)
    return bar_fig4

## Line plot for total recovery cases for India:
def india_recovery():

    df_gr = load_global_recover_data()
    df_gr = df_gr.sort_values(by=df_gr.columns[-1],ascending=False)

    bar_fig6 = go.Figure()

    bar_fig6.add_trace(go.Scatter(
        x=df_gr[df_gr["Country/Region"]=='India'].iloc[:,1:].columns,
        y=df_gr[df_gr["Country/Region"]=='India'].iloc[:,1:].sum(),
        mode = 'lines+markers',
        name = "<b>Recovery rate (Linear)</b>",
        marker_color='rgb(102,178,178)',
        fill = 'tozeroy',
        showlegend=True
        ))

    bar_fig6.update_layout(
        #title='<b>Total Recovered cases: India</b>',
        legend_orientation="h",
        # width=680,
        # height=500,
        xaxis=dict(
            title='Date (mm/dd/yy)',
            titlefont_size=14,
            tickfont_size=12,
            tickangle=-45
        ),
        yaxis=dict(
            title='Recovered Cases',
            titlefont_size=14,
            tickfont_size=12,
        ),
        legend=dict(
            #x=0.2,
            #y=0.9,
            x=0,
            y=1.2,

            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)'
        )
    )

    pyo.plot(bar_fig6, filename="output/India_Recovered_Cases.html", auto_open=False)
    return bar_fig6


## Exponential growth plot for India:
def india_conf_exponential():
    
    df_gc = load_global_conf_data()
    
    df_gc = df_gc.sort_values(by=df_gc.columns[-1],ascending=False)


    labels = (df_gc[df_gc["Country/Region"]=='India'].iloc[:,-1:1:-1].columns)

    bar_fig7 = go.Figure()

    bar_fig7.add_trace(go.Scatter(
        #x=(df_gc[df_gc["Country/Region"]=='India'].iloc[:,-1:-8:-1].sum()).values,
        x=(df_gc[df_gc["Country/Region"]=='India'].iloc[:,-1:1:-1].sum()).values,
        
        #y=df_gc[df_gc["Country/Region"]=='India'].iloc[:,-1:-8:-1] - df_gc[df_gc["Country/Region"]=='India'].iloc[:,-2:-9:-1],
        #y=(df_gc[df_gc["Country/Region"]=='India'].iloc[:,-1:-8:-1].sum()).values - (df_gc[df_gc["Country/Region"]=='India'].iloc[:,-2:-9:-1].sum()).values,
        y=(df_gc[df_gc["Country/Region"]=='India'].iloc[:,-1:1:-1].sum()).values - (df_gc[df_gc["Country/Region"]=='India'].iloc[:,-2:0:-1].sum()).values,
        mode = 'lines+markers',
        name = "<b>Logarithmic Growth rate</b>",
        marker_color='rgb(55, 83, 109)',
        fill= 'tozeroy',
        
        #hovertemplate =
        text = ['Date (mm/dd/yy): '+i for i in labels],
        hovertemplate =
            '<i><b>%{text}</b></i>'
            '<br><i><b>New Cases: %{y}</b></i><br>'
            '<extra></extra>',
        showlegend=True
        ))

    bar_fig7.update_layout(
        title='<b>Exponential Growth Rate</b>',
        # width=680,
        # height=500,
        legend_orientation="h",
        autosize=True,
        xaxis=dict(
            title='Total Confirmed Cases (Log Scale)',
            titlefont_size=14,
            tickfont_size=12,
            tickangle=-45,
            type="log",
            rangeslider=dict(
                visible=True
            ),
        ),
        yaxis=dict(
            title='New Cases (Log Scale)',
            titlefont_size=14,
            tickfont_size=12,
            type="log"
        ),
        
        #xaxis_type="log", yaxis_type="log",
        
        legend=dict(
            #x=0.2,
            #y=0.9,

            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)'
        )
    )        

    pyo.plot(bar_fig7, filename="output/India_Conf_log_Cases.html", auto_open=False)
    return bar_fig7
 
def get_district_link():
    response = requests.get('https://www.mohfw.gov.in/index.html')
    pattern = re.compile('District Reportings')
    soup = BeautifulSoup(response.content, "html.parser")
    ul = soup.find_all("ul", {"class":"nav clearfix"})
    district_link=ul[0].find('a', text=pattern).get('href')

    return district_link

def get_last_updated_time():
    return time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime("Data_Scrap.log")))

# def serve_layout():
#     return html.Div(children=[
#         html.H1('Dashboard hi'),
#         html.Div(className='Maps', children=[
#                 html.Div(className='world_map', children=[
#                 dcc.Graph(id='world_map',figure=world_map())]
#                 ),
#                 html.Iframe(className='india_map',srcDoc=open(india_map(), 'r').read(), width='40%', height='500')
#             ]),
#         html.Div(className='Line_plots_conf', children=[
#                 html.Div(className='most_conf', children=[
#                 dcc.Graph(id='most_conf',figure=most_affected_20())]
#                 ),
#                 html.Div(className='most_death', children=[
#                 dcc.Graph(id='most_death',figure=most_death_20())]
#                 ),
#                 html.Div(className='most_recover', children=[
#                 dcc.Graph(id='most_recover',figure=most_recover_20())]
#                 )
#             ]),
#         ])


@app.route('/')
def main():
    
    # Display World Map and its table:
    world_data = world_map()
    wmJSON = json.dumps(world_data[0], cls=plotly.utils.PlotlyJSONEncoder)
    world_table = world_data[1].to_dict('records')
    
    # Display India's Map and its table:
    india_data = india_map()[1]
    india_table = india_data.to_dict('records')

    # Display Confirmed cases of 20 Most Affected countries:
    conf_20_most = most_affected_20()
    c20JSON = json.dumps(conf_20_most, cls=plotly.utils.PlotlyJSONEncoder)

    # Display Death cases of 20 Most Affected countries:
    death_20_most = most_death_20()
    d20JSON = json.dumps(death_20_most, cls=plotly.utils.PlotlyJSONEncoder)

    # Display Recovered cases of 20 Most Affected countries:
    recovered_20_most = most_recover_20()
    r20JSON = json.dumps(recovered_20_most, cls=plotly.utils.PlotlyJSONEncoder)

    # Display Confirmed cases of India:
    conf_ind = india_conf()
    cindJSON = json.dumps(conf_ind, cls=plotly.utils.PlotlyJSONEncoder)

    # Display Death cases of India:
    death_ind = india_death()
    dindJSON = json.dumps(death_ind, cls=plotly.utils.PlotlyJSONEncoder)

    # Display Recovered cases of India:
    recovery_ind = india_recovery()
    rindJSON = json.dumps(recovery_ind, cls=plotly.utils.PlotlyJSONEncoder)

    # Display Recovered cases of India:
    conf_ind_expo = india_conf_exponential()
    cindexpJSON = json.dumps(conf_ind_expo, cls=plotly.utils.PlotlyJSONEncoder)

    

    # Display global counts:
    world_conf = load_global_conf_data().iloc[:,-1].sum()
    world_death = load_global_death_data().iloc[:,-1].sum()
    world_recovered = load_global_recover_data().iloc[:,-1].sum()
    world_days = (date.today() - date(2019, 12, 31)).days

    wc24h = load_global_conf_data().iloc[:,-1].sum() - load_global_conf_data().iloc[:,-2].sum()
    wd24h = load_global_death_data().iloc[:,-1].sum() - load_global_death_data().iloc[:,-2].sum()
    wr24h = load_global_recover_data().iloc[:,-1].sum() - load_global_recover_data().iloc[:,-2].sum()
    
    # Get district wise list of cases:
    dist_link = get_district_link()

    # Get last updated time of data:
    last_update = get_last_updated_time()

    return render_template('index.html', a=wmJSON, world_table=world_table, india_table=india_table, c20lplot=c20JSON, 
    d20lplot=d20JSON, r20lplot=r20JSON, cindlplot=cindJSON, dindlplot=dindJSON, rindlplot=rindJSON, cindexpplot=cindexpJSON,
    wconf=world_conf, wdeath=world_death, wrecoverd=world_recovered, wdays=world_days, wc24h=wc24h, wd24h=wd24h, wr24h=wr24h,
    dist_link=dist_link, last_update = last_update)


# Display India's Map
@app.route('/map')
def map():
    #return send_file(url_for('templates', filename = 'India.html'))
    #return india_map()[0].get_root().render()
    return india_map()[0]._repr_html_()
