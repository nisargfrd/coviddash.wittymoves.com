#!/usr/bin/env python
# coding: utf-8

# # Web Scrapper and data formatter file

# In[1]:


# Importing Libraries:
import urllib.request
import pandas as pd

import plotly.offline as pyo
import plotly.graph_objects as go

import math
import numpy as np

# To set working Directorty:
import os
import time

# For scrapping data from MOHFW and Wikipedia:
from bs4 import BeautifulSoup
import requests

# To set Lat, Long and for Folium:
from geopy.geocoders import Nominatim

# To merge geojson data and cases data:
import geopandas as gpd

# To create custom maps:
import folium


# ## Set Working Directory:

# In[2]:

#my_path='/home/ubuntu/CovidApp/COVID_19_Flask/'
my_path='/run/media/nisarg/Drive2/AWS - Nisarg Covid Instance/Elastic_IP/CovidApp/COVID_19_Flask'
os.chdir(my_path)


# ## Fetching data and saving them into excel file for future reference:

# In[3]:


# Confirmed cases data stored in df:

#url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv'
# Data source URL updated:
url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
df = pd.read_csv(url)


# In[4]:


# Death cases data stored in df1:

#url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Deaths.csv'
# Data source URL updated:
url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
df1 = pd.read_csv(url)


# In[5]:


# Recovered cases data stored in df2:

# url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Recovered.csv'
# Data source URL updated:

url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv'
df2 = pd.read_csv(url)


# In[6]:


# Store data in csv files:

df.to_csv('input/covid-Confirmed.csv', index=False)
df1.to_csv('input/covid-Death.csv', index=False)
df2.to_csv('input/covid-Recovered.csv', index=False)
del df, df1, df2


# In[7]:


# Load data from CSV files:

df_conf = pd.read_csv('input/covid-Confirmed.csv')
df_death = pd.read_csv('input/covid-Death.csv')
df_recovered = pd.read_csv('input/covid-Recovered.csv')


# ## Scrapping Data from Wikipedia for Global data:

# In[8]:


'''
The data is from CSSE at Johns Hopkins University. But for recovered cases, it's no more reliable.
Hence, we'll use data from wikipedia.
'''

#response = requests.get('https://en.wikipedia.org/wiki/2019%E2%80%9320_coronavirus_pandemic#covid19-container')
response = requests.get('https://en.wikipedia.org/wiki/2019%E2%80%9320_coronavirus_pandemic_by_country_and_territory#covid19-container')

# In[9]:


soup = BeautifulSoup(response.content, "html.parser")


# In[10]:


tb = soup.find_all("div", {"id":"covid19-container"})
               #"content newtab")

t_rows=tb[0].find('table').find_all('tr')
    
res = []
wiki_country = []

for tr in t_rows[2:]:            # To remove Headers and get the country's list
    td = tr.find_all('th')
    '''
    # Old code for reference:
    wiki_country = [tr.find('a').get_text() for tr in td if tr.find('a') is not None]
    if wiki_c:
        wiki_country.append(wiki_c)
    '''

    def no_links(tr):
        #print(type(node))
        try:
            # Will return -1 one for all tags with <a> as children and raise exception for none <a> children tag:
            #list(tr.children)[1].find('a')
            list(tr.children)[1].find('a')
            #    wiki_country.append(tr.get_text())
        except:
            a=(list(tr.children)[0])
            a=a.strip()
            print(a)
            wiki_country.append(a)


    [wiki_country.append(tr.find('a').get_text()) if tr.find('a') is not None and tr.find('a').get_text() != '' else no_links(tr)
    for tr in td]

# To remove Headers:
# wiki_country=wiki_country[2:]

for tr in t_rows:
    td = tr.find_all('td')
    row = [tr.text.strip() for tr in td if tr.text.strip()]
    if row:
        res.append(row)


# Save all rows in DF_WIKI:
df_wiki = pd.DataFrame(columns=["Confirmed_Cases","Deaths","Recovered","Ref"])
df_wiki=df_wiki.append(pd.DataFrame(res, columns=df_wiki.columns))

# To remove extra lines and Ref column from table:
df_wiki.drop(df_wiki.tail(2).index,inplace=True)
df_wiki.drop('Ref', axis=1, inplace=True)

print(len(wiki_country))
print(wiki_country)
#wiki_country.remove("")
print(len(wiki_country))
[print(i) for i in wiki_country]

print(df_wiki)
#print(df_wiki..map(tuple).isin([(1,2)]))
# Add Location data in df:
df_wiki['Locations'] = (wiki_country)

# Save df data in csv:
df_wiki.to_csv('input/covid-wiki-data.csv', index=False)

del wiki_country, res, tb, t_rows,response, soup

df_wiki.head()


# ## Check Data Summary:

# In[11]:


df_conf.describe()


# In[12]:


df_conf.head()


# In[13]:


df_death.describe()


# In[14]:


df_death.head()


# In[15]:


df_recovered.describe()


# In[16]:


df_recovered.head()


# ## Data Cleaning for John Hopkins Data:

# In[17]:


# Check for type of data:
print("Confirmed Cases:")
print(df_conf.dtypes)
print("\nDeath Cases:")
print(df_death.dtypes)
print("\nRecovered Cases:")
print(df_recovered.dtypes)


# In[18]:


def df_preproc(df=df_conf, name="Confirmed"):
    
    # Check and replace NA values:
    print("NA values in",name,"Cases:", [print("Column",x,"has -", df[x].isna().sum(),"NA values.") for x in df.drop(["Province/State","Country/Region","Lat","Long"], axis=1).columns if df[x].isna().sum()>0])
    [df[x].fillna(value=0, inplace=True) for x in df.drop(["Province/State","Country/Region","Lat","Long"], axis=1).columns if df[x].isna().sum()>0]
    print("NA values Filled with 0 in",name,"Cases.")
    
    # Change Country to china, and update provinces for easy interpretation:
    for key, df_ in df.items():
        df[key]=df[key].replace({'Country/Region':'Mainland China'}, 'China')
        df[key]=df[key].replace({'Province/State':'Queensland'}, 'Brisbane')
        df[key]=df[key].replace({'Province/State':'New South Wales'}, 'Sydney')
        df[key]=df[key].replace({'Province/State':'Victoria'}, 'Melbourne')
        df[key]=df[key].replace({'Province/State':'South Australia'}, 'Adelaide')
    
    # Update Province / State name for easy plotting in map:
    df['Province/State'] = df['Province/State'].apply(lambda x: (x+", ") if not pd.isna(x) else np.nan)

    print("Data Cleaning is now completed.")
    
    return df


# In[19]:


# Data Cleaning and Pre-Processing of dataframes:

df_conf=df_preproc(df_conf,"Confirmed")
df_death=df_preproc(df_death,"Death")
df_recovered=df_preproc(df_recovered,"Recovered")


# In[20]:


df_conf


# In[21]:


df_conf[df_conf["Country/Region"]=='India']


# In[22]:


# Store data in csv files:

df_conf.to_csv('output/covid-Confirmed.csv', index=False)
df_death.to_csv('output/covid-Death.csv', index=False)
df_recovered.to_csv('output/covid-Recovered.csv', index=False)


# In[23]:


# Group By Data:
gdf_c=df_conf.groupby('Country/Region')[df_conf.columns[4:]].sum().reset_index()

gdf_r=df_recovered.groupby('Country/Region')[df_recovered.columns[4:]].sum().reset_index()

gdf_d=df_death.groupby('Country/Region')[df_death.columns[4:]].sum().reset_index()


# In[24]:


# Store data in csv files:

gdf_c.to_csv('output/group-covid-Confirmed.csv', index=False)
gdf_d.to_csv('output/group-covid-Death.csv', index=False)
gdf_r.to_csv('output/group-covid-Recovered.csv', index=False)


# ## Pre-Processing Wiki Data:

# In[25]:


# Pre-Processing Wiki Data:

# To set Lat and Long of Countries:
df_wiki['Lat'] = np.nan
df_wiki['Long'] = np.nan

geolocator = Nominatim(user_agent="My App",timeout=100)
#geolocator = RateLimiter(geolocator.geocode, min_delay_seconds=1)

'''

[df_wiki['Lat'][i]:=geolocator.geocode(df_wiki['Locations'][i]).latitude,
 df_wiki['Long'][i]:=geolocator.geocode(df_wiki['Locations'][i]).longitude
 if df_wiki['Locations'][i]!='China (mainland)'
 else
 df_wiki['Lat'][i]:=geolocator.geocode("Beijing, China").latitude,
 df_wiki['Long'][i]:=geolocator.geocode("Beijing, China").longitude
 for i in df_wiki.index]

'''



for i in df_wiki.index:
    # To replace China (mainland) with Beijing, China, for better geo location:
    if df_wiki['Locations'][i]=='China (mainland)':
        location = geolocator.geocode("Beijing, China")
        time.sleep(2)
        #print(location.latitude, location.longitude)
        df_wiki['Lat'][i]=location.latitude
        time.sleep(2)
        df_wiki['Long'][i]=location.longitude
        time.sleep(2)

    elif df_wiki['Locations'][i]=="Donetsk People's Republic":
        #location = geolocator.geocode("Donetsk")
        #print(location.latitude, location.longitude)
        df_wiki['Lat'][i]=48.002778
        df_wiki['Long'][i]=37.805278
    
    elif df_wiki['Locations'][i]=="MS Zaandam & Rotterdam":
        #location = geolocator.geocode("Donetsk")
        #print(location.latitude, location.longitude)
        df_wiki['Lat'][i]=25.96947
        df_wiki['Long'][i]=-79.83765

    elif df_wiki['Locations'][i]=="Luhansk People's Republic":
        df_wiki['Lat'][i]=48.566667
        df_wiki['Long'][i]=39.333333

    elif df_wiki['Locations'][i]=="Republic of Crimea":
        df_wiki['Lat'][i]=44.951944
        df_wiki['Long'][i]=34.102222

    elif df_wiki['Locations'][i]=="Diamond Princess":
        df_wiki['Lat'][i]=35.41458
        df_wiki['Long'][i]=139.68205
    
    elif df_wiki['Locations'][i]=='USS Theodore Roosevelt':
        location = geolocator.geocode("Apra Harbor, Guam")
        time.sleep(2)
        df_wiki['Lat'][i]=location.latitude
        time.sleep(2)
        df_wiki['Long'][i]=location.longitude
        time.sleep(2)

    elif df_wiki['Locations'][i]=='Coral Princess':
        #location = geolocator.geocode("Port of Miami")
        df_wiki['Lat'][i]=25.774167
        df_wiki['Long'][i]=-80.171111

    elif df_wiki['Locations'][i]=='Sint Maarten':
        #location = geolocator.geocode("Philipsburg")
        #time.sleep(2)
        df_wiki['Lat'][i]=18.033333
        #time.sleep(2)
        df_wiki['Long'][i]=-63.05
        #time.sleep(2)

    elif df_wiki['Locations'][i]=='Saint Martin':
        #location = geolocator.geocode("Marigot")
        #time.sleep(2)
        df_wiki['Lat'][i]=18.0731
        #time.sleep(2)
        df_wiki['Long'][i]=-63.0822
        #time.sleep(2)

    elif df_wiki['Locations'][i]=='Dominica':
        #location = geolocator.geocode("Roseau")
        df_wiki['Lat'][i]=15.301389
        time.sleep(2)
        df_wiki['Long'][i]=-61.388333
        time.sleep(2)

    elif df_wiki['Locations'][i]=='Dominican Republic':
        #location = geolocator.geocode("")
        df_wiki['Lat'][i]=19
        time.sleep(2)
        df_wiki['Long'][i]=-70.666667
        time.sleep(2)

    elif df_wiki['Locations'][i]=='Akrotiri and Dhekelia':
        location = geolocator.geocode("Episkopi Cantonment")
        time.sleep(2)
        df_wiki['Lat'][i]=location.latitude
        time.sleep(2)
        df_wiki['Long'][i]=location.latitude
        time.sleep(2)

    elif df_wiki['Locations'][i]=='Greg Mortimer':
        df_wiki['Lat'][i]=-34.904592
        time.sleep(2)
        df_wiki['Long'][i]=-56.214962
        time.sleep(2)

    elif df_wiki['Locations'][i]=='Azerbaijan':
        df_wiki['Lat'][i]=40.395278
        time.sleep(2)
        df_wiki['Long'][i]=49.882222
        time.sleep(2)

    elif df_wiki['Locations'][i]=='Artsakh':
        df_wiki['Lat'][i]=39.815278
        time.sleep(2)
        df_wiki['Long'][i]=46.751944
        time.sleep(2)

    else:
        print(df_wiki['Locations'][i])
        time.sleep(2)
        location = geolocator.geocode(str(df_wiki['Locations'][i]))
        time.sleep(2)
        #print(location.latitude, location.longitude)
        #print(df_wiki['Locations'][i])
        df_wiki['Lat'][i]=location.latitude
        time.sleep(2)
        df_wiki['Long'][i]=location.longitude
        time.sleep(2)
    
    print('done')



# To remove coma from the data:
df_wiki["Confirmed_Cases"] = df_wiki["Confirmed_Cases"].str.replace(",","")
df_wiki["Deaths"] = df_wiki["Deaths"].str.replace(",","")
print("Before: ",df_wiki["Recovered"])
df_wiki["Recovered"] = df_wiki["Recovered"].str.replace(",","").replace(".","")
print("After: ",df_wiki["Recovered"])

# To replace "-" with NA:
df_wiki["Recovered"] = df_wiki["Recovered"].replace("–",np.nan)

# Convert float data of recovered column to int:
#df_wiki['Recovered'] = df_wiki['Recovered'].fillna(0.0).astype(float).astype(int)
df_wiki['Recovered'] = df_wiki['Recovered'].fillna(0.0).astype(float).astype(int)

# Save df data in csv:
df_wiki.to_csv('output/covid-wiki-data.csv', index=False)


# ## Scrapping for India Specific Data:

# In[26]:


response = requests.get('https://www.mohfw.gov.in/index.html')


# In[27]:


soup = BeautifulSoup(response.content, "html.parser")


# In[28]:

'''
tb = soup.find_all("div", {"class":"content newtab"})
               #"content newtab")

t_rows=tb[0].find('div').find('table').find_all('tr')
'''

tb = soup.find_all("div", {"class":"data-table"})

t_rows=tb[0].find('table').find_all('tr')

res = []
for tr in t_rows:
    td = tr.find_all('td')
    row = [tr.text.strip() for tr in td if tr.text.strip()]
    if row:
        res.append(row)


df_india = pd.DataFrame(res, columns=["Sr.No.","State/UT","Total Confirmed cases (including Foreign National)","Cured/Discharged/Migrated","Death"])
df_india


# ## Preprocessing of India Specific Data:

# In[29]:


# df_india preprocessing:

# Remove Last row which contains total of all columns:
df_india.drop(df_india.tail(2).index, inplace=True)

# Drop column of Sr.No., as it's of no use to us:
df_india.drop(["Sr.No."], axis=1, inplace=True)

# Convert the type of columns from object to string and int:
convert_dict = {'State/UT': str, 
                'Total Confirmed cases (including Foreign National)': int,
                'Cured/Discharged/Migrated': int,
                'Death': int
               }
# Also replace "-" with 0, as NA is still a zero for us in recovered cases:
df_india = df_india.fillna(0).astype(convert_dict)

df_india['State/UT'] = df_india['State/UT'].replace("Telengana", "Telangana") 

# To insert remaining states with 0 cases:
st=['Jammu and Kashmir',
    'West Bengal',
    'Uttarakhand',
    'Uttar Pradesh',
    'Tripura',
    'Tamil Nadu',
    'Telangana',
    'Sikkim',
    'Rajasthan',
    'Puducherry',
    'Punjab',
    'Odisha',
    'Nagaland',
    'Mizoram',
    'Madhya Pradesh',
    'Manipur',
    'Meghalaya',
    'Maharashtra',
    'Lakshadweep',
    'Kerala',
    'Karnataka',
    'Ladakh',
    'Jharkhand',
    'Haryana',
    'Himachal Pradesh',
    'Gujarat',
    'Goa',
    'Dadra and Nagar Haveli',
    'Delhi',
    'Daman and Diu',
    'Chhattisgarh',
    'Chandigarh',
    'Bihar',
    'Assam',
    'Arunachal Pradesh',
    'Andhra Pradesh',
    'Andaman and Nicobar Islands']

rst = list(set(st)-set(df_india['State/UT'].values))

for i in rst:
    df_india=df_india.append({'State/UT':i,'Total Confirmed cases (including Foreign National)':0,
                    'Cured/Discharged/Migrated':0,
                    'Death':0},ignore_index=True,sort=False)

del st, rst, convert_dict

# To add cases data in geojson data for hover details in map:
gps=gpd.read_file("input/map_India.geojson")

gps=gps.merge(df_india[['State/UT','Total Confirmed cases (including Foreign National)',
'Cured/Discharged/Migrated','Death']],
              left_on="NAME", right_on="State/UT")


# In[30]:


# Updated df_india:

print(df_india)


# In[31]:


# Save files locally:

df_india.to_csv('output/India_confirmed_cases.csv', index=False)

gps.to_file('output/Updated_Geojson_data.geojson', driver="GeoJSON")

gps.to_csv('output/Updated_Geojson_data_csv.csv', index=False)

with open('output/Updated_Geojson_data.json', 'w') as f:
        f.write(gps.to_json())


# In[ ]:
print('Data Scrapping is now completed!')



