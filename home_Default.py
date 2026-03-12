import gspread
from google.oauth2.service_account import Credentials
import requests
import pandas as pd
from bs4 import BeautifulSoup
import math
import plotly.graph_objects as go
import streamlit as st
import pickle

# @st.cache_data
# def connect_ggsheet():
#     print("Reconnect GG sheet")
#     SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

#     # Đường dẫn tới file JSON credentials
#     CREDS_FILE = 'valuation-430503-780d52190443.json'

#     # Kết nối với Google Sheets
#     creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
#     client = gspread.authorize(creds)

#     # Lấy dữ liệu từ Google Sheets
#     spreadsheet_id = '1_BTPaJtdmQSYeEYfneG34ldm5QXDi5rxP2ttt-UAnL4'
#     sheet = client.open_by_key(spreadsheet_id)
#     worksheet = sheet.worksheet('RSI VNINDEX')
#     dt_rsi = worksheet.get_all_values() 
#     df_rsi = pd.DataFrame(dt_rsi)
#     valu = float(df_rsi.iloc[2,0])
#     url = f'https://finviz.com/quote.ashx?t={'SPY'}'
#     # Define headers to mimic a browser request
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#     }
#     response = requests.get(url, headers=headers)
#     if response.status_code == 200:
#         # Parse the page content
#         soup = BeautifulSoup(response.text, 'html.parser')

#         # Extract the relevant data
#         data = {}
#         for row in soup.find_all('tr', class_='table-dark-row'):
#             columns = row.find_all('td')
#             if len(columns) >= 2:
#                 key = columns[8].text.strip()
#                 value = columns[9].text.strip()
#                 data[key] = value

#         # Convert the data into a pandas DataFrame
#         dfe = pd.DataFrame(list(data.items()), columns=['Metric', 'Value'])
#     value2 = float(dfe.iloc[7]['Value'])
#     r = requests.get('https://api.alternative.me/fng/?limit=0')
#     cryp = pd.DataFrame(r.json()['data'])
#     valu3 = float(cryp.iloc[0,0])

#     with open("./valuesGGS.pkl", "wb") as f:
#         pickle.dump(
#             {
#                 "valu": valu,
#                 "value2": value2,
#                 "valu3": valu3,
#             },f
#         )

#     return valu, value2, valu3

@st.cache_data
def load_ggSheet():
    print("LOAD PICKLE FILE")
    with open("./valuesGGS.pkl", "rb") as f:
        data = pickle.load(f)
    valu = data.get("valu")
    value2 = data.get("value2")
    valu3 = data.get("valu3")
    return valu, value2, valu3

def show_default(st):
    st.markdown(
    """
    <h1 style='text-align: left;font-size: 30px'>WELCOME TO OUR WEBSITE</h1>
    """,
    unsafe_allow_html=True)

    # valu, value2, valu3 = connect_ggsheet()
    valu, value2, valu3 = load_ggSheet()

    def create_gauge(va, needle_length=0.25, needle_base_width=0.008):
        angle = 180 - (va / 100) * 180
        # Calculate the (x, y) position for the tip of the needle
        center_x = 0.55
        center_y = 0.52  # Adjusted for the gauge's actual center position

        x_tip = center_x + needle_length * math.cos(math.radians(angle))
        y_tip = center_y + needle_length * math.sin(math.radians(angle))

        # Calculate the (x, y) positions for the base of the needle
        base_angle_1 = angle + 90
        base_angle_2 = angle - 90
        x_base_left = center_x + needle_base_width * math.cos(math.radians(base_angle_1))
        y_base_left = center_y + needle_base_width * math.sin(math.radians(base_angle_1))
        x_base_right = center_x + needle_base_width * math.cos(math.radians(base_angle_2))
        y_base_right = center_y + needle_base_width * math.sin(math.radians(base_angle_2))


        # Gauge chart using Plotly
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=va,
            gauge={
                'axis': {
                    'range': [0, 100],
                    'tickvals': [0, 25, 50, 75, 100],  # Custom tick values
                    'ticktext': ['0', '25', '50', '75', '100'],  # Custom tick labels
                    'tickcolor': 'black'  # Color of tick labels
                },
                'shape': 'angular',
                'bar': {'color': 'rgba(0,0,0,0)'},  # Set bar color to transparent
                'steps': [
                    {'range': [0, 25], 'color': "red"},  # Keep original color ranges
                    {'range': [25, 50], 'color': "orange"},
                    {'range': [50, 75], 'color': "yellow"},
                    {'range': [75, 100], 'color': "green"}
                ],
                'bgcolor': 'rgba(0,0,0,0)',  # Make the background transparent
                'bordercolor': 'rgba(0,0,0,0)'  # Make the border transparent
            },
            number={'font': {'size': 20}},  # Adjust the font size as needed
            domain={'x': [0.2, 0.9], 'y': [0.2, 1]}  # Adjust the size and position of the gauge
        ))

        # Add the needle shape with rounded base and sharp tip
        fig.add_shape(
            type="path",
            path=f'M {x_base_left} {y_base_left} L {x_base_right} {y_base_right} L {x_tip} {y_tip} Z',
            fillcolor="black",
            line=dict(color="black")
        )

        return fig
    st.markdown(
        """
        <h1 style='text-align: center;font-size: 24px'>FEAR & GREED INDEX</h1>
        """,
        unsafe_allow_html=True)
    ct1, ct2, ct3 = st.columns(3)
    with ct1:
        st.markdown(
            """
            <h1 style='text-align: center;font-size: 24px'>VNINDEX</h1>
            """,
            unsafe_allow_html=True)
        fig1 = create_gauge(valu)
        st.plotly_chart(fig1)
    with ct2:
        st.markdown(
            """
            <h1 style='text-align: center;font-size: 24px'>S&P500</h1>
            """,
            unsafe_allow_html=True)
        fig2 = create_gauge(value2)
        st.plotly_chart(fig2)
    with ct3:
        st.markdown(
            """
            <h1 style='text-align: center;font-size: 24px'>CRYPTO</h1>
            """,
            unsafe_allow_html=True)
        fig3 = create_gauge(valu3)
        st.plotly_chart(fig3)