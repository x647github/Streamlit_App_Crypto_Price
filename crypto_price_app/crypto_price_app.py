import streamlit as st
from PIL import Image
import pandas as pd
import numpy as np
import base64
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests
import json

# Page layout
## Page expands to full width
st.set_page_config(layout='wide')

## Insert logo
#image = Image.open('logo.jpg')
#st.image(image, width=500)


# Title
st.title('Crypto Price App')
st.markdown('This app retrieves cryptocurrency prices for the top 100 cryptocurrency from the **CoinMarketCap**!')


# About
expander_bar = st.expander("About")
expander_bar.markdown(''' 
* **Python libraries:** base64, pandas, streamlit, matplotlib, BeautifulSoup, requests, json
* **Data source:** [CoinMarketCap](http://coinmarketcap.com).
* **Credit:** [EDA Cryptocurrency](https://www.youtube.com/redirect?event=video_description&redir_token=QUFFLUhqbkc2d2xFNHFnZ2NPRFctbWFBMHdBWUlqUFE3Z3xBQ3Jtc0tsSFd5SmQyclFlNmlZN3NLSUZtU2Y2T2hlRERqSEtMZTJkMzRyNTRPWGtvS0x1SGhScUI3cWRjLUp1ZWF6MjRwa3lkQUo0MktibllUZHRQaXpfbEQ1eWFYYThPcnpWUzdJQzVhaHNoRXAyTXp1RGlNYw&q=https%3A%2F%2Fgithub.com%2Fdataprofessor%2Fstreamlit_freecodecamp%2Ftree%2Fmain%2Fapp_6_eda_cryptocurrency&v=JwSS70SZdyM).                      
''')


# Page layout (continued)
## Divide page to 3 columns
col1 = st.sidebar
col2, col3 = st.columns((2, 1))

col1.header('Filter')

## Sidebar - currency price unit
currency_price_unit = col1.selectbox('Select currency for price', ['USD'])

# Web scraping of CoinMarketCap data
@st.cache_data
def load_data():
    cmc = requests.get('http://coinmarketcap.com')
    soup = BeautifulSoup(cmc.content, 'html.parser')
    
    data = soup.find('script', id='__NEXT_DATA__', type='application/json')
    data = json.loads(data.contents[0])
    coin_data = json.loads(data['props']['initialState'])
    listings = coin_data['cryptocurrency']['listingLatest']['data']
    
    df = pd.DataFrame(listings[1:], columns=listings[0]['keysArr']+['unknown'])
    
    cols = ['slug', 'symbol', 'cmcRank', 'quote.USD.price', 
            'quote.USD.percentChange1h', 
            'quote.USD.percentChange24h', 
            'quote.USD.percentChange7d', 
            'quote.USD.marketCap', 'quote.USD.volume24h']
    
    df = df[cols].drop('cmcRank', axis=1) # .sort_values('cmcRank', ascending=True)
    
    new_cols = {'slug':'coin_name', 'symbol': 'coin_symbol', 'quote.USD.price': 'price', 'quote.USD.percentChange1h': 'percent_change_1h',
                'quote.USD.percentChange24h': 'percent_change_24h', 'quote.USD.percentChange7d': 'percent_change_7d', 
                'quote.USD.marketCap': 'market_cap', 'quote.USD.volume24h': 'volume_24h'}
    
    df = df.rename(columns=new_cols)
    df.index = np.arange(1, len(df) + 1)
    return df

df = load_data()

## Sidebar - Cryptocurrency selections
coins = df['coin_symbol']
selected_coin = col1.multiselect('Cryptocurrency', coins, coins)

df_selected_coin = df[df['coin_symbol'].isin(selected_coin)]

## Sidebar - number of coins to display
num_coin = col1.slider('Display Top N Coins', 1, 100, 100)
df_coins = df_selected_coin[:num_coin]

## Sidebar - percent change timeframe
percent_timeframe = col1.selectbox('Percent change time frame', ['7d', '24h', '1h'])

## Sidebar - sorting values
sort_values = col1.selectbox('Sort values?', ['Yes', 'No'])


col2.subheader('Price of Selected Cryptocurrency')
col2.write('Data Dimension: ' + str(df_selected_coin.shape[0]) + ' rows and ' + str(df_selected_coin.shape[1]) + ' columns')

col2.dataframe(df_coins)

# Download CSV data
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="crypto.csv">Download CSV File</a>'
    return href

col2.markdown(filedownload(df_selected_coin), unsafe_allow_html=True)


col3.subheader('Bar plot of % Price Change')

def bar_plot(percent_timeframe, sort_values):
    percent_dict = {'7d': 'percent_change_7d', '24h': 'percent_change_24h', '1h': 'percent_change_1h'}
    selected_percent_timeframe = percent_dict[percent_timeframe]
    
    df_change = df_coins[['coin_symbol', 'percent_change_1h', 'percent_change_24h', 'percent_change_7d']]
    df_change = df_change.set_index('coin_symbol')
    
    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=[selected_percent_timeframe])
    
    if percent_timeframe == '7d':
        title_name = '*7 days period*'
    if percent_timeframe == '24h':
        title_name = '*24 hour period*'
    if percent_timeframe == '1h':
        title_name = '*1 hour period*'
    col3.write(title_name)
    
    plt.figure(figsize=(5,25))
    plt.subplots_adjust(top=1, bottom=0)
    
    df_change['positive_change'] = df_change[selected_percent_timeframe] > 0
    df_change[selected_percent_timeframe].plot(kind='barh', color=df_change['positive_change'].map({True: 'g', False: 'r'}))
    col3.pyplot(plt)

bar_plot(percent_timeframe, sort_values)
