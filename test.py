
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google.oauth2 import service_account
from streamlit_navigation_bar import st_navbar
import gspread
from google.oauth2.service_account import Credentials
import math
from datetime import datetime
from datetime import timedelta
import requests
import os
from google import genai
from google.genai import types
import numpy as np
from pathlib import Path
import json

#import fix lib - DangBH
from requests.exceptions import HTTPError
import home_Default
import crawl_mck
from theme_config import pages, styles, marquee_html
import connect_ggsheet
from check_keys import ensure_key
from test_chatGPT import ask_chatGPT
from test_chatGPT import chatBot_answer
import checkTypeData



st.set_page_config(layout="wide")

# Hiển thị thanh navbar và lấy trang được chọn
page = st_navbar(pages, styles=styles)

st.markdown(marquee_html, unsafe_allow_html=True)
# Hiển thị nội dung tương ứng với trang được chọn

#load Data - DangBH
# VN_Financial_Data = pd.read_excel("./data/VN100_financial_data.xlsx")

#comp_name,ticker,short_name,sector
# VN_Financial_Info = pd.read_csv("./data/vn100_full_list.csv")
VN_Financial_Info = pd.read_csv("./data/vn_yf_ticker.csv")
EN_Financial_Info = pd.read_csv("./data/SP500_list.csv")

DB_DIR = Path("./database")

required_files = ["mck_info.json", "bsheet.parquet", "cfs.parquet", "data.parquet", "fast_info.json", "income.parquet", "quarter_bsheet.parquet", "quarter_cfs.parquet",
                  "quater_income.parquet", "save_selenium.json"]


if page == "Home":

    placeholder = st.empty()

    print("RELOAD HOME PAGE")
    VN_stock_list = VN_Financial_Info['Ticker'].unique()
    EN_stock_list = EN_Financial_Info['ticker'].unique()
    ticker = None
    tick_col, op_tick_col, tcol1, tcol2, tcol3 = st.columns(5)
    with tick_col:
        tick = st.selectbox("World Ticker", EN_stock_list, index=None, placeholder="Choose here")
    with op_tick_col:
        option_tick = st.selectbox("Vietnamese Ticker", VN_stock_list, index=None, placeholder="Choose here")

    if not tick and not option_tick:
        home_Default.show_default(st)
    
    elif tick and not option_tick:
        ticker = tick
    elif not tick and option_tick:
        ticker = option_tick
    elif tick and option_tick:
        ticker = None  # Reset ticker to None if both tick and option_tick have values
        st.subheader('Select only one Ticker')
    
    if ticker is not None:
        headers = crawl_mck.headers
        
        ticker = ticker.upper()

        @st.cache_resource
        def call_mck(ticker):
            return yf.Ticker(ticker)
        
        ticker_dir = DB_DIR / ticker

        try:
            if ticker_dir.exists() and ticker_dir.is_dir() and (ticker_dir / required_files[0]).exists():
                # ====== CÓ DATA LOCAL ======
                print(f"[LOCAL] Found data for {ticker}")
                mck_info_data = checkTypeData.load_mck_info(ticker)
                mck_info = mck_info_data["mck_info"]
            else:
                # ====== CHƯA CÓ DATA ======
                print(f"[CRAWL] No data for {ticker}, crawling...")
                mck = call_mck(ticker)
                mck_info = mck.info
            print(mck_info)

            beta_value = mck_info['beta'] if 'beta' in mck_info else 0
            company_name =  mck_info['longName']
            st.title(company_name)
        except Exception as e:
            if "HTTP Error 404" in str(e):
                st.error(f"Ticker '{ticker}' không tồn tại! Vui lòng nhập lại")
                st.stop()
            else:
                st.error(f"Ticker '{ticker}' không đầy đủ dữ liệu! Vui lòng nhập lại")
                st.stop()
                

        summary, estimation, valuation, guru = st.tabs(
                ["Summary", 'Discount Rate', "Valuation", "Financial Analysis"])

        with summary:
            print("Run Summary")
            if ticker[-3:] != '.VN':
                st1, st2 = st.columns(2)
                with st1:
                    st.subheader('Candlestick Chart')
                    current = datetime.today().date()
                    start_date = st.date_input('Start Date', current - timedelta(days=365))
                    end_date = st.date_input('End Date', current)
                with st2:
                    url = f'https://finviz.com/quote.ashx?t={ticker}'
                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        # Parse the page content
                        soup = BeautifulSoup(response.text, 'html.parser')
                        content_div = soup.find("div", class_="content")
                        content_text = content_div.get_text(strip=True)

                        if "not found" in content_text:
                            st.error("Không có đủ dữ liệu cho ticker này.")
                            st.stop()
                        else:
                            # Extract the relevant data
                            data = {}
                            for row in soup.find_all('tr', class_='table-dark-row'):
                                columns = row.find_all('td')
                                # print(columns)
                                if len(columns) >= 2:
                                    key = columns[8].text.strip()
                                    value = columns[9].text.strip()
                                    data[key] = value

                            # Convert the data into a pandas DataFrame
                            dfe = pd.DataFrame(list(data.items()), columns=['Metric', 'Value'])
                            print(dfe)
                    else:
                        st.error("Finviz không cung cấp đủ dữ liệu.")
                        st.stop()
                    value2 = float(dfe.loc[dfe["Metric"] == "RSI (14)", "Value"].values[0])

                    angle = 180 - (value2 / 100) * 180
                    # angle = 180 * (1 - value2/100)
                    needle_length = 0.25
                    needle_base_width = 0.008
                    # Calculate the (x, y) position for the tip of the needle
                    center_x = 0.5
                    center_y = 0.6  # Adjusted for the gauge's actual center position

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
                    figa = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=value2,
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
                        domain={'x': [0.2, 0.8], 'y': [0.2, 1]}  # Adjust the size and position of the gauge
                    ))

                    # Add the needle shape with rounded base and sharp tip
                    figa.add_shape(
                        type="path",
                        path=f'M {x_base_left} {y_base_left} L {x_base_right} {y_base_right} L {x_tip} {y_tip} Z',
                        fillcolor="black",
                        line=dict(color="black")
                    )
                    # Update layout to ensure proper coordinate system
                    figa.update_layout(
                        xaxis=dict(range=[0, 1], showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(range=[0, 1], showgrid=False, zeroline=False, showticklabels=False),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    st.markdown(
                        """
                        <h1 style='text-align: center;font-size: 24px'>RSI Index</h1>
                        """,
                        unsafe_allow_html=True)
                    st.plotly_chart(figa)
            else:
                st.subheader('Candlestick Chart')
                current = datetime.today().date()
                start_date = st.date_input('Start Date', current - timedelta(days=365))
                end_date = st.date_input('End Date', current)
            
            #PLOT
            @st.cache_data
            def download_data(ticker, start, end):
                data = yf.download(ticker, start, end)
                return data
            try:
                if ticker_dir.exists() and ticker_dir.is_dir() and (ticker_dir / required_files[3]).exists():
                    # ====== CÓ DATA LOCAL ======
                    print(f"[LOCAL] Found data for {ticker}")
                    dataa = pd.read_parquet(f"./database/{ticker}/data.parquet")
                else:
                    # ====== CHƯA CÓ DATA ======
                    print(f"[CRAWL] No data for {ticker}, crawling...")
                    dataa = download_data(ticker, start_date, end_date)
            except Exception as e:
                if "HTTP Error 404" in str(e):
                    st.error(f"Ticker '{ticker}' không tồn tại! Vui lòng nhập lại")
                    st.stop()
                else:
                    st.error(f"Ticker '{ticker}' không đầy đủ dữ liệu! Vui lòng nhập lại")
                    st.stop()
            # print(dataa['Open'], dataa['High'], dataa['Low'])
            
            # Các đường trung bình
            dataa['EMA20'] = dataa['Close'][ticker].ewm(span=20, adjust=False).mean()
            dataa['MA50'] = dataa['Close'][ticker].rolling(50).mean()
            dataa['MA100'] = dataa['Close'][ticker].rolling(100).mean()
            dataa['MA150'] = dataa['Close'][ticker].rolling(150).mean()
            
            if dataa.empty:
                st.write("<p style='color:red'><strong>Please reset the date to see the chart</strong></p>",
                            unsafe_allow_html=True)
            else:
                fig = go.Figure(data=[
                    go.Scatter(x=dataa.index, y=dataa['EMA20'], line=dict(color='green', width=1.5, dash='dot'),
                                name='EMA20'),
                    go.Scatter(x=dataa.index, y=dataa['MA50'], line=dict(color='blue', width=1.5), name='MA50'),
                    go.Scatter(x=dataa.index, y=dataa['MA100'], line=dict(color='yellow', width=1.5), name='MA100'),
                    go.Scatter(x=dataa.index, y=dataa['MA150'], line=dict(color='red', width=1.5), name='MA150'),
                    go.Candlestick(x=dataa.index, open=dataa['Open'][ticker], high=dataa['High'][ticker], low=dataa['Low'][ticker],
                                    close=dataa['Close'][ticker],
                                    name='Candle Stick')
                ])
            
                fig.update_layout(autosize=True, width=1100, height=750,
                                legend=dict(orientation="h", yanchor="top", y=1.08, xanchor="right", x=1))
                # fig.update_layout(autosize=True)

                st.plotly_chart(fig)
            # GEMINI - CHATGPT - DONE

            if "last_ticker" not in st.session_state or st.session_state.last_ticker != ticker:
                # reset dữ liệu cũ
                st.session_state.output_text = None
                st.session_state.output_text_2 = None
                st.session_state.output_text_3 = None

                # cập nhật ticker hiện tại làm "ticker cũ"
                st.session_state.last_ticker = ticker

            st.title("1. Giới thiệu tổng quan về công ty:")
            if st.button("▼", key="button1"):
                try:
                    # output_text = ask_chatGPT(f"Giới thiệu về cổ phiêu công ty {ticker}")
                    st.session_state.output_text = ask_chatGPT(f"giới thiệu tổng quan về cổ phiếu công ty {ticker}, ngắn gọn, xúc tích")
                    # st.write(output_text) 
                except Exception as e:    
                    st.session_state.output_text = 'Please reload the website'
            if "output_text" in st.session_state:
                st.write(st.session_state.output_text)
                st.session_state.output_text = None
            st.title("2. Phân tích lợi thế cạnh tranh bền vững")
            if st.button("▼", key="button2"):
                try:
                    st.session_state.output_text_2 = ask_chatGPT(f"Phân tích “moat” (lợi thế cạnh tranh bền vững) của cổ phiếu công ty {ticker} theo thang điểm 10, ngắn gọn, xúc tích")
                    # st.write(output_text_2) 
                except Exception as e:    
                    # st.write('Please reload the website')
                    st.session_state.output_text_2 = 'Please reload the website'
            if "output_text_2" in st.session_state:
                st.write(st.session_state.output_text_2)
            st.title("3. Cuộc gọi công bố kết quả kinh doanh gần đây, ngắn gọn, xúc tích")
            if st.button("▼", key="button3"):
                try:
                    # st.session_state.output_text_3 = ask_chatGPT(f"Phân tích MOAT của cổ phiếu công ty {ticker} với các yếu tố trên thang điểm 10, tính điểm tổng cho công ty đó.")
                    st.session_state.output_text_3 = ask_chatGPT(f"Tóm tắt hình hình kinh doanh gần nhất của {ticker}, ngắn gọn, xúc tích ")
                    # st.write(output_text_3) 
                except Exception as e:    
                    st.session_state.output_text_3 = 'Please reload the website'
            if "output_text_3" in st.session_state:
                st.write(st.session_state.output_text_3)
        # --------------------------------------------------------------------------      
        with estimation:
            print("Run Discount Rate")
            # beta
            connect_ggsheet.update_cell_data(ticker=ticker)
            beta = connect_ggsheet.download_sheet_data()
            cola, colb = st.columns(2)
            with cola: 
                st.subheader('Discount Rate for US Stocks')
                risk_free1 = st.number_input("Risk Free Rate (%)", value=float(2.19))
                market_risk1 = st.number_input("Average Market Risk Premium (%)", value=float(3.7))
                if ticker[-3:] != ".VN":
                    capm1 = risk_free1 + beta_value*market_risk1 if beta_value != 0 else risk_free1 + float(beta[2].iloc[6])*market_risk1
                    st.write('Discount Rate (CAPM): ' + str(round(capm1,3)) + '%')
                bt = [0.8, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6]
                dc_us = {
                    'BETA': ['Less than 0.8', '1', '1.1', '1.2', '1.3', '1.4', '1.5', 'More than 1.6'],
                    'DISCOUNT RATE': [round((risk_free1 + num*market_risk1),2) for num in bt]
                }
                st.data_editor(
                    dc_us,
                    hide_index=True,
                )
            with colb: 
                st.subheader('Discount Rate for VN Stocks')
                risk_free2 = st.number_input("Risk Free Rate (%)", value=float(4.0))
                market_risk2 = st.number_input("Average Market Risk Premium (%)", value=float(7.1))
                if ticker[-3:] == ".VN":
                    try:
                        capm2 = risk_free2 + beta_value*market_risk2 if beta_value != 0 else risk_free2 + float(dfe['Value'].iloc[6])*market_risk2
                        st.write('Discount Rate (CAPM): ' + str(round(capm2,3)) + '%')
                    except NameError:
                        st.error("Ticker này không đủ dữ liệu để tính toán Discount Rate, giá trị được gán mặc định 0")
                        capm2=0
                dc_vn = {
                    'BETA': ['Less than 0.8', '1', '1.1', '1.2', '1.3', '1.4', '1.5', 'More than 1.6'],
                    'DISCOUNT RATE': [round((risk_free2 + num*market_risk2),2) for num in bt]
                }
                st.data_editor(
                    dc_vn,
                    hide_index=True,
                )    
            if ticker[-3:] == '.VN':
                capm = capm2
            else: capm = capm1
        # --------------------------------------------------------------------------   
        with valuation:
            print("Run Valuation")
            try:
                if ticker_dir.exists() and ticker_dir.is_dir():
                    # ====== CÓ DATA LOCAL ======
                    
                    if (ticker_dir / required_files[5]).exists():
                        print(f"[LOCAL] Found data for {ticker}")
                        income = pd.read_parquet(f"./database/{ticker}/income.parquet")
                    else:
                        print(f"[CRAWL] No data for {ticker}, crawling...")
                        income = mck.income_stmt
                    if (ticker_dir / required_files[6]).exists():
                        quarter_bsheet = pd.read_parquet(f"./database/{ticker}/quarter_bsheet.parquet")
                    else:
                        print(f"[CRAWL] No data for {ticker}, crawling...")
                        quarter_bsheet = mck.quarterly_balance_sheet
                    if (ticker_dir / required_files[1]).exists(): 
                        bsheet = pd.read_parquet(f"./database/{ticker}/bsheet.parquet")
                    else:
                        bsheet = mck.balance_sheet
                    if (ticker_dir / required_files[0]).exists(): 
                        crprice = float(mck_info_data['crprice'])
                    else:
                        crprice = float(mck.history(period='1d')['Close'].iloc[0])
                    if (ticker_dir / required_files[7]).exists():  
                        quarter_cfs = pd.read_parquet(f"./database/{ticker}/quarter_cfs.parquet")
                    else:
                        quarter_cfs = mck.quarterly_cashflow
                    if (ticker_dir / required_files[8]).exists(): 
                        quarter_income = pd.read_parquet(f"./database/{ticker}/quater_income.parquet")
                    else:
                        quarter_income = mck.quarterly_income_stmt
                    if (ticker_dir / required_files[4]).exists(): 
                        fast_info = checkTypeData.load_fast_info(ticker)
                    else:
                        fast_info = mck.fast_info

                else:
                    # ====== CHƯA CÓ DATA ======
                    print(f"[CRAWL] No data for {ticker}, crawling...")
                    income = mck.income_stmt
                    quarter_bsheet = mck.quarterly_balance_sheet
                    bsheet = mck.balance_sheet
                    crprice = float(mck.history(period='1d')['Close'].iloc[0])
                    quarter_cfs = mck.quarterly_cashflow
                    quarter_income = mck.quarterly_income_stmt
                    fast_info = mck.fast_info
            except Exception as e:
                if "HTTP Error 404" in str(e):
                    st.error(f"Ticker '{ticker}' không tồn tại! Vui lòng nhập lại")
                    st.stop()
                else:
                    st.error(f"Ticker '{ticker}' không đầy đủ dữ liệu! Vui lòng nhập lại")
                    st.stop()
                    
            years_val = income.columns[-5:-1] # 4 cột cho 4 năm và 1 cột cho TTM

            

            # print(quarter_bsheet)
            if quarter_bsheet is None or quarter_bsheet.empty:
                # st.write("❌ quarter_bsheet bị rỗng, dừng xử lý.")
                placeholder.error("❌ quarter_bsheet bị rỗng, dừng xử lý các tác vụ tiếp theo.")
                st.stop()
            
            first_column_index = quarter_bsheet.columns[0]
            # print(first_column_index)
            TTM_bsheet = quarter_bsheet[first_column_index]
            # print(TTM_bsheet)
            second_column_index = quarter_bsheet.columns[1]
            # print(second_column_index)
            TTM_bsheet2 = quarter_bsheet[second_column_index]
            TTM_bsheet3 = quarter_bsheet.iloc[:, :4].sum(axis=1)
            five_column_index = quarter_bsheet.columns[len(years_val)]
            TTM_bsheet4 = quarter_bsheet[five_column_index]

            cr_price = "{:.2f}".format(crprice)

            col5, col6 = st.columns(2)
            with col5:
                # Current year
                current_year = datetime.now().year
                st.subheader("Current Year")
                number0 = st.number_input("Current Year:", value=current_year, placeholder="Type a number...")

                # debt
                st.subheader("Total Debt")
                if 'Current Debt' in TTM_bsheet.index:
                    cr_debt = TTM_bsheet['Current Debt']
                    cr_debt = 0 if pd.isna(cr_debt) else cr_debt 
                else:
                    cr_debt = 0 
                st.write('Current Debt: ', "{:,.2f}".format(cr_debt))

                if 'Long Term Debt' in TTM_bsheet.index:
                    lt_debt = TTM_bsheet['Long Term Debt']
                    lt_debt = 0 if pd.isna(lt_debt) else lt_debt 
                else:
                    lt_debt = 0 
                st.write('Long Term Debt: ', "{:,.2f}".format(lt_debt))

                ttm_cr = cr_debt + lt_debt
                formatted_ttm_cr = "{:,.2f}".format(ttm_cr)
                number5_str = st.text_input("Total Debt (Current Debt + Long Term Debt)", value=formatted_ttm_cr, placeholder="Type a number...")
                number5 = float(number5_str.replace(',', ''))

                # cash
                if 'Cash Cash Equivalents And Short Term Investments' in TTM_bsheet.index:
                    cash = TTM_bsheet.loc['Cash Cash Equivalents And Short Term Investments']
                    TTM_bsheet2['Cash Cash Equivalents And Short Term Investments'] = cash
                elif any("Cash Cash" in idx for idx in TTM_bsheet.index):
                    cash = TTM_bsheet.loc[[i for i in TTM_bsheet.index if "Cash Cash" in i]].iloc[0]
                    bsheet.loc['Cash Cash Equivalents And Short Term Investments'] = [1] * len(bsheet.columns)
                    TTM_bsheet['Cash Cash Equivalents And Short Term Investments'] = cash
                    TTM_bsheet2['Cash Cash Equivalents And Short Term Investments'] = cash
                else:
                    st.warning("Cash item not found in balance sheet, assigning value 0.")
                    cash = 0  # or some fallback value
                    bsheet.loc['Cash Cash Equivalents And Short Term Investments'] = [1] * len(bsheet.columns)
                    TTM_bsheet['Cash Cash Equivalents And Short Term Investments'] = 0
                    TTM_bsheet2['Cash Cash Equivalents And Short Term Investments']=0
                # cash = TTM_bsheet.loc['Cash Cash Equivalents And Short Term Investments']
                st.subheader("Cash and Short Term Investments:")
                formatted_cash = "{:,.2f}".format(cash)
                number6_str = st.text_input("Cash and Short Term Investments:", value=formatted_cash,
                                            placeholder="Type a number...")
                number6 = float(number6_str.replace(',', ''))

                

                #Nhập growth rate
                st.subheader("EPS Growth Rate")

                try:

                    if ticker_dir.exists() and ticker_dir.is_dir() and (ticker_dir / required_files[9]).exists():
                        # ====== CÓ DATA LOCAL ======
                        print(f"[LOCAL] Found data for {ticker}")
                        with open(f"database/{ticker}/save_selenium.json", "r", encoding="utf-8") as f:
                            raw = json.load(f)

                        results = checkTypeData.deserialize_results(raw)
                        # print(results)

                        growth_rate1, growth_rate2, growth_rate3 = crawl_mck.analysis(ticker, results, fullExchangeName=mck_info['fullExchangeName'])

                        daf, daf2, daf3, daf4, peg = crawl_mck.discounted_Cash_Flow_Method_10_years(ticker=ticker, rsSel=results)

                    else:
                        # ====== CHƯA CÓ DATA ======
                        print(f"[CRAWL] No data for {ticker}, crawling...")
                        secDict = crawl_mck.run_selenium(ticker, fullExchangeName=mck_info['fullExchangeName'])
                        print(secDict.keys())
                        growth_rate1, growth_rate2, growth_rate3 = crawl_mck.analysis(ticker=ticker, fullExchangeName = mck_info['fullExchangeName'], rsSel=secDict)
                        daf, daf2, daf3, daf4, peg = crawl_mck.discounted_Cash_Flow_Method_10_years(ticker=ticker, rsSel=secDict)
                except Exception as e:
                    if "HTTP Error 404" in str(e):
                        st.error(f"Ticker '{ticker}' không tồn tại! Vui lòng nhập lại")
                        st.stop()
                    else:
                        st.error(f"Ticker '{ticker}' không đầy đủ dữ liệu! Vui lòng nhập lại")
                        st.stop()
                            
                        gr1_str = st.text_input('EPS Next 5Y (%):', value=growth_rate1,
                                                    placeholder="Type a number...")
                        growth_rate1 = float(gr1_str)

                gr2_str = st.text_input('EPS Next 10Y (%):', value=growth_rate2,
                                            placeholder="Type a number...")
                growth_rate2 = float(gr2_str)
                gr3_str = st.text_input('EPS Next 20Y (%):', value=growth_rate3,
                                            placeholder="Type a number...") 
                growth_rate3 = float(gr3_str)

            with col6:

                TTM_cfs = quarter_cfs.iloc[:, :4].sum(axis=1)

                print(fast_info)

                TTM = quarter_income.iloc[:, :4].sum(axis=1)

                st.subheader("Currency Unit: " + str(fast_info['currency']))
                # fcf
                st.subheader("Free Cash Flow/Net Income/Operating Cash Flow")
                display_options = ["Free Cash Flow", "Net Income", "Operating Cash Flow"]
                selected_display_option = st.radio("Select display option:", display_options)

                if selected_display_option == "Free Cash Flow":
                    free_cash_flow = TTM_cfs['Free Cash Flow']
                    formatted_free_cash_flow = "{:,.2f}".format(free_cash_flow)
                    number2_str = st.text_input("Free Cash Flow (current):", value=formatted_free_cash_flow,
                                                placeholder="Type a number...")
                    number2 = float(number2_str.replace(',', ''))


                elif selected_display_option == "Net Income":
                    net_income = TTM['Net Income']
                    formatted_net_income = "{:,.2f}".format(net_income)
                    number2_str = st.text_input("Net Income:", value=formatted_net_income,
                                                placeholder="Type a number...")
                    number2 = float(number2_str.replace(',', ''))
                
                elif selected_display_option == "Operating Cash Flow":
                    operating_cash_flow = TTM_cfs['Operating Cash Flow']
                    formatted_operating_cash_flow = "{:,.2f}".format(operating_cash_flow)
                    number2_str = st.text_input("Operating Cash Flow:", value=formatted_operating_cash_flow,
                                                placeholder="Type a number...")
                    number2 = float(number2_str.replace(',', ''))
                
                # ds
                shares_outstanding = fast_info['shares']
                st.subheader("Implied Shares Outstanding:")
                formatted_shares_outstanding = "{:,.2f}".format(shares_outstanding)
                number7_str = st.text_input("Implied Shares Outstanding:", value=formatted_shares_outstanding,
                                            placeholder="Type a number...")
                number7 = float(number7_str.replace(',', ''))


                if ticker[-3:] == ".VN":
                    beta_value = beta_value if beta_value != 0 else beta[2].iloc[6]
                else: 
                    beta_value = beta_value if beta_value != 0 else float(dfe['Value'].iloc[6])
                st.subheader("Company Beta")
                formatted_beta = "{:,.3f}".format(float(beta_value))
                number1_str = st.text_input("Company Beta:", value=formatted_beta, placeholder="Type a number...")
                number1 = float(number1_str.replace(',', '')) 
                # Tính toán discount rate dựa trên giá trị beta
                st.subheader(" Discount Rate ")
                discount_rate_value = capm
                # Tính toán discount rate tương ứng
                formatted_discount_rate_value = "{:,.3f}".format(discount_rate_value)
                # Hiển thị discount rate trên Streamlit
                
                number8_str = st.text_input('Discount Rate (%):', value=formatted_discount_rate_value,
                                            placeholder="Type a number...")
                number8 = float(number8_str.replace(',', '').replace(' %', ''))

            col7, col8 = st.columns(2)
            with col7:
                # Creating the first table
                data1 = {
                    'Operating Cash Flow/Free Cash Flow/Net Income': [number2],
                    'Growth rate (Y 1-5)': growth_rate1/100,
                    'Growth rate (Y 6-10)': growth_rate2/100,
                    'Growth rate (Y 11-20)': growth_rate3/100,
                    'Discount rate': number8,
                    'Current year': number0
                }

                table1 = pd.DataFrame(data=data1)

                # Creating the second table with calculations based on the first table
                years = [
                    ((table1['Current year'][0]) + i)
                    for i in range(21)
                ]
                # print(table1['Current year'][0])
                cash_flows = [
                    (table1['Operating Cash Flow/Free Cash Flow/Net Income'][0] * (
                            (1 + table1['Growth rate (Y 1-5)'][0]) ** i)) if i <= 5
                    else ((table1['Operating Cash Flow/Free Cash Flow/Net Income'][0] * (
                            (1 + table1['Growth rate (Y 1-5)'][0]) ** 5)) * (
                                (1 + table1['Growth rate (Y 6-10)'][0]) ** (i - 5))) if 6 <= i <= 10
                    else ((table1['Operating Cash Flow/Free Cash Flow/Net Income'][0] * (
                            (1 + table1['Growth rate (Y 1-5)'][0]) ** 5)) * (
                                (1 + table1['Growth rate (Y 6-10)'][0]) ** 5) * (
                                (1 + table1['Growth rate (Y 11-20)'][0]) ** (i - 10)))
                    for i in range(21)
                ]

                discount_factors = [(1 / ((1 + table1['Discount rate'][0]/100) ** i)) for i in range(21)]
        
                discounted_values = [cf * df for cf, df in zip(cash_flows, discount_factors)]

                data2 = {
                    'Year': years[1:],
                    'Cash Flow': cash_flows[1:],
                    'Discount Factor': discount_factors[1:],
                    'Discounted Value': discounted_values[1:]
                }

                table2 = pd.DataFrame(data=data2)
                pd.set_option('display.float_format', lambda x: '{:,.2f}'.format(x))
                table2['Year'] = table2['Year'].astype(str).str.replace(',', '')
                st.subheader('Discounted Cash Flow')
                st.write(table2)
            with col8:
                # Tính Intrinsic Value
                total_discounted_value = sum(discounted_values)
                intrinsic_value = sum(discounted_values) / number7
                debt_per_share = number5 / number7
                cash_per_share = number6 / number7
                st.subheader('Value')
                data3 = pd.DataFrame({
                    "STT": [1, 2, 3, 4],
                    "Index": ['PV of 20 yr Cash Flows', 'Intrinsic Value before cash/debt', 'Debt per Share',
                            'Cash per Share'],
                    "Value": [total_discounted_value, intrinsic_value, debt_per_share, cash_per_share],
                })
                st.data_editor(data3, hide_index=True)

                final_intrinsic_value = intrinsic_value - debt_per_share + cash_per_share
                st.subheader(f"Final Intrinsic Value per Share: {final_intrinsic_value:,.2f}")
                st.write('Current Price: ', cr_price)
                ratio = ((final_intrinsic_value/crprice) - 1)*100
                st.markdown(
                    f":{'red' if ratio < 0 else 'green'}[{'↓' if ratio < 0 else '↑'} {round(ratio,2)} %]"
                )

            # Ve bieu do Intrinsic Value Calculator (Discounted Cash Flow Method 10 years)
            # daf, daf2, daf3, daf4, peg = crawl_mck.discounted_Cash_Flow_Method_10_years(ticker=ticker, rsSel=secDict)

            pDe = round(float(daf3.iloc[0, 1]),2) if '--' not in daf3.iloc[0, 1] else 0
            EPS_LT_Growth_Est = growth_rate1
            print(EPS_LT_Growth_Est)
            PEG_Ratio = pDe/EPS_LT_Growth_Est

            ticker_csv = pd.read_csv("ticker_data.csv")
            list_ticker = ticker_csv["Ticker"].to_list()

            if "MOAT_grade" not in st.session_state:
                st.session_state.MOAT_grade = None

            # Chỉ tính nếu chưa có trong CSV và chưa từng tính
            if ticker in list_ticker:
                st.session_state.MOAT_grade = ticker_csv.loc[
                    ticker_csv["Ticker"] == ticker, "Moat Score"
                ].values[0]
            else:
            #     if st.session_state.MOAT_grade is None:
            #         print("Sử dụng ChatGPT để tính điểm MOAT")
            #         st.session_state.MOAT_grade = ask_chatGPT(f"tính điểm Economic Moat cho công ty {ticker}. Sau đó trả lời cho tôi duy nhất số điểm, có format là số điểm/10, không thêm từ nào khác.")
            # MOAT_grade = st.session_state.MOAT_grade
                if st.session_state.MOAT_grade is None:
                    if st.button("Calculate Economic Moat Score"):
                        with st.spinner("Calculating MOAT score..."):
                            st.session_state.MOAT_grade = ask_chatGPT(
                                f"Tính điểm Economic Moat cho công ty {ticker}. "
                                "Chỉ trả lời duy nhất một giá trị có định dạng X/10, không thêm bất kỳ từ nào khác."
                            )
            MOAT_grade = st.session_state.MOAT_grade
            his = {
                "Ticker": [ticker],
                "Industry": [mck_info['industry']],
                "Current Price": [cr_price],
                "P/E": [pDe],
                "Forward P/E": [round(float(daf4.iloc[0, 1]),2) if '--' not in daf4.iloc[0, 1] else ''],
                "PEG Ratio": [f"{PEG_Ratio:.2f}"],
                "P/B": [round(float(daf.iloc[0, 1]),2) if '--' not in daf.iloc[0, 1] else ''],
                "EPS LT Growth Est": [f"{EPS_LT_Growth_Est:.2f}%"],
                "Intrinsic Value": [f"{final_intrinsic_value:.2f}"],
                "Discount/Premium": [f"{ratio:.2f}%"], 
                "Moat Score": [MOAT_grade]
            }
                    
            # Chart
            cash_flow = table2['Cash Flow']
            discounted_value = table2['Discounted Value']
            years = table2['Year']
            # print(years)
            columns_to_plot = ['Cash Flow', 'Discounted Value']
            fig = px.line(table2, x=years, y=columns_to_plot,
                        title='Intrinsic Value Calculator (Discounted Cash Flow Method 10 years)',
                        labels={'value': 'Value', 'variable': 'Legend'},
                        height=500, width=1100, markers='o')
            fig.update_xaxes(fixedrange=True)

            # Thay đổi các chú thích trên trục x
            fig.update_xaxes(
                tickvals=years[0:]
            )
            fig.update_xaxes(title_text="Time")
            st.plotly_chart(fig)
            wat = pd.DataFrame(his)
            st.markdown("<h1 style='font-size: 16px; font-weight: bold;'>Các phương pháp định giá</h1>", unsafe_allow_html=True)
            st.write(wat)

            if st.button("Save to Watchlist", key="button4"):
                crawl_mck.save_to_csv(wat)
        with guru:

            shares_outstanding = fast_info['shares']

            try:
                if ticker_dir.exists() and ticker_dir.is_dir() and (ticker_dir / required_files[2]).exists():
                    # ====== CÓ DATA LOCAL ======
                    print(f"[LOCAL] Found data for {ticker}")
                    cfs = pd.read_parquet(f"./database/{ticker}/cfs.parquet")

                else:
                    # ====== CHƯA CÓ DATA ======
                    print(f"[CRAWL] No data for {ticker}, crawling...")
                    cfs = mck.cash_flow
            except Exception as e:
                if "HTTP Error 404" in str(e):
                    st.error(f"Ticker '{ticker}' không tồn tại! Vui lòng nhập lại")
                    st.stop()
                else:
                    st.error(f"Ticker '{ticker}' không đầy đủ dữ liệu! Vui lòng nhập lại")
                    st.stop()


            print("----------------------------------Các features bị thiếu trong bsheet----------------------------------")
            ensure_key(bsheet , "bsheet")
            print("----------------------------------Các features bị thiếu trong TTM_bsheet----------------------------------")
            ensure_key(TTM_bsheet, "TTM_bsheet")
            print("----------------------------------Các features bị thiếu trong TTM_bsheet2----------------------------------")
            ensure_key(TTM_bsheet2, "TTM_bsheet2")
            print("----------------------------------Các features bị thiếu trong TTM_bsheet3----------------------------------")
            ensure_key(TTM_bsheet3, "TTM_bsheet3")
            print("----------------------------------Các features bị thiếu trong TTM_bsheet4----------------------------------")
            ensure_key(TTM_bsheet4, "TTM_bsheet4")
            print("----------------------------------Các features bị thiếu trong TTM----------------------------------")
            ensure_key(TTM, "TTM")
            print("----------------------------------Các features bị thiếu trong TTM_cfs----------------------------------")
            ensure_key(TTM_cfs, "TTM_cfs")
            print("----------------------------------Các features bị thiếu trong income----------------------------------")
            ensure_key(income, "income")

            ave_debt = TTM_bsheet3/4
            print(TTM_bsheet3['Total Debt'])
            print(ave_debt['Total Debt'])
            cost_of_debt = TTM['Interest Expense']/ave_debt['Total Debt'] if 'Interest Expense' in TTM else 0
            tax_rate = TTM['Tax Provision']/TTM['Pretax Income']
            market_cap = fast_info['marketCap'] 
            wacc = (market_cap/(market_cap+ave_debt['Total Debt'])) * discount_rate_value + (ave_debt['Total Debt']/(market_cap+ave_debt['Total Debt'])) * cost_of_debt *(1-tax_rate)

            placeholder.success("Tất cả đã load xong!")
            
            # if 'Current Liabilities' not in TTM_bsheet.index:
            #     TTM_bsheet['Current Liabilities'] = 1
            #     TTM_bsheet2['Current Liabilities'] = 1
            # if 'Current Assets' not in TTM_bsheet.index:
            #     TTM_bsheet['Current Assets'] = 1
            #     TTM_bsheet2['Current Assets'] = 1
            # if 'Operating Income' not in TTM.index:
            #     TTM['Operating Income'] = 1

            # if 'Current Liabilities' not in bsheet.index:
            #     bsheet.loc['Current Liabilities'] = [1] * len(bsheet.columns)
            # if 'Current Assets' not in bsheet.index:
            #     bsheet.loc['Current Assets'] = [1] * len(bsheet.columns)
            # if 'Operating Income' not in bsheet.index:
            #     bsheet.loc['Operating Income'] = [1] * len(bsheet.columns)

            # Score #7 - change in Current Ratio
            cr_ratio_history = [bsheet[year]['Current Assets'] / bsheet[year]['Current Liabilities'] for year in
                                years_val[::-1]]

            # GURU
            # Liquidity + Dividend
            cr_ratio = round((TTM_bsheet['Current Assets'] / TTM_bsheet['Current Liabilities']), 2)
            # Lấy dữ liệu từ năm trước đến năm hiện tại
            cr_list = cr_ratio_history + [cr_ratio]
            cr_rank = sorted(cr_list)
            cr_ratio_p = cr_rank.index(cr_ratio) + 1
            cr_len = len(cr_rank)
            cr_values2 = cr_ratio_p / cr_len

            if 'Inventory' in TTM_bsheet:
                qr_ratio = round(
                    ((TTM_bsheet['Current Assets'] - TTM_bsheet['Inventory']) / TTM_bsheet['Current Liabilities']), 2)
                qr_ratio_history = [(bsheet[year]['Current Assets'] - bsheet[year]['Inventory']) / bsheet[year]['Current Liabilities'] for year in
                                    years_val[::-1]]
                
                qr_ratio_history = []
                for year in years_val[::-1]:

                    inventory_values = bsheet.loc['Inventory', year]
                    if pd.isnull(inventory_values):  # Kiểm tra xem inventory_values có phải là NaN hay không
                        inventory_values = bsheet.loc['Inventory', year - pd.DateOffset(years=1)]

                    cr_liabilities = bsheet.loc['Current Liabilities', year]
                    cr_asset = bsheet.loc['Current Assets', year]

                    if pd.notnull(cr_liabilities) and pd.notnull(cr_asset) and pd.notnull(inventory_values):
                        qr_ratio = (cr_asset - inventory_values) / cr_liabilities
                        qr_ratio_history.append(qr_ratio)
                    else:
                        qr_ratio_history.append(0)
            else:
                inventory_values = 0
                qr_ratio = cr_ratio
                qr_ratio_history = cr_ratio_history

            qr_list = qr_ratio_history + [qr_ratio] 
            qr_rank = sorted(qr_list)
            qr_ratio_p = qr_rank.index(qr_ratio) + 1
            qr_len = len(qr_rank)
            qr_values = qr_ratio_p / qr_len

            car_ratio = round((TTM_bsheet['Cash And Cash Equivalents'] / TTM_bsheet['Current Liabilities']), 2)
            car_ratio_history = [
                bsheet.loc['Cash And Cash Equivalents', year] / (bsheet.loc['Current Liabilities', year] or 1) for year
                in
                years_val[::-1]]

            car_list = car_ratio_history + [car_ratio]
            car_rank = sorted(car_list)
            car_ratio_p = car_rank.index(car_ratio) + 1
            car_len = len(car_rank)
            car_values = car_ratio_p / car_len

            if 'Accounts Receivable' not in TTM_bsheet.index:
                TTM_bsheet['Accounts Receivable'] = 0
                TTM_bsheet2['Accounts Receivable'] = 0
                bsheet.loc['Accounts Receivable'] = [1] * len(bsheet.columns)
            dso_ratio = round((TTM_bsheet['Accounts Receivable'] / TTM['Total Revenue']) * 365, 2)
            dso_ratio_history = [
                bsheet.loc['Accounts Receivable', year] * 365 / (income.loc['Total Revenue', year] or 1) for year in
                years_val[::-1]]

            dso_ = dso_ratio_history + [dso_ratio]
            dso_l = np.array(dso_)
            mean_value = np.nanmean(dso_l)
            dso_l[np.isnan(dso_l)] = mean_value
            dso_list = dso_l.tolist()
            dso_rank = sorted(dso_list, reverse=True)
            dso_ratio_p = dso_rank.index(dso_ratio) + 1
            dso_len = len(dso_rank)
            dso_values = dso_ratio_p / dso_len

            if 'Cost Of Revenue' not in TTM.index:
                TTM['Cost Of Revenue'] = 1
                income.loc['Cost Of Revenue'] = [1] * len(income.columns)

            ap_average_values = (TTM_bsheet2['Accounts Payable'] + TTM_bsheet['Accounts Payable']) / 2
            dp_ratio = round((ap_average_values / TTM['Cost Of Revenue']) * 365, 2)
            dp_ratio_history = [bsheet.loc['Accounts Payable', year] * 365 / (income.loc['Cost Of Revenue', year] or 1)
                                for year in years_val[::-1]]

            dp_list = dp_ratio_history + [dp_ratio]
        
            dp_rank = sorted(dp_list)
            dp_ratio_p = dp_rank.index(dp_ratio) + 1
            dp_len = len(dp_rank)
            dp_values = dp_ratio_p / dp_len

            if 'Inventory' in TTM_bsheet:

                inv_average = (TTM_bsheet2['Inventory'] + TTM_bsheet['Inventory']) / 2
                dio_ratio = round((inv_average / TTM['Cost Of Revenue']) * 365, 2)
                dio_ratio_history = [bsheet.loc['Inventory', year] * 365 / (income.loc['Cost Of Revenue', year] or 1)
                                    for year in years_val[::-1]]
                dio_ratio_history = []
                for year in years_val[::-1]:
                    inventory_values = bsheet.loc['Inventory', year]
                    if pd.isnull(inventory_values):  # Kiểm tra xem inventory_values có phải là NaN hay không
                        inventory_values = bsheet.loc['Inventory', year - pd.DateOffset(years=1)]

                    cost_of_rvn = income.loc['Cost Of Revenue', year]

                    if pd.notnull(cost_of_rvn) and pd.notnull(inventory_values):
                        dio_ratio = (inventory_values) * 365 / cost_of_rvn
                        dio_ratio_history.append(dio_ratio)
                    else:
                        dio_ratio_history.append(0)

                dio_list = dio_ratio_history + [dio_ratio]
                dio_rank = sorted(dio_list, reverse=True)
                dio_ratio_p = dio_rank.index(dio_ratio) + 1
                dio_len = len(dio_rank)
                dio_values = dio_ratio_p / dio_len
            else:
                dio_values = 0
                dio_ratio = 0
                dio_ratio_p = 0
                dio_len = 0
                dio_list = 0

            div_ratio = mck_info[
                            'trailingAnnualDividendYield'] * 100 if 'trailingAnnualDividendYield' in mck_info else 0
            pr_ratio = mck_info['payoutRatio'] if 'payoutRatio' in mck_info else 0
            five_years_ratio = mck_info['fiveYearAvgDividendYield'] if 'fiveYearAvgDividendYield' in mck_info else 0
            forward_ratio = mck_info['dividendYield'] * 100 if 'dividendYield' in mck_info else 0

            # PE Ratio
            shares_outstanding = fast_info['shares']
            # with open('mck_fast_info.pkl', 'wb') as f:
            #     pickle.dump(mck.fast_info, f)
            PE_ratio = mck_info['trailingPE'] if 'trailingPE' in mck_info else 0

            pe_ratio_history = []
            for year in years_val[::-1]:
                basic_eps = income.loc['Basic EPS', year]
                if pd.isnull(basic_eps):  # Kiểm tra xem basic_eps có phải là NaN hay không
                    basic_eps = income.loc['Basic EPS', year - pd.DateOffset(years=1)]

                total_capitalization = bsheet.loc['Total Capitalization', year]
                share_issued = bsheet.loc['Share Issued', year]

                if pd.notnull(total_capitalization) and pd.notnull(share_issued) and pd.notnull(basic_eps):
                    pe_ratio = (total_capitalization / share_issued) / basic_eps
                    pe_ratio_history.append(pe_ratio)
                else:
                    pe_ratio_history.append(0)

            PE_ratio_list = pe_ratio_history + [PE_ratio]
            PE_ratio_rank = sorted(PE_ratio_list)
            PE_ratio_p = PE_ratio_rank.index(PE_ratio) + 1
            PE_ratio_len = len(PE_ratio_rank)
            PE_ratio_values = PE_ratio_p / PE_ratio_len

            # P/S Ratio
            PS_ratio = crprice / (TTM['Total Revenue']/fast_info['shares'])
            ps_ratio_history = [(bsheet.loc['Total Capitalization', year] / bsheet.loc['Share Issued', year]) / (
                    income.loc['Total Revenue', year] / bsheet.loc['Share Issued', year]) for year in years_val[::-1]]
            PS_ratio_list = ps_ratio_history + [PS_ratio]
            PS_ratio_rank = sorted(PS_ratio_list)
            PS_ratio_p = PS_ratio_rank.index(PS_ratio) + 1
            PS_ratio_len = len(PS_ratio_rank)
            PS_ratio_values = PS_ratio_p / PS_ratio_len

            # P/B Ratio
            PB_ratio = 0
            if 'priceToBook' in mck_info:
                PB_ratio = mck_info['priceToBook']
            else:
                PB_ratio = 0
            pb_ratio_history = []
            for year in years_val[::-1]:
                basic_eps = income.loc['Basic EPS', year]
                if pd.isnull(basic_eps):  # Kiểm tra xem basic_eps có phải là NaN hay không
                    basic_eps = income.loc['Basic EPS', year - pd.DateOffset(years_val=1)]

                stock_holderequity = bsheet.loc['Stockholders Equity', year]
                net_income1 = income.loc['Net Income', year]

                if pd.notnull(stock_holderequity) and pd.notnull(net_income1) and pd.notnull(basic_eps):
                    pb_ratio = (stock_holderequity / net_income1) / basic_eps
                    pb_ratio_history.append(pb_ratio)
                else:
                    pb_ratio_history.append(0)

            PB_ratio_list = pb_ratio_history + [PB_ratio]
            PB_ratio_rank = sorted(PB_ratio_list)
            PB_ratio_p = PB_ratio_rank.index(PB_ratio) + 1
            PB_ratio_len = len(PB_ratio_rank)
            PB_ratio_values = PB_ratio_p / PB_ratio_len

            # Price-to-tangible-book Ratio
            Price_to_TBV = crprice / (TTM_bsheet['Tangible Book Value'] / shares_outstanding)
            Price_to_TBV_history = [(bsheet.loc['Total Capitalization', year] / bsheet.loc['Share Issued', year]) / (
                    bsheet.loc['Tangible Book Value', year] / bsheet.loc['Share Issued', year]) for year in years_val[::-1]]
            Price_to_TBV_list = Price_to_TBV_history + [Price_to_TBV]
            Price_to_TBV_rank = sorted(Price_to_TBV_list)
            Price_to_TBV_p = Price_to_TBV_rank.index(Price_to_TBV) + 1
            Price_to_TBV_len = len(Price_to_TBV_rank)
            Price_to_TBV_values = Price_to_TBV_p / Price_to_TBV_len

            # Price-to-Free-Cash_Flow Ratio
            price_to_FCF = crprice / (TTM_cfs['Free Cash Flow'] / shares_outstanding)
            Price_to_FCF_history = [(bsheet.loc['Total Capitalization', year] / bsheet.loc['Share Issued', year]) / (
                    cfs.loc['Free Cash Flow', year] / bsheet.loc['Share Issued', year]) for year in years_val[::-1]]
            price_to_FCF_list = Price_to_FCF_history + [price_to_FCF]
            price_to_FCF_rank = sorted(price_to_FCF_list)
            price_to_FCF_p = price_to_FCF_rank.index(price_to_FCF) + 1
            price_to_FCF_len = len(price_to_FCF_rank)
            price_to_FCF_values = price_to_FCF_p / price_to_FCF_len

            # EV-to-EBIT
            if 'EBIT' not in TTM.index:
                TTM['EBIT'] = 1
                income.loc['EBIT'] = [1] * len(income.columns)
            EV_to_EBIT = (fast_info['marketCap'] + TTM_bsheet['Total Debt'] - TTM_bsheet['Cash Cash Equivalents And Short Term Investments'])/ TTM['EBIT'] if 'Total Debt' in TTM_bsheet and 'Cash Cash Equivalents And Short Term Investments' in TTM_bsheet else fast_info['marketCap']/TTM['EBIT']
            EV_to_EBIT_history = [(bsheet.loc['Total Capitalization', year] - bsheet.loc[
                'Total Liabilities Net Minority Interest', year] - bsheet.loc[
                                    'Cash Cash Equivalents And Short Term Investments', year]) / (
                                    income.loc['EBIT', year]) for year in years_val[::-1]]
            EV_to_EBIT_list = EV_to_EBIT_history + [EV_to_EBIT]
            EV_to_EBIT_rank = sorted(EV_to_EBIT_list)
            EV_to_EBIT_p = EV_to_EBIT_rank.index(EV_to_EBIT) + 1
            EV_to_EBIT_len = len(EV_to_EBIT_rank)
            EV_to_EBIT_values = EV_to_EBIT_p / EV_to_EBIT_len

            # EV-to-EBITDA
            EV_to_EBITDA = (fast_info['marketCap'] + TTM_bsheet['Total Debt'] - TTM_bsheet['Cash Cash Equivalents And Short Term Investments'])/ TTM['EBITDA'] if 'Total Debt' in TTM_bsheet and 'Cash Cash Equivalents And Short Term Investments' in TTM_bsheet else fast_info['marketCap']/TTM['EBITDA']
            EV_to_EBITDA_history = [(bsheet.loc['Total Capitalization', year] - bsheet.loc[
                'Total Liabilities Net Minority Interest', year] - bsheet.loc[
                                        'Cash Cash Equivalents And Short Term Investments', year]) / (
                                        income.loc['EBITDA', year]) for year in years_val[::-1]]
            EV_to_EBITDA_list = EV_to_EBITDA_history + [EV_to_EBITDA]
            EV_to_EBITDA_rank = sorted(EV_to_EBITDA_list)
            EV_to_EBITDA_p = EV_to_EBITDA_rank.index(EV_to_EBITDA) + 1
            EV_to_EBITDA_len = len(EV_to_EBITDA_rank)
            EV_to_EBITDA_values = EV_to_EBITDA_p / EV_to_EBITDA_len

            # EV-to-Revenue
            EV_to_Revenue = (fast_info['marketCap'] + TTM_bsheet['Total Debt'] - TTM_bsheet['Cash Cash Equivalents And Short Term Investments'])/ TTM['Total Revenue'] if 'Total Debt' in TTM_bsheet and 'Cash Cash Equivalents And Short Term Investments' in TTM_bsheet else fast_info['marketCap']/TTM['Total Revenue']
            EV_to_Revenue_history = [(bsheet.loc['Total Capitalization', year] - bsheet.loc[
                'Total Liabilities Net Minority Interest', year] - bsheet.loc[
                                        'Cash Cash Equivalents And Short Term Investments', year]) / (
                                        income.loc['Total Revenue', year]) for year in years_val[::-1]]
            EV_to_Revenue_list = EV_to_Revenue_history + [EV_to_Revenue]
            EV_to_Revenue_rank = sorted(EV_to_Revenue_list)
            EV_to_Revenue_p = EV_to_Revenue_rank.index(EV_to_Revenue) + 1
            EV_to_Revenue_len = len(EV_to_Revenue_rank)
            EV_to_Revenue_values = EV_to_Revenue_p / EV_to_Revenue_len

            # EV-to-FCF
            EV_to_FCF = (fast_info['marketCap'] + TTM_bsheet['Total Debt'] - TTM_bsheet['Cash Cash Equivalents And Short Term Investments'])/ TTM_cfs['Free Cash Flow'] if 'Total Debt' in TTM_bsheet and 'Cash Cash Equivalents And Short Term Investments' in TTM_bsheet else fast_info['marketCap']/TTM_cfs['Free Cash Flow']
            EV_to_FCF_history = [(bsheet.loc['Total Capitalization', year] - bsheet.loc[
                'Total Liabilities Net Minority Interest', year] - bsheet.loc[
                                    'Cash Cash Equivalents And Short Term Investments', year]) / (
                                    cfs.loc['Free Cash Flow', year]) for year in years_val[::-1]]
            EV_to_FCF_list = EV_to_FCF_history + [EV_to_FCF]
            EV_to_FCF_rank = sorted(EV_to_FCF_list)
            EV_to_FCF_p = EV_to_FCF_rank.index(EV_to_FCF) + 1
            EV_to_FCF_len = len(EV_to_FCF_rank)
            EV_to_FCF_values = EV_to_FCF_p / EV_to_FCF_len

            # Price-to-Net-Current-Asset-Value
            print(TTM_bsheet['Current Assets'])
            print(TTM_bsheet['Current Liabilities'])
            print(shares_outstanding)
            Price_to_Net_CAV = crprice / (
                    (TTM_bsheet['Current Assets'] - TTM_bsheet['Current Liabilities']) / shares_outstanding)
            Price_to_Net_CAV_history = [
                (bsheet.loc['Total Capitalization', year] / bsheet.loc['Share Issued', year]) / (
                        (bsheet.loc['Current Assets', year] - bsheet.loc['Current Liabilities', year])
                        / bsheet.loc['Share Issued', year]) for year in years_val[::-1]]
            Price_to_Net_CAV_list = Price_to_Net_CAV_history + [Price_to_Net_CAV]
            Price_to_Net_CAV_rank = sorted(Price_to_Net_CAV_list)
            Price_to_Net_CAV_p = Price_to_Net_CAV_rank.index(Price_to_Net_CAV) + 1
            Price_to_Net_CAV_len = len(Price_to_Net_CAV_rank)
            Price_to_Net_CAV_values = Price_to_Net_CAV_p / Price_to_Net_CAV_len

            # Earnings Yields (Greenblatt) %
            EarningsYields = (TTM['EBIT'] / (fast_info['marketCap'] + TTM_bsheet['Total Debt'] - TTM_bsheet['Cash Cash Equivalents And Short Term Investments']) if 'Total Debt' in TTM_bsheet and 'Cash Cash Equivalents And Short Term Investments' in TTM_bsheet else TTM['EBIT']/fast_info['marketCap']) * 100
            EarningsYields_history = [
                ((income.loc['EBIT', year] / (bsheet.loc['Total Capitalization', year] - bsheet.loc[
                    'Total Liabilities Net Minority Interest', year] - bsheet.loc[
                                                'Cash Cash Equivalents And Short Term Investments', year])) * 100)
                for year in years_val[::-1]]
            EarningsYields_list = EarningsYields_history + [EarningsYields]
            EarningsYields_rank = sorted(EarningsYields_list)
            EarningsYields_p = EarningsYields_rank.index(EarningsYields) + 1
            EarningsYields_len = len(EarningsYields_rank)
            EarningsYields_values = EarningsYields_p / EarningsYields_len

            # FCF Yield %
            FCFYield = (TTM_cfs['Free Cash Flow'] / mck_info['marketCap']) * 100 if 'marketCap' in mck_info else (
                    TTM_cfs[
                            'Free Cash Flow'] /
                        fast_info[
                            'marketCap']) * 100
            FCFYield_history = [((cfs.loc['Free Cash Flow', year] / bsheet.loc['Total Capitalization', year]) * 100) for
                                year in
                                years_val[::-1]]
            FCFYield_list = FCFYield_history + [FCFYield]
            FCFYield_rank = sorted(FCFYield_list)
            FCFYield_p = FCFYield_rank.index(FCFYield) + 1
            FCFYield_len = len(FCFYield_rank)
            FCFYield_values = FCFYield_p / FCFYield_len

            # Profitability Rank
            # Gross Margin %
            gr_margin = round((TTM['Gross Profit'] * 100 / TTM['Total Revenue']), 2)
            gr_margin_history = [
                income.loc['Gross Profit', year] * 100 / (income.loc['Total Revenue', year] or 1) for year in
                years_val[::-1]]
            # Tìm min max
            gr_margin_list = gr_margin_history + [gr_margin]
            gr_margin_rank = sorted(gr_margin_list)
            gr_margin_p = gr_margin_rank.index(gr_margin) + 1
            gr_margin_len = len(gr_margin_rank)
            gr_margin_values = gr_margin_p / gr_margin_len

            # Operating Margin %
            op_margin = round((TTM['Operating Income'] * 100 / TTM['Total Revenue']), 2)
            op_margin_history = [
                income.loc['Operating Income', year] * 100 / (income.loc['Total Revenue', year] or 1) for year in
                years_val[::-1]]
            # Tìm min max
            op_margin_list = op_margin_history + [op_margin]
            op_margin_rank = sorted(op_margin_list)
            op_margin_p = op_margin_rank.index(op_margin) + 1
            op_margin_len = len(op_margin_rank)
            op_margin_values = op_margin_p / op_margin_len
            # Net Margin %
            net_margin = round((TTM['Net Income'] * 100 / TTM['Total Revenue']), 2)
            net_margin_history = [
                income.loc['Net Income', year] * 100 / (income.loc['Total Revenue', year] or 1) for year in
                years_val[::-1]]
            # Tìm min max
            net_margin_list = net_margin_history + [net_margin]
            net_margin_rank = sorted(net_margin_list)
            net_margin_p = net_margin_rank.index(net_margin) + 1
            net_margin_len = len(net_margin_rank)
            net_margin_values = net_margin_p / net_margin_len
            # FCF margin %
            fcf_margin = round((TTM_cfs['Free Cash Flow'] * 100 / TTM['Total Revenue']), 2)
            fcf_margin_history = [
                cfs.loc['Free Cash Flow', year] * 100 / (income.loc['Total Revenue', year] or 1) for year in
                years_val[::-1]]
            # Tìm min max
            fcf_margin_list = fcf_margin_history + [fcf_margin]
            fcf_margin_rank = sorted(fcf_margin_list)
            fcf_margin_p = fcf_margin_rank.index(fcf_margin) + 1
            fcf_margin_len = len(fcf_margin_rank)
            fcf_margin_values = fcf_margin_p / fcf_margin_len

            # ROE%
            roe_stock_average = (TTM_bsheet2['Total Equity Gross Minority Interest'] + TTM_bsheet[
                'Total Equity Gross Minority Interest']) / 2
            roe_margin = round((TTM['Net Income'] * 100 / roe_stock_average), 2)
            roe_margin_history = [
                income.loc['Net Income', year] * 100 / bsheet.loc['Total Equity Gross Minority Interest', year] if pd.notnull(bsheet.loc['Total Equity Gross Minority Interest', year]) else 1
                for year in years_val[::-1]]
            # Tìm min max
            roe_margin_list = roe_margin_history + [roe_margin]
            roe_margin_rank = sorted(roe_margin_list)
            roe_margin_p = roe_margin_rank.index(roe_margin) + 1
            roe_margin_len = len(roe_margin_rank)
            roe_margin_values = roe_margin_p / roe_margin_len

            # ROA%
            roa_tta_average = (TTM_bsheet2['Total Assets'] + TTM_bsheet['Total Assets']) / 2
            roa_margin = round((TTM['Net Income'] * 100 / roa_tta_average), 2)
            roa_margin_history = [income.loc['Net Income', year] * 100 / (bsheet.loc['Total Assets', year] or 1)
                                for year in years_val[::-1]]

            # Tìm min max
            roa_margin_list = roa_margin_history + [roa_margin]
            roa_margin_rank = sorted(roa_margin_list)
            roa_margin_p = roa_margin_rank.index(roa_margin) + 1
            roa_margin_len = len(roa_margin_rank)
            roa_margin_values = roa_margin_p / roa_margin_len

            # ROC (Joel Greenblatt) %
            # print(TTM_bsheet.index)
            fix_work_average = (TTM_bsheet['Net Tangible Assets'] + TTM_bsheet['Working Capital']) / 2
            roc_margin = round((TTM['EBIT'] * 100 / fix_work_average), 2)
            roc_margin_history = [income.loc['EBIT', year] * 100 / (
                    (bsheet.loc['Net Tangible Assets', year] + bsheet.loc['Working Capital', year]) / 2 or 1)
                                for year in years_val[::-1]]
            # Tìm min max
            roc_margin_list = roc_margin_history + [roc_margin]
            roc_margin_rank = sorted(roc_margin_list)
            roc_margin_p = roc_margin_rank.index(roc_margin) + 1
            roc_margin_len = len(roc_margin_rank)
            roc_margin_values = roc_margin_p / roc_margin_len

            # ROCE%
            cap_em_1 = (TTM_bsheet['Total Assets'] - TTM_bsheet['Current Liabilities'])
            cap_em_2 = (TTM_bsheet2['Total Assets'] - TTM_bsheet2['Current Liabilities'])
            cap_em_average = (cap_em_1 + cap_em_2) / 2
            roce_margin = round((TTM['EBIT'] * 100 / cap_em_average), 2)
            roce_margin_history = [income.loc['EBIT', year] * 100 / 
                    (bsheet.loc['Total Assets', year] - bsheet.loc['Current Liabilities', year]) if pd.notnull(income.loc['EBIT', year]) and pd.notnull(bsheet.loc['Current Liabilities', year])
                    else 1 for year in years_val[::-1]]
            # Tìm min max
            roce_margin_list = roce_margin_history + [roce_margin]
            roce_margin_rank = sorted(roce_margin_list)
            roce_margin_p = roce_margin_rank.index(roce_margin) + 1
            roce_margin_len = len(roce_margin_rank)
            roce_margin_values = roce_margin_p / roce_margin_len
            
            # Financial Strength

            # Cash_to_debt
            cash_debt = TTM_bsheet['Cash Cash Equivalents And Short Term Investments'] / TTM_bsheet['Total Debt']
            cash_debt_history = [
                (bsheet.loc['Cash Cash Equivalents And Short Term Investments', year] / bsheet.loc['Total Debt', year]
                if pd.notnull(bsheet.loc['Cash Cash Equivalents And Short Term Investments', year]) and bsheet.loc['Total Debt', year] != 0
                else 0 if bsheet.loc['Total Debt', year] == 0
                else 1)
                for year in years_val[::-1]
            ]

            cash_debt_list = cash_debt_history + [cash_debt]
            cash_debt_rank = sorted(cash_debt_list)
            cash_debt_p = cash_debt_rank.index(cash_debt) + 1
            cash_debt_len = len(cash_debt_rank)
            cash_debt_values = cash_debt_p / cash_debt_len

            # Equity to Asset
            equity_asset = TTM_bsheet['Stockholders Equity'] / TTM_bsheet['Total Assets']
            equity_asset_history = [bsheet.loc['Stockholders Equity', year] / bsheet.loc['Total Assets', year] if pd.notnull(bsheet.loc['Stockholders Equity', year]) else 1
                                    for year in years_val[::-1]]

            equity_asset_list = equity_asset_history + [equity_asset]
            equity_asset_rank = sorted(equity_asset_list)
            equity_asset_p = equity_asset_rank.index(equity_asset) + 1
            equity_asset_len = len(equity_asset_rank)
            equity_asset_values = equity_asset_p / equity_asset_len

            # Debt to Equity
            debt_equity = TTM_bsheet['Total Debt'] / TTM_bsheet['Stockholders Equity']
            debt_equity_history = [bsheet.loc['Total Debt', year] / bsheet.loc['Stockholders Equity', year] if pd.notnull(bsheet.loc['Stockholders Equity', year]) else 1 for
                                year in years_val[::-1]]

            debt_equity_list = debt_equity_history + [debt_equity]
            debt_equity_rank = sorted(debt_equity_list, reverse=True)
            debt_equity_p = debt_equity_rank.index(debt_equity) + 1
            debt_equity_len = len(debt_equity_rank)
            debt_equity_values = debt_equity_p / debt_equity_len

            # Debt to EBITDA
            debt_ebitda = TTM_bsheet['Total Debt'] / TTM['EBITDA'] if 'Total Debt' in TTM_bsheet else 0
            debt_ebitda_history = [bsheet.loc['Total Debt', year] / income.loc['EBITDA', year] if pd.notnull(income.loc['EBITDA', year]) else 1 for year in
                                years_val[::-1]]

            debt_ebitda_list = debt_ebitda_history + [debt_ebitda]
            debt_ebitda_rank = sorted(debt_ebitda_list)
            debt_ebitda_p = debt_ebitda_rank.index(debt_ebitda) + 1
            debt_ebitda_len = len(debt_ebitda_rank)
            debt_ebitda_values = debt_ebitda_p / debt_ebitda_len
            
            # Interest Coverage
            if 'Interest Expense' in TTM and TTM['Interest Expense'] !=0:
                interest_coverage = TTM['Operating Income'] / TTM['Interest Expense']
                interest_coverage_history = [
                    income.loc['Operating Income', year] / income.loc['Interest Expense', year] if pd.notnull(income.loc['Interest Expense', year]) else 1 for year in
                    years_val[::-1]]
                interest_coverage_list = interest_coverage_history + [interest_coverage]
                interest_coverage_rank = sorted(interest_coverage_list)
                interest_coverage_p = interest_coverage_rank.index(interest_coverage) + 1
                interest_coverage_len = len(interest_coverage_rank)
                interest_coverage_values = interest_coverage_p / interest_coverage_len
            else: 
                interest_coverage_values = 0
                interest_coverage = 'None'
                interest_coverage_list = [0]
                interest_coverage_p = 0
                interest_coverage_len = 0
            # Altman F-Score
            a = TTM_bsheet['Working Capital'] / TTM_bsheet['Total Assets']
            b = TTM_bsheet['Retained Earnings'] / TTM_bsheet['Total Assets']
            c = TTM['EBIT'] / TTM_bsheet['Total Assets']
            try:
                if ticker_dir.exists() and ticker_dir.is_dir() and (ticker_dir / required_files[4]).exists():
                    # ====== CÓ DATA LOCAL ======
                    print(f"[LOCAL] Found data for {ticker}")
                    d = fast_info['marketCap'] / TTM_bsheet['Total Liabilities Net Minority Interest'] 

                else:
                    # ====== CHƯA CÓ DATA ======
                    print(f"[CRAWL] No data for {ticker}, crawling...")
                    d = mck.fast_info['marketCap'] / TTM_bsheet['Total Liabilities Net Minority Interest'] 
            except Exception as e:
                if "HTTP Error 404" in str(e):
                    st.error(f"Ticker '{ticker}' không tồn tại! Vui lòng nhập lại")
                    st.stop()
                else:
                    st.error(f"Ticker '{ticker}' không đầy đủ dữ liệu! Vui lòng nhập lại")
                    st.stop()
            e = TTM['Total Revenue'] / TTM_bsheet['Total Assets']
            altmanz_score = 1.2 * a + 1.4 * b + 3.3 * c + 0.6 * d + e

            # Piotroski F-Score
            # Score #1 - ROA
            roa_score = 1 if TTM['Net Income'] > 0 else 0

            # Score #2 - Operating Cash Flow
            ocf_score = 1 if TTM_cfs['Operating Cash Flow'] > 0 else 0

            # Score #3 - change in ROA
            roa_1 = TTM['Net Income'] / TTM_bsheet2['Total Assets']
            roa_2 = income[years_val[1 - len(years_val)]]['Net Income'] / bsheet[years_val[2 - len(years_val)]]['Total Assets']
            croa_score = 1 if roa_1 > roa_2 else 0

            # Score #4 - Quality of Earnings (Accrual)
            acc_score = 1 if TTM_cfs['Operating Cash Flow'] > TTM['Net Income'] else 0

            # Score #5 - Leverage (long term debt/average total assets) (Moi lay 2 quy gan nhat 2022, yf khum co)
            t_assets = quarter_bsheet.sum(axis=1)
            ave_assets = t_assets / 5
            lv_1 = TTM_bsheet['Long Term Debt And Capital Lease Obligation'] / ave_assets[
                'Total Assets'] if 'Long Term Debt And Capital Lease Obligation' in TTM_bsheet else 0
            pre_assets = 1 / 2 * (bsheet[years_val[1 - len(years_val)]]['Total Assets'] + TTM_bsheet4['Total Assets'])
            lv_2 = TTM_bsheet4[
                    'Long Term Debt And Capital Lease Obligation'] / pre_assets if 'Long Term Debt And Capital Lease Obligation' in TTM_bsheet4 else 0
            lv_score = 0 if lv_1 > lv_2 else 1

            # Score #6 - change in Working Capital (Liquidity)
            cr_1 = TTM_bsheet['Current Assets'] / TTM_bsheet['Current Liabilities']
            cr_2 = bsheet[years_val[1 - len(years_val)]]['Current Assets'] / bsheet[years_val[1 - len(years_val)]][
                'Current Liabilities']
            cr_score = 1 if cr_1 > cr_2 else 0

            # Score #7 - change in Share Issued
            si_score = 0 if TTM_bsheet['Share Issued'] > bsheet[years_val[1 - len(years_val)]]['Share Issued'] else 1

            # Score #8 - change in Gross Margin
            gm_1 = TTM['Gross Profit'] / TTM['Total Revenue']
            gm_2 = income[years_val[1 - len(years_val)]]['Gross Profit'] / income[years_val[1 - len(years_val)]]['Total Revenue']
            gm_score = 1 if gm_1 > gm_2 else 0

            # Score #9 - change in Asset Turnover
            at_1 = TTM['Total Revenue'] / TTM_bsheet2['Total Assets']
            at_2 = income[years_val[1 - len(years_val)]]['Total Revenue'] / bsheet[years_val[2 - len(years_val)]]['Total Assets']
            at_score = 1 if at_1 > at_2 else 0

            piotroski = at_score + gm_score + si_score + cr_score + acc_score + lv_score + croa_score + roa_score + ocf_score

            # Tính điểm cho guru
            liquidity_score = round(
                (cr_ratio_p + qr_ratio_p + car_ratio_p + dio_ratio_p + dso_ratio_p + dp_ratio_p) * 10 / (
                            cr_len + qr_len + car_len + dio_len + dso_len + dp_len), 0)
            profitability_score = round((
                                                gr_margin_p + op_margin_p + net_margin_p + fcf_margin_p + roe_margin_p + roa_margin_p + roc_margin_p + roce_margin_p) * 10 / (
                                                gr_margin_len + op_margin_len + net_margin_len + fcf_margin_len + roe_margin_len + roa_margin_len + roc_margin_len + roce_margin_len),
                                        0)

            gfvalues_score = round((
                                            PE_ratio_p + PS_ratio_p + PB_ratio_p + Price_to_TBV_p + price_to_FCF_p + EV_to_EBIT_p + EV_to_EBITDA_p + EV_to_Revenue_p + EV_to_FCF_p + Price_to_Net_CAV_p + EarningsYields_p + FCFYield_p) * 10 / (
                                            PE_ratio_len + PS_ratio_len + PB_ratio_len + Price_to_TBV_len + price_to_FCF_len + EV_to_EBIT_len + EV_to_EBITDA_len + EV_to_Revenue_len + EV_to_FCF_len + Price_to_Net_CAV_len + EarningsYields_len + FCFYield_len),
                                0)
            financial_score = round(
                (cash_debt_p + equity_asset_p + debt_equity_p + debt_ebitda_p + interest_coverage_p) * 10 / (
                            cash_debt_len + equity_asset_len + debt_equity_len + debt_ebitda_len + interest_coverage_len),
                0)

            col1, col2 = st.columns(2)
            with col1:

                st.subheader('Profitability Rank: ' + str(profitability_score) + '/' + '10')
                data_profitability = pd.DataFrame(
                    {
                        "STT": [1, 2, 3, 4, 5, 6, 7, 8],
                        "Index": ['	Gross Margin %', '	Operating Margin %', '	Net Margin %',
                                '	FCF Margin %',
                                '	ROE %',
                                '	ROA %', '	ROC (Joel Greenblatt) %', '	ROCE %'],
                        "-": [gr_margin_list, op_margin_list, net_margin_list, fcf_margin_list, roe_margin_list,
                            roa_margin_list,
                            roc_margin_list, roce_margin_list],
                        "Current": [gr_margin, op_margin, net_margin, fcf_margin, roe_margin, roa_margin,
                                    roc_margin,
                                    roce_margin],
                        "Vs History": [gr_margin_values, op_margin_values, net_margin_values, fcf_margin_values,
                                    roe_margin_values, roa_margin_values,
                                    roc_margin_values, roce_margin_values],
                    }
                )
                st.data_editor(
                    data_profitability,
                    column_config={
                        "-": st.column_config.BarChartColumn(
                            "-", width="small",
                        ),
                        "Vs History": st.column_config.ProgressColumn(
                            "Vs History",
                        ),
                    },
                    hide_index=True,
                )
                st.subheader('Financial Strength: ' + str(financial_score) + '/' + '10')
                        
                data_financial = pd.DataFrame(
                    {
                        "STT": [1, 2, 3, 4, 5],
                        "Index": ['Cash to Debt', 'Equity to Assets', 'Debt to Equity', 'Debt to EBITDA',
                                'Interest Coverage'],
                        "-": [cash_debt_list, equity_asset_list, debt_equity_list, debt_ebitda_list,
                            interest_coverage_list],
                        "Current": [cash_debt, equity_asset, debt_equity, debt_ebitda, interest_coverage],
                        "Vs History": [cash_debt_values, equity_asset_values, debt_equity_values,
                                    debt_ebitda_values, interest_coverage_values],
                    }
                )
                st.data_editor(
                    data_financial,
                    column_config={
                        "-": st.column_config.BarChartColumn(
                            "-", width="small",
                        ),
                        "Vs History": st.column_config.ProgressColumn(
                            "Vs History",
                        ),
                    },
                    hide_index=True,
                )

                st.subheader('Score')

                # Beneish M-Score
                # Day Sales in Receivables Index
                if 'Receivables' in TTM_bsheet:
                    t1 = TTM_bsheet['Receivables']/TTM['Total Revenue'] 
                    pre_t1 = bsheet[years_val[1-len(years_val)]]['Receivables']/income[years_val[1-len(years_val)]]['Total Revenue'] if 'Receivables' in TTM_bsheet else 0
                    dsri = t1 / pre_t1
                else: dsri = 0
                # Gross Margin Index
                t2 = TTM['Gross Profit'] / TTM['Total Revenue'] #is gm_1 and gm_2
                pre_t2 = income[years_val[1-len(years_val)]]['Gross Profit'] / income[years_val[1-len(years_val)]]['Total Revenue']
                gmi = pre_t2/t2
                # Asset Quality Index
                t3 = 1 - TTM_bsheet['Current Assets'] + TTM_bsheet['Net PPE']
                pre_t3 = 1 - bsheet[years_val[1-len(years_val)]]['Current Assets'] + bsheet[years_val[1-len(years_val)]]['Net PPE']
                aqi = t3/pre_t3
                # Sales Growth Index
                t4 = TTM['Total Revenue']
                pre_t4 = income[years_val[1-len(years_val)]]['Total Revenue']
                sgi = t4/pre_t4
                # Sales, General & Administrative expense index
                t5 = TTM['Selling General And Administration']/TTM['Total Revenue']
                pre_t5 = income[years_val[1-len(years_val)]]['Selling General And Administration']/income[years_val[1-len(years_val)]]['Total Revenue']
                sgai = t5/pre_t5
                # Depreciation Index
                if 'Depreciation Amortization Depletion' in cfs:
                    t6 = TTM_cfs['Depreciation Amortization Depletion']/(TTM_cfs['Depreciation Amortization Depletion']+TTM_bsheet['Net PPE'])
                    pre_t6 = cfs[years_val[1-len(years_val)]]['Depreciation Amortization Depletion']/(cfs[years_val[1-len(years_val)]]['Depreciation Amortization Depletion']+bsheet[years_val[1-len(years_val)]]['Net PPE'])
                    depi = pre_t6/t6
                else: depi = 0
                # leverage Index
                if 'Long Term Debt' in bsheet:
                    t7 = (TTM_bsheet['Long Term Debt'] + TTM_bsheet['Current Liabilities'])/TTM_bsheet['Total Assets']
                    pre_t7 = (bsheet[years_val[1-len(years_val)]]['Long Term Debt'] + bsheet[years_val[1-len(years_val)]]['Current Liabilities'])/bsheet[years_val[1-len(years_val)]]['Total Assets']
                    lvgi = t7/pre_t7
                else: lvgi = 0
                # Total Accruals to Total Assets
                tata = (TTM['Net Income Continuous Operations']-TTM_cfs['Operating Cash Flow'])/TTM_bsheet['Total Assets']
                
                m = -4.84 + 0.92 * dsri + 0.52 * gmi + 0.404 * aqi + 0.892 * sgi + 0.115 * depi - 0.172 * sgai + 4.679 * tata - 0.327 * lvgi

                #roic
                invest_cap_dec = TTM_bsheet['Total Assets'] - TTM_bsheet['Payables And Accrued Expenses'] - (TTM_bsheet['Cash Cash Equivalents And Short Term Investments'] 
                                - max(0,(TTM_bsheet['Current Liabilities'] - TTM_bsheet['Current Assets'] + TTM_bsheet['Cash Cash Equivalents And Short Term Investments']))) if 'Payables And Accrued Expenses' in TTM_bsheet else TTM_bsheet['Total Assets'] - (TTM_bsheet['Cash Cash Equivalents And Short Term Investments'] 
                                - max(0,(TTM_bsheet['Current Liabilities'] - TTM_bsheet['Current Assets'] + TTM_bsheet['Cash Cash Equivalents And Short Term Investments'])))
                invest_cap_sep = TTM_bsheet2['Total Assets'] - TTM_bsheet2['Payables And Accrued Expenses'] - (TTM_bsheet2['Cash Cash Equivalents And Short Term Investments'] 
                                - max(0,(TTM_bsheet2['Current Liabilities'] - TTM_bsheet2['Current Assets'] + TTM_bsheet2['Cash Cash Equivalents And Short Term Investments']))) if 'Payables And Accrued Expenses' in TTM_bsheet2 else TTM_bsheet2['Total Assets'] - (TTM_bsheet2['Cash Cash Equivalents And Short Term Investments'] 
                                - max(0,(TTM_bsheet2['Current Liabilities'] - TTM_bsheet2['Current Assets'] + TTM_bsheet2['Cash Cash Equivalents And Short Term Investments'])))
                roic = TTM['Operating Income'] * (1-tax_rate) / (1/2 * (invest_cap_dec + invest_cap_sep)) 

                data_score = pd.DataFrame(
                    {
                        "STT": [1, 2, 3, 4, 5],
                        "Index": ['Altman Z-Score', 'Beneish M-Score', 'Piotroski F-Score (Scale of 9)','WACC','ROIC'],
                        "Value": [altmanz_score, m, piotroski, wacc, roic],
                    }
                )
                st.data_editor(data_score, hide_index=True)

                st.write('Conclusion: ')
                if altmanz_score <=1.81:
                    st.write('1. Altman Z-Score = ' + str(round(altmanz_score,2)) + ': Distress Zone - High Likelihood of Bankruptcy')
                elif 1.81 < altmanz_score <2.99:
                    st.write('1. Altman Z-Score = ' + str(round(altmanz_score,2)) + ':  Grey - Moderate Likelihood of Bankruptcy')
                else:
                    st.write('1. Altman Z-Score = ' + str(round(altmanz_score,2)) + ': Safe Zone - Low Likelihood of Bankruptcy')
                
                if m <=-1.78:
                    st.write('2. Beneish M-Score = ' + str(round(m,2)) + ': Unlikely to be a manipulator')
                else:
                    st.write('2. Beneish M-Score = ' + str(round(m,2)) + ': Likely to be a manipulator')

            with col2:
                st.subheader('Liquidity Ratio: ' + str(liquidity_score) + '/' + '10')
                data_liquidity = pd.DataFrame(
                    {
                        "STT": [1, 2, 3, 4, 5, 6],
                        "Index": ['Current Ratio', 'Quick Ratio', 'Cash Ratio', 'Days Inventory',
                                'Days Sales Outstanding',
                                'Days Payable'],
                        "-": [cr_list, qr_list, car_list, dio_list, dso_list, dp_list],
                        "Current": [cr_ratio, qr_ratio, car_ratio, dio_ratio, dso_ratio, dp_ratio],
                        "Vs History": [cr_values2, qr_values, car_values, dio_values, dso_values, dp_values],
                    }
                )
                st.data_editor(
                    data_liquidity,
                    column_config={
                        "-": st.column_config.BarChartColumn(
                            "-", width="small",
                        ),
                        "Vs History": st.column_config.ProgressColumn(
                            "Vs History",
                        ),
                    },
                    hide_index=True,
                )
                st.subheader('GF Values')


                data_GF_Value = pd.DataFrame(
                    {
                        "STT": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                        "Index": ['PE Ratio', 'PS Ratio', 'PB Ratio', 'Price-to-tangible-book Ratio',
                                'Price-to-Free-Cash_Flow Ratio',
                                'EV-to-EBIT', 'EV-to-EBITDA', 'EV-to-Revenue', 'EV-to-FCF',
                                'Price-to-Net-Current-Asset-Value', 'Earnings Yields (Greenblatt) %',
                                'FCF Yield %'],
                        "Current": [PE_ratio, PS_ratio, PB_ratio, Price_to_TBV, price_to_FCF, EV_to_EBIT,
                                    EV_to_EBITDA,
                                    EV_to_Revenue, EV_to_FCF, Price_to_Net_CAV, EarningsYields, FCFYield],
                    },
                )
                st.data_editor(
                    data_GF_Value,
                    hide_index=True,
                )

                st.subheader('Dividend & Buy Back')
                data_dividend = pd.DataFrame(
                    {
                        "STT": [1, 2, 3, 4],
                        "Index": ['Dividend Yield', 'Dividend Payout Ratio', '5-Year Yield-on-Cost',
                                'Forward Dividend Yield'],
                        "Current": [div_ratio, pr_ratio, five_years_ratio, forward_ratio],
                    }
                )

                # Hiển thị DataFrame đã chỉnh sửa trong st.data_editor
                st.data_editor(data_dividend, hide_index=True)

            # Revenue, Net Income, EBITDA
            col9, col10 = st.columns(2)
            with col9:

                datav = {
                    'Time': [year.date().strftime("%Y-%m-%d") for year in years_val[::-1]] + ['TTM'],
                    'Revenue': [income.loc['Total Revenue', year] for year in years_val[::-1]] + [
                        TTM['Total Revenue']],
                    'Net Income': [income.loc['Net Income', year] for year in years_val[::-1]] + [
                        TTM['Net Income']],
                    'Free Cash Flow': [cfs.loc['Free Cash Flow', year] for year in years_val[::-1]] + [
                        TTM_cfs['Free Cash Flow']],
                    'Operating Cash Flow': [cfs.loc['Operating Cash Flow', year] for year in years_val[::-1]] + [
                        TTM_cfs['Operating Cash Flow']],
                    'ROE': [income.loc['Net Income', year] / (
                            bsheet.loc['Total Equity Gross Minority Interest', year] or 1)
                            for
                            year in years_val[::-1]] + [
                            TTM['Net Income'] / TTM_bsheet['Total Equity Gross Minority Interest']],
                    'EPS': [income.loc['Net Income', year] / (fast_info['shares'] or 1) for year in
                            years_val[::-1]] + [
                            TTM['Basic EPS']],
                    'Current Ratio': [bsheet.loc['Current Assets', year] / (
                            bsheet.loc['Current Liabilities', year] or 1)
                                    for
                                    year in years_val[::-1]] + [
                                        TTM_bsheet['Current Assets'] / TTM_bsheet['Current Liabilities']],
                    'Debt to Equity Ratio': [bsheet.loc['Total Debt', year] / (
                            bsheet.loc['Total Equity Gross Minority Interest', year] or 1) for year in
                                            years_val[::-1]] + [
                                                TTM_bsheet['Total Debt'] / TTM_bsheet[
                                                    'Total Equity Gross Minority Interest']],
                    'Accounts Receivable': [bsheet.loc['Accounts Receivable', year] for year in years_val[::-1]] + [
                        TTM_bsheet['Accounts Receivable']],
                    'EBITDA': [income.loc['EBITDA', year] for year in years_val[::-1]] + [TTM['EBITDA']],
                    'Cash': [bsheet.loc['Cash Cash Equivalents And Short Term Investments', year] for year in
                            years_val[::-1]] + [TTM_bsheet['Cash Cash Equivalents And Short Term Investments']],
                    'Debt': [bsheet.loc['Total Debt', year] for year in years_val[::-1]] + [TTM_bsheet['Total Debt']],
                    'Stockholders Equity': [bsheet.loc['Stockholders Equity', year] for year in years_val[::-1]] + [
                        TTM_bsheet['Stockholders Equity']],
                    'Total Assets': [bsheet.loc['Total Assets', year] for year in years_val[::-1]] + [
                        TTM_bsheet['Total Assets']],
                    'Stock Based Compensation': [cfs.loc['Stock Based Compensation', year] for year in years_val[::-1]] + [
                        TTM_cfs['Stock Based Compensation']] if 'Stock Based Compensation' in cfs else 0,
                    'Cash Flow for Dividends': [cfs.loc['Cash Dividends Paid', year] for year in years_val[::-1]] + [
                        TTM_cfs['Cash Dividends Paid']] if 'Cash Dividend Paid' in cfs else 0,
                    'Capital Expenditure': [cfs.loc['Capital Expenditure', year] for year in years_val[::-1]] + [
                        TTM_cfs['Capital Expenditure']] if 'Capital Expenditure' in TTM_cfs else 0
                }

                dfv = pd.DataFrame(datav)
                # print(dfv['Cash'])
                # print(dfv['Debt'])

                # Cash-debt
                columns_to_plot2 = ['Cash', 'Debt']
                x = ['['] + dfv['Time'] + [']']
                # Plot grouped bar chart
                fig = px.bar(dfv, x, y=columns_to_plot2,
                            labels={'value': 'Value', 'variable': 'Legend'},
                            barmode='group')

                # Add text on top of each bar
                for col in columns_to_plot2:
                    new_values = dfv[col] / 1e9
                    fig.update_traces(text=new_values.apply(lambda x: f'{x:.2f}B'), textposition='outside',
                                    selector=dict(name=col))
                fig.update_xaxes(fixedrange=True, title_text='')
                fig.update_yaxes(fixedrange=True, title_text="")
                fig.update_layout(legend_title_text=None)
                fig.update_layout(legend=dict(orientation='h', x=0.5, y=1.2), width=500, height=400)

                # Display the chart in Streamlit app
                st.plotly_chart(fig)

                # Stockholders equity vs total asset
                columns_to_plot3 = ['Stockholders Equity', 'Total Assets']
                x = ['['] + dfv['Time'] + [']']
                # Plot grouped bar chart
                fig = px.bar(dfv, x, y=columns_to_plot3,
                            labels={'value': 'Value', 'variable': 'Legend'},
                            barmode='group')

                # Add text on top of each bar
                for col in columns_to_plot3:
                    new_values = dfv[col] / 1e9
                    fig.update_traces(text=new_values.apply(lambda x: f'{x:.2f}B'), textposition='outside',
                                    selector=dict(name=col))
                fig.update_xaxes(fixedrange=True, title_text='')
                fig.update_yaxes(fixedrange=True, title_text="")
                fig.update_layout(legend_title_text=None)
                fig.update_layout(legend=dict(orientation='h', x=0.5, y=1.2), width=520, height=400)
                # Display the chart in Streamlit app
                st.plotly_chart(fig)

            with col10:
                columns_to_plot1 = ['Revenue', 'Net Income', 'EBITDA']
                x = ['['] + dfv['Time'] + [']']
                # Plot grouped bar chart
                fig = px.bar(dfv, x, y=columns_to_plot1,
                            labels={'value': 'Value', 'variable': 'Legend'},
                            barmode='group')

                # Add text on top of each bar
                for col in columns_to_plot1:
                    new_values = dfv[col] / 1e9
                    fig.update_traces(text=new_values.apply(lambda x: f'{x:.2f}B'), textposition='outside',
                                    selector=dict(name=col))
                fig.update_xaxes(fixedrange=True, title_text='')
                fig.update_yaxes(fixedrange=True, title_text="")
                fig.update_layout(legend_title_text=None)
                fig.update_layout(width=600, height=400, legend=dict(orientation='h', x=0.5, y=1.2))
                # Display the chart in Streamlit app
                st.plotly_chart(fig)

                columns_to_plot4 = ['Operating Cash Flow', 'Free Cash Flow', 'Net Income',
                                    'Cash Flow for Dividends', 'Stock Based Compensation']
                x = ['['] + dfv['Time'] + [']']
                # Plot grouped bar chart
                fig = px.bar(dfv, x, y=columns_to_plot4,
                            labels={'value': 'Value', 'variable': 'Legend'},
                            barmode='group')

                # Add text on top of each bar
                for col in columns_to_plot4:
                    new_values = dfv[col] / 1e9
                    fig.update_traces(text=new_values.apply(lambda x: f'{x:.2f}B'), textposition='outside',
                                    selector=dict(name=col))
                fig.update_xaxes(fixedrange=True, title_text='')
                fig.update_yaxes(fixedrange=True, title_text="")
                fig.update_layout(legend=dict(orientation='h', y=1.35), width=600, height=400)
                fig.update_layout(legend_title_text=None)
                
                # Display the chart in Streamlit app
                st.plotly_chart(fig)

            # Revenue, Net Income, Operating Cash Flow
            
            columns_to_plot = ['Revenue', 'Net Income', 'Operating Cash Flow', 'Free Cash Flow', 'Capital Expenditure']
            x = ['['] + dfv['Time'] + [']']
            # Plot grouped bar chart
            fig = px.bar(dfv, x, y=columns_to_plot, title='Financial Ratios',
                        height=530, width=1100, barmode='group')

            # Add text on top of each bar
            for col in columns_to_plot:
                new_values = dfv[col] / 1e9
                fig.update_traces(text=new_values.apply(lambda x: f'{x:.2f}B'), textposition='outside',
                                selector=dict(name=col))
            fig.update_xaxes(fixedrange=True, title_text="Time")
            fig.update_layout(legend_title_text=None)
            fig.update_xaxes(fixedrange=True, title_text="")
            fig.update_yaxes(fixedrange=True, title_text="")
            # Display the chart in Streamlit app
            st.plotly_chart(fig)

            col3, col4 = st.columns(2)
            with col3:

                # EPS
                # Vẽ biểu đồ đường sử dụng Plotly Express
                dfv['EPS'] = dfv['EPS'].round(2)
                fig = px.line(dfv, x, y='EPS', title='EPS', markers='o', line_shape='spline', text='EPS')
                fig.update_traces(textposition='top center')
                fig.update_xaxes(fixedrange=True, title_text='')
                fig.update_yaxes(fixedrange=True, title_text="")
                # Thay đổi màu của đường
                fig.update_traces(line=dict(color='dodgerblue'))
                fig.update_layout(width=500, height=400)
                # Hiển thị biểu đồ trong ứng dụng Streamlit
                st.plotly_chart(fig)

                # ROE
                # Vẽ biểu đồ đường sử dụng Plotly Express
                dfv['ROE'] = dfv['ROE'].round(2)
                fig = px.line(dfv, x, y='ROE', title='ROE', markers='o', line_shape='spline', text='ROE')
                fig.update_traces(textposition='top center')
                fig.update_xaxes(fixedrange=True, title_text='')
                fig.update_yaxes(fixedrange=True, title_text="")
                # Thay đổi màu của đường
                fig.update_traces(line=dict(color='dodgerblue'))
                fig.update_layout(width=500, height=400)
                # Hiển thị biểu đồ trong ứng dụng Streamlit
                st.plotly_chart(fig)

            with col4:
                # Debt to Equity Ratio
                # Vẽ biểu đồ đường sử dụng Plotly Express
                dfv['Debt to Equity Ratio'] = dfv['Debt to Equity Ratio'].round(2)
                fig = px.line(dfv, x, y='Debt to Equity Ratio', title='Debt to Equity Ratio', markers='o',
                            line_shape='spline', text='Debt to Equity Ratio')
                fig.update_traces(textposition='top center')
                fig.update_xaxes(fixedrange=True, title_text='')
                fig.update_yaxes(fixedrange=True, title_text="")
                # Thay đổi màu của đường
                fig.update_traces(line=dict(color='dodgerblue'))
                fig.update_layout(width=500, height=400)
                # Hiển thị biểu đồ trong ứng dụng Streamlit
                st.plotly_chart(fig)

                # Current Ratio
                # Vẽ biểu đồ đường sử dụng Plotly Express
                dfv['Current Ratio'] = dfv['Current Ratio'].round(2)
                fig = px.line(dfv, x, y='Current Ratio', title='Current Ratio', markers='o', line_shape='spline',
                            text='Current Ratio')
                fig.update_traces(textposition='top center')
                fig.update_xaxes(fixedrange=True, title_text='')
                fig.update_yaxes(fixedrange=True, title_text="")
                # Thay đổi màu của đường
                fig.update_traces(line=dict(color='dodgerblue'))
                fig.update_layout(width=500, height=400)
                # Hiển thị biểu đồ trong ứng dụng Streamlit
                st.plotly_chart(fig)

elif page == "Trading Portfolio":
    print("RELOAD PAGE 2")
    st.markdown(
            """
            <h1 style='text-align: center;'>TỔNG QUAN</h1>
            """,
            unsafe_allow_html=True
        )

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    # Đường dẫn tới file JSON credentials
    CREDS_FILE = 'valuation-430503-780d52190443.json'

    # Kết nối với Google Sheets
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)

    # Lấy dữ liệu từ Google Sheets
    spreadsheet_id = '1_BTPaJtdmQSYeEYfneG34ldm5QXDi5rxP2ttt-UAnL4'
    sheet = client.open_by_key(spreadsheet_id)
    worksheet = sheet.worksheet('Danh mục lướt sóng')
    data = worksheet.get_all_values() 
    worksheet2 = sheet.worksheet('BDTS lướt sóng theo ngày')
    swing = worksheet2.get_all_values() 
    df_swing = pd.DataFrame(swing)
    # Chuyển dữ liệu thành DataFrame với tên cột là dòng 3
    df = pd.DataFrame(data)
    data_a = {
        'Cột 1': [df.iloc[2, 0], 'Tổng tài sản', df.iloc[9, 0] + " (" + df.iloc[9, 2] + ")", df.iloc[11, 0]],
        'Cột 2': [df.iloc[2, 1], df.iloc[6, 1], df.iloc[9, 1], df.iloc[11, 1]],
        'Cột 3': ['', '', df.iloc[10, 2], df.iloc[11, 2]],
    }
    data_b = {
        'Cột 1': [df.iloc[2, 4], 'Tổng tài sản', df.iloc[9, 4] + " (" + df.iloc[9, 6] + ")", df.iloc[11, 4]],
        'Cột 2': [df.iloc[2, 5], df.iloc[6, 5], df.iloc[9, 5], df.iloc[11, 5]],
        'Cột 3': ['', '', df.iloc[10, 6], df.iloc[11, 6]]
    }
    data3 = {
        'Cột 1': [df.iloc[2, 8] + " (" + df.iloc[6, 8] + ")", df.iloc[7, 8]],
        'Cột 2': ['Mức tăng trưởng', df.iloc[7, 10]],
        'Cột 3': [df.iloc[9, 8], df.iloc[9, 10]],
        'Cột 4': [df.iloc[10, 8], df.iloc[10, 10]],
        'Cột 5': [df.iloc[11, 8], df.iloc[11, 10]]
    }
    data4 = {
        'Cột 1': [df.iloc[23, 8], df.iloc[24, 8], df.iloc[25, 8], df.iloc[26, 8], df.iloc[27, 8], df.iloc[28, 8], df.iloc[29, 8]],
        'Cột 2': [df.iloc[23, 9], df.iloc[24, 9], df.iloc[25, 9], df.iloc[26, 9], df.iloc[27, 9], df.iloc[28, 9], df.iloc[29, 9]],
        'Cột 3': [df.iloc[23, 10], df.iloc[24, 10], df.iloc[25, 10], df.iloc[26, 10], df.iloc[27, 10], df.iloc[28, 10], df.iloc[29, 10]],
        'Cột 4': [df.iloc[23, 11], df.iloc[24, 11], df.iloc[25, 11], df.iloc[26, 11], df.iloc[27, 11], df.iloc[28, 11], df.iloc[29, 11]],
        'Cột 5': [df.iloc[23, 12], df.iloc[24, 12], df.iloc[25, 12], df.iloc[26, 12], df.iloc[27, 12], df.iloc[28, 12], df.iloc[29, 12]],
        'Cột 6': [df.iloc[23, 13], df.iloc[24, 13], df.iloc[25, 13], df.iloc[26, 13], df.iloc[27, 13], df.iloc[28, 13], df.iloc[29, 13]],
        'Cột 7': [df.iloc[23, 14], df.iloc[24, 14], df.iloc[25, 14], df.iloc[26, 14], df.iloc[27, 14], df.iloc[28, 14], df.iloc[29, 14]]
    }

    df_a = pd.DataFrame(data_a)
    df_b = pd.DataFrame(data_b)
    df3 = pd.DataFrame(data3)
    df4 = pd.DataFrame(data4)
    def style_dataframe(df):
        styled_df = df.style.applymap(lambda x: 'color: black; font-weight: bold', subset=['Cột 1'])
        styled_df.set_table_styles({
            'Cột 1': [{'selector': 'thead th', 'props': 'display: none;'}],
            'Cột 2': [{'selector': 'thead th', 'props': 'display: none;'}],
            'Cột 3': [{'selector': 'thead th', 'props': 'display: none;'}],
        })
        return styled_df.hide(axis='index').to_html()

    styled_dfa_html = style_dataframe(df_a)
    styled_dfb_html = style_dataframe(df_b)

    combined_html = f"""
    <div style="display: flex; justify-content: center; flex-direction: row;">
        <div style="margin-right: 20px;">{styled_dfa_html}</div>
        <div style="margin-left: 20px;">{styled_dfb_html}</div>
    </div>
    """
    # Display the combined HTML content in Streamlit
    st.write(combined_html, unsafe_allow_html=True)
    
    st.write("")
    st.write("")
    html3 = df3.to_html(index=False, header=False)
    html_3_centered = f"""
    <div style="display: flex; justify-content: center;">
        {html3}
    </div>
    """
    # Add CSS to change the color of the first row to green
    html_3_centered = html_3_centered.replace('<tr>', '<tr style="font-weight: bold; color: black;">', 1)

    # Display the HTML in Streamlit
    st.write(html_3_centered, unsafe_allow_html=True)
    st.markdown(
        """
        <h1 style='text-align: center;'>CƠ CẤU TỔNG TÀI SẢN HIỆN TẠI</h1>
        """,
        unsafe_allow_html=True
    )

    # Path to the service account JSON file
    SERVICE_ACCOUNT_FILE = 'valuation-430503-780d52190443.json'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def connect_to_google_sheets():
        # Authenticate using the service account JSON file
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )

        # Build the Google Sheets API service
        service = build('sheets', 'v4', credentials=credentials)

        return service
    col1, col2 = st.columns(2)
    with col1:    
        RANGE_NAME = 'Positions lướt sóng!A1:H20'
        def ve_hinh():
            sheets_service = connect_to_google_sheets()
            # Define the spreadsheet ID and range
            SPREADSHEET_ID = '1_BTPaJtdmQSYeEYfneG34ldm5QXDi5rxP2ttt-UAnL4'
            sheet = sheets_service.spreadsheets()
            result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
            values = result.get('values', [])
            return values

        def main():

            # Fetch data
            data = ve_hinh()
            pos = pd.DataFrame(data)
            labels = pos.iloc[2:5,0]
            val = [float(item.replace(',', '')) for item in pos.iloc[2:5,4]]
               # Create a pie chart
            fig = go.Figure(data=[go.Pie(labels=labels, values=val, 
                                        marker=dict(colors=['#34A853', '#EA4335', '#FBBC05']),
                                        textinfo='percent', insidetextorientation='radial')])

            # Update layout for title
            fig.update_layout(title_text='CƠ CẤU DANH MỤC', title_x=0.2)

            # Display the chart in Streamlit
            st.plotly_chart(fig)

        if __name__ == "__main__":
            main()
    with col2:
        RANGE_NAME = 'Danh mục lướt sóng!G11:G12'
        def ve_hinh():
            sheets_service = connect_to_google_sheets()
            # Define the spreadsheet ID and range
            SPREADSHEET_ID = '1_BTPaJtdmQSYeEYfneG34ldm5QXDi5rxP2ttt-UAnL4'
            sheet = sheets_service.spreadsheets()
            result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
            values = result.get('values', [])
            return values

        # Main Streamlit app
        def main():
            values = ve_hinh()
            
            # Extract the numeric values from the fetched data
            values = [float(value[0][:-1]) for value in values]

            # Define labels
            labels = ['Cổ phiếu', 'Tiền mặt']

            # Create a pie chart
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])

            # Update layout for title
            fig.update_layout(title_text='CƠ CẤU TÀI SẢN', title_x=0.2)

            # Display the chart in Streamlit
            st.plotly_chart(fig)

        if __name__ == "__main__":
            main()
    st.markdown("<h1 style='text-align: center; font-weight: bold; font-size: 24px;'>CHI TIẾT LÃI LỖ</h1>", unsafe_allow_html=True)

    html4 = df4.to_html(index=False, header=False)
    html_4_centered = f"""
    <div style="display: flex; justify-content: center;">
        {html4}
    </div>
    """
    # Add CSS to change the color of the first row to green
    html_4_centered = html_4_centered.replace('<tr>', '<tr style="font-weight: bold; color: black;">', 1)
    st.write(html_4_centered, unsafe_allow_html=True)
    colm, coln = st.columns(2)
    with colm:
        dates = pd.to_datetime(df_swing.iloc[4:16, 0])
        column_3 = df_swing.iloc[4:16, 3].str.rstrip('%').astype(float)
        column_5 = df_swing.iloc[4:16, 5].str.rstrip('%').astype(float)

        # Create the plotly chart
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=dates,
            y=column_3,
            mode='lines+markers',
            name='Thay đổi danh mục',
            marker=dict(symbol='circle')
        ))

        fig.add_trace(go.Scatter(
            x=dates,
            y=column_5,
            mode='lines+markers',
            name='VN-Index',
            marker=dict(symbol='circle')
        ))

        fig.update_layout(
            title='BIẾN ĐỘNG TÀI SẢN LƯỚT SÓNG THEO NGÀY',
            xaxis_title='Ngày',
        )

        # Display the plot in Streamlit
        st.plotly_chart(fig)
    with coln:
        worksheet_tra = sheet.worksheet('Positions lướt sóng')
        trading = worksheet_tra.get_all_values() 
        df_trading = pd.DataFrame(trading)
        maa = [item1 for item1 in df_trading.iloc[2:6, 0]]
        column4 = [item1 for item1 in df_trading.iloc[2:6, 6].str.rstrip('%').astype(float)]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=maa,
            y=column4,
            width=0.4, 
            marker_color=['#636EFA', '#EF553B', '#00CC96']  # Change column colors
        ))

        # Add data table as annotations
        annotations = []
        for i in range(len(maa)):
            annotations.append(
                dict(
                    x=maa[i],
                    y=column4[i] + 1,  # Position above the bar
                    text=f'{column4[i]:.2f}%',
                    showarrow=False,
                    font=dict(size=12, color='black')
                )
            )

        fig.update_layout(
            title='PORTFOLIO POSITIONS',
            xaxis_title='Tickers',
            yaxis_title='Values (%)',
            annotations=annotations
        )
        st.plotly_chart(fig)
    st.markdown("<h1 style='text-align: center; font-weight: bold; '>LỊCH SỬ LỆNH ĐÃ THỰC HIỆN</h1>", unsafe_allow_html=True)
    center_button_css = """
    <style>
    div.stButton > button {
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
    """

    # Apply the CSS
    st.markdown(center_button_css, unsafe_allow_html=True)
    if st.button("▼", key="button5"):
        worksheet3 = sheet.worksheet('Lệnh')
        swing1 = worksheet3.get_all_values() 
        df_swing1 = pd.DataFrame(swing1)
        df_fina = df_swing1.iloc[3:17, 0:13]

        html_fina = df_fina.to_html(index=False, header=False)
        html_fina_centered = f"""
        <div style="display: flex; justify-content: center;">
            {html_fina}
        </div>
        """
        # Add CSS to change the color of the first row to green
        html_fina_centered = html_fina_centered.replace('<tr>', '<tr style="font-weight: bold; color: black;">', 1)

        # Display the HTML in Streamlit
        st.write(html_fina_centered, unsafe_allow_html=True)

elif page == "Investing Portfolio":
    print("RELOAD PAGE 3")
    st.markdown(
            """
            <h1 style='text-align: center;'>TỔNG QUAN</h1>
            """,
            unsafe_allow_html=True
        )

    # Định nghĩa phạm vi của Google Sheets API
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    # Đường dẫn tới file JSON credentials
    CREDS_FILE = 'valuation-430503-780d52190443.json'

    # Kết nối với Google Sheets
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)

    # Lấy dữ liệu từ Google Sheets
    spreadsheet_id = '1_BTPaJtdmQSYeEYfneG34ldm5QXDi5rxP2ttt-UAnL4'
    sheet = client.open_by_key(spreadsheet_id)
    worksheet = sheet.worksheet('Danh mục đầu tư')
    data = worksheet.get_all_values() 

    worksheet2 = sheet.worksheet('BDTS đầu tư theo ngày')
    invest = worksheet2.get_all_values() 
    df_invest = pd.DataFrame(invest)
    # Chuyển dữ liệu thành DataFrame với tên cột là dòng 3
    df = pd.DataFrame(data)

    data_a = {
        'Cột 1': [df.iloc[2, 0], 'Tổng tài sản', df.iloc[9, 0] + " (" + df.iloc[9, 2] + ")", df.iloc[11, 0]],
        'Cột 2': [df.iloc[2, 1], df.iloc[6, 1], df.iloc[9, 1], df.iloc[11, 1]],
        'Cột 3': ['', '', df.iloc[10, 2], df.iloc[11, 2]],
    }
    data_b = {
        'Cột 1': [df.iloc[2, 4], 'Tổng tài sản', df.iloc[9, 4] + " (" + df.iloc[9, 6] + ")", df.iloc[11, 4]],
        'Cột 2': [df.iloc[2, 5], df.iloc[6, 5], df.iloc[9, 5], df.iloc[11, 5]],
        'Cột 3': ['', '', df.iloc[10, 6], df.iloc[11, 6]]
    }
    data3 = {
        'Cột 1': [df.iloc[2, 8] + " (" + df.iloc[6, 8] + ")", df.iloc[7, 8]],
        'Cột 2': ['Mức tăng trưởng', df.iloc[7, 10]],
        'Cột 3': [df.iloc[9, 8], df.iloc[9, 10]],
        'Cột 4': [df.iloc[10, 8], df.iloc[10, 10]],
        'Cột 5': [df.iloc[11, 8], df.iloc[11, 10]]
    }
    data4 = {
        'Cột 1': [df.iloc[23, 8], df.iloc[24, 8], df.iloc[25, 8], df.iloc[26, 8], df.iloc[27, 8]],
        'Cột 2': [df.iloc[23, 9], df.iloc[24, 9], df.iloc[25, 9], df.iloc[26, 9], df.iloc[27, 9]],
        'Cột 3': [df.iloc[23, 10], df.iloc[24, 10], df.iloc[25, 10], df.iloc[26, 10], df.iloc[27, 10]],
        'Cột 4': [df.iloc[23, 11], df.iloc[24, 11], df.iloc[25, 11], df.iloc[26, 11], df.iloc[27, 11]],
        'Cột 5': [df.iloc[23, 12], df.iloc[24, 12], df.iloc[25, 12], df.iloc[26, 12], df.iloc[27, 12]],
        'Cột 6': [df.iloc[23, 13], df.iloc[24, 13], df.iloc[25, 13], df.iloc[26, 13], df.iloc[27, 13]],
        'Cột 7': [df.iloc[23, 14], df.iloc[24, 14], df.iloc[25, 14], df.iloc[26, 14], df.iloc[27, 14]]
    }

    df_a = pd.DataFrame(data_a)
    df_b = pd.DataFrame(data_b)
    df3 = pd.DataFrame(data3)
    df4 = pd.DataFrame(data4)
    def style_dataframe(df):
        styled_df = df.style.applymap(lambda x: 'color: black; font-weight: bold', subset=['Cột 1'])
        styled_df.set_table_styles({
            'Cột 1': [{'selector': 'thead th', 'props': 'display: none;'}],
            'Cột 2': [{'selector': 'thead th', 'props': 'display: none;'}],
            'Cột 3': [{'selector': 'thead th', 'props': 'display: none;'}],
        })
        return styled_df.hide(axis='index').to_html()

    styled_dfa_html = style_dataframe(df_a)
    styled_dfb_html = style_dataframe(df_b)

    combined_html = f"""
    <div style="display: flex; justify-content: center; flex-direction: row;">
        <div style="margin-right: 20px;">{styled_dfa_html}</div>
        <div style="margin-left: 20px;">{styled_dfb_html}</div>
    </div>
    """
    # Display the combined HTML content in Streamlit
    st.write(combined_html, unsafe_allow_html=True)
    
    st.write("")
    st.write("")
    html3 = df3.to_html(index=False, header=False)
    html_3_centered = f"""
    <div style="display: flex; justify-content: center;">
        {html3}
    </div>
    """
    # Add CSS to change the color of the first row to green
    html_3_centered = html_3_centered.replace('<tr>', '<tr style="font-weight: bold; color: black;">', 1)

    # Display the HTML in Streamlit
    st.write(html_3_centered, unsafe_allow_html=True)

    st.markdown(
        """
        <h1 style='text-align: center;'>CƠ CẤU TỔNG TÀI SẢN HIỆN TẠI</h1>
        """,
        unsafe_allow_html=True
    )
    # Path to the service account JSON file
    SERVICE_ACCOUNT_FILE = 'valuation-430503-780d52190443.json'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


    def connect_to_google_sheets():
        # Authenticate using the service account JSON file
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )

        # Build the Google Sheets API service
        service = build('sheets', 'v4', credentials=credentials)

        return service
    col1, col2 = st.columns(2)
    with col1:    
        RANGE_NAME = 'Danh mục đầu tư!J25:O28'
        def ve_hinh():
            sheets_service = connect_to_google_sheets()
            # Define the spreadsheet ID and range
            SPREADSHEET_ID = '1_BTPaJtdmQSYeEYfneG34ldm5QXDi5rxP2ttt-UAnL4'
            sheet = sheets_service.spreadsheets()
            result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
            values = result.get('values', [])
            return values

        def main():

            # Fetch data
            data = ve_hinh()
            # Extract the numeric values from the fetched data
            value1 = [float(item[0]) * float(item[1]) for item in data]
            total = sum(value1)
            val = []
            for value in value1:
                if value > 0:
                    percentage = round((value / total) * 100, 2)
                    val.append(percentage)
                else:
                    percentage = 0


            labels = ['SSI', 'MBB', 'FPT', 'SAB']


            # Create a pie chart
            fig = go.Figure(data=[go.Pie(labels=labels, values=val, 
                                        marker=dict(colors=['#4285F4', '#EA4335', '#FBBC05', '#34A853']),
                                        textinfo='percent', insidetextorientation='radial')])

            # Update layout for title
            fig.update_layout(title_text='CƠ CẤU DANH MỤC', title_x=0.2)

            # Display the chart in Streamlit
            st.plotly_chart(fig)

        if __name__ == "__main__":
            main()
    with col2:
        RANGE_NAME = 'Danh mục đầu tư!G11:G12'
        def ve_hinh():
            sheets_service = connect_to_google_sheets()
            # Define the spreadsheet ID and range
            SPREADSHEET_ID = '1_BTPaJtdmQSYeEYfneG34ldm5QXDi5rxP2ttt-UAnL4'
            sheet = sheets_service.spreadsheets()
            result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
            values = result.get('values', [])
            return values

        # Main Streamlit app
        def main():
            values = ve_hinh()
            
            # Extract the numeric values from the fetched data
            values = [float(value[0][:-1]) for value in values]

            # Define labels
            labels = ['Cổ phiếu', 'Tiền mặt']

            # Create a pie chart
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])

            # Update layout for title
            fig.update_layout(title_text='CƠ CẤU TÀI SẢN', title_x=0.2)

            # Display the chart in Streamlit
            st.plotly_chart(fig)

        if __name__ == "__main__":
            main()
    st.markdown("<h1 style='text-align: center; font-weight: bold; font-size: 24px;'>CHI TIẾT LÃI LỖ</h1>", unsafe_allow_html=True)
    html4 = df4.to_html(index=False, header=False)
    html_4_centered = f"""
    <div style="display: flex; justify-content: center;">
        {html4}
    </div>
    """
    # Add CSS to change the color of the first row to green
    html_4_centered = html_4_centered.replace('<tr>', '<tr style="font-weight: bold; color: black;">', 1)
    st.write(html_4_centered, unsafe_allow_html=True)
    colx,coly = st.columns(2)
    with colx:
        dates = pd.to_datetime(df_invest.iloc[4:16, 0])
        column_3 = df_invest.iloc[4:16, 3].str.rstrip('%').astype(float)
        column_5 = df_invest.iloc[4:16, 5].str.rstrip('%').astype(float)

        # Create the plotly chart
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=dates,
            y=column_3,
            mode='lines+markers',
            name='Thay đổi danh mục',
            marker=dict(symbol='circle')
        ))

        fig.add_trace(go.Scatter(
            x=dates,
            y=column_5,
            mode='lines+markers',
            name='VN-Index',
            marker=dict(symbol='circle')
        ))

        fig.update_layout(
            title='BIẾN ĐỘNG TÀI SẢN ĐẦU TƯ THEO NGÀY',
            xaxis_title='Ngày',
        )

        # Display the plot in Streamlit
        st.plotly_chart(fig)
    with coly:

        # Chart
        worksheet_tra = sheet.worksheet('Positions đầu tư')
        trading = worksheet_tra.get_all_values() 
        df_trading = pd.DataFrame(trading)
        maa = [item1 for item1 in df_trading.iloc[2:6, 0]]
        column4 = [item1 for item1 in df_trading.iloc[2:6, 6].str.rstrip('%').astype(float)]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=maa,
            y=column4,
            width=0.4, 
            marker_color=['#636EFA', '#EF553B', '#00CC96', '#AB63FA']  # Change column colors
        ))

        # Add data table as annotations
        annotations = []
        for i in range(len(maa)):
            annotations.append(
                dict(
                    x=maa[i],
                    y=column4[i] + 1,  # Position above the bar
                    text=f'{column4[i]:.2f}%',
                    showarrow=False,
                    font=dict(size=12, color='black')
                )
            )

        fig.update_layout(
            title='PORTFOLIO POSITIONS',
            xaxis_title='Tickers',
            yaxis_title='Values (%)',
            annotations=annotations
        )
        st.plotly_chart(fig)

    st.markdown("<h1 style='text-align: center; font-weight: bold; '>LỊCH SỬ LỆNH ĐÃ THỰC HIỆN</h1>", unsafe_allow_html=True)
    center_button_css = """
    <style>
    div.stButton > button {
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
    """

    # Apply the CSS
    st.markdown(center_button_css, unsafe_allow_html=True)
    if st.button("▼", key="button6"):
        worksheet3 = sheet.worksheet('History Đầu tư')
        swing1 = worksheet3.get_all_values() 
        df_swing1 = pd.DataFrame(swing1)

        df_fina1 = df_swing1.iloc[1:11, 0:6]
        df_fina2 = df_swing1.iloc[1:3, 7:13]
        col_ia, col_ib = st.columns(2)
        with col_ia:
            st.markdown("<h1 style='text-align: center; font-weight: bold; font-size: 24px;'>LỊCH SỬ GIAO DỊCH CHỨNG KHOÁN</h1>", unsafe_allow_html=True)
            
            html1 = df_fina1.to_html(index=False, header=False)

            # Add CSS to change the color of the first row to green
            html1 = html1.replace('<tr>', '<tr style="font-weight: bold; color: black;">', 1)

            # Display the HTML in Streamlit
            st.write(html1, unsafe_allow_html=True)
        with col_ib:
            st.markdown("<h1 style='text-align: center; font-weight: bold; font-size: 24px;'>LỊCH SỬ GIAO DỊCH TIỀN</h1>", unsafe_allow_html=True)
            html2 = df_fina2.to_html(index=False, header=False)

            # Add CSS to change the color of the first row to green
            html2 = html2.replace('<tr>', '<tr style="font-weight: bold; color: black;">', 1)

            # Display the HTML in Streamlit
            st.write(html2, unsafe_allow_html=True)

elif page == "Watchlist":
    print("RELOAD PAGE 4")
  
    st.markdown("<h1 style='text-align: center; font-weight: bold;'>WATCHLIST</h1>", unsafe_allow_html=True)
    csv_path ='ticker_data.csv'

    mh = pd.read_csv(csv_path)
    if mh.empty:
        st.info("Watchlist trống")
    else:
        ticker = mh.iloc[0,0]
        mh.fillna(' ', inplace=True)
        
        # Thêm cột xoá (checkbox)
        mh["❌ Xóa"] = False

        edited_df = st.data_editor(
            mh,
            hide_index=True,
            num_rows="dynamic",
            use_container_width=True,
        )

        # Tìm dòng bị tick xoá
        to_delete = edited_df[edited_df["❌ Xóa"]].index
        if len(to_delete) > 0:
            mh = mh.drop(to_delete).drop(columns=["❌ Xóa"])
            mh.to_csv(csv_path, index=False)
            st.success("✅ Đã xoá và cập nhật Watchlist!")
            st.rerun()

elif page == "Financial Freedom Calculator":
    print("RELOAD PAGE 5")
    st.markdown(
        """
        <h1 style='text-align: center;'>FINANCIAL FREEDOM CALCULATOR</h1>
        """,
        unsafe_allow_html=True
    )
    cl1, cl2 = st.columns(2)
    with cl1:
        cr = st.text_input("Current Age:", value=0, placeholder="Type a number...")
        cr_age = int(cr)
        ff = st.text_input("Financial Freedom Age:", value=0, placeholder="Type a number...")
        ff_age = int(ff)
        ffi = 0
        # formatted_fg = "{:,.2f}".format(ffi)
        # formatted_fg = float(ffi)
        fg_income = st.text_input("Financial Freedom Income per month:", value=ffi,
                                    placeholder="Type a number...")
        # ff_income = float(fg_income[1:].replace(',', ''))
        ff_income = float(fg_income)
        inf = st.text_input("Inflation Rate(%):", value=0, placeholder="Type a number...")
        infla = float(inf)
    with cl2:
        els = st.text_input("Estimated Life Span:", value=0, placeholder="Type a number...")
        est = int(els)
        cla = 0
        # formatted_cla = "{:,.2f}".format(cla)
        # formatted_cla = float(cla)
        cr_cla = st.text_input("Current Liquidity Asset:", value=cla,
                                    placeholder="Type a number...")
        # cr_li = float(cr_cla[1:].replace(',', ''))
        cr_li = float(cr_cla)
        rate = st.text_input("Rate of Return (Active) (%):", value=0, placeholder="Type a number...")
        rr_ac = float(rate)
        rr = st.text_input("Rate of Return (Passive) (%):", value=0, placeholder="Type a number...")
        rr_pa = float(rr)
        
    realr2 = (rr_pa-infla)/100
    realr1 = (rr_ac-infla)/100
    if ff_age == 0 or cr_age == 0 or rr_ac == 0 or rr_pa == 0:
        st.write("Please insert information")
    else:
        tt_saving = ff_income/(realr2/12) * (1-1/(1+realr2/12)**((est-ff_age)*12))
        an_saving = (tt_saving-cr_li*((1+realr1)**(ff_age-cr_age)))*(realr1)/((1+realr1)**(ff_age-cr_age) - 1)
        center_button_css = """
        <style>
        div.stButton > button {
            display: block;
            margin-left: auto;
            margin-right: auto;
        }
        </style>
        """
        # Apply the CSS
        st.markdown(center_button_css, unsafe_allow_html=True)
        if st.button('Solve'):
            st.write('Years to save to Financial Freedom: ', str(ff_age - cr_age), 'yrs')
            st.write('Total Savings needed for Financial Freedom:',  "${:,.2f}".format(tt_saving))
            st.write('Annual Savings needed to reach Financial Freedom:', "${:,.2f}".format(an_saving))

elif page == "Position Sizing Calculator":
    print("RELOAD PAGE 6")
    st.markdown(
        """
        <h1 style='text-align: center;'>POSITION SIZING CALCULATOR</h1>
        """,
        unsafe_allow_html=True
    )

    cl1, cl2, cl3 = st.columns(3)
    with cl1:
        cr_acc = 0
        formatted_acc = "${:,.2f}".format(cr_acc)
        accnt = st.text_input("Current Account Size:", value=formatted_acc,
                                    placeholder="Type a number...")
        c_acc = float(accnt[1:].replace(',', ''))
        risk2 = 0
        risk = st.text_input("Risk Per Trade(%):", value=risk2, placeholder="Type a number...")
        riskpt = float(risk)
    with cl2:
        en_p = 0
        formatted_enp = "${:,.2f}".format(en_p)
        en_pr = st.text_input("Entry Price:", value=formatted_enp,
                                    placeholder="Type a number...")
        ent_pr = float(en_pr[1:].replace(',', ''))
        stl = 0
        formatted_stl = "${:,.2f}".format(stl)
        stl_p = st.text_input("Stop Loss Price", value=formatted_stl,
                                    placeholder="Type a number...")
        stl_pr = float(stl_p[1:].replace(',', ''))
       
        tag = ent_pr + (ent_pr - stl_pr)*2
        formatted_tag = "${:,.2f}".format(tag)
        tag_p = st.text_input("Target Price", value=formatted_tag,
                                    placeholder="Type a number...")
        tag_pr = float(tag_p[1:].replace(',', ''))
    with cl3:
        pro = tag_pr - ent_pr
        formatted_pro = "${:,.2f}".format(pro)
        pro_sh = st.text_input("Profit Per Share:", value=formatted_pro,
                                    placeholder="Type a number...")
        pro_sha = float(pro_sh[1:].replace(',', ''))
        
        lss = ent_pr - stl_pr
        formatted_lss = "${:,.2f}".format(lss)
        lss_sh = st.text_input("Stop Loss Per Share", value=formatted_lss,
                                    placeholder="Type a number...")
        lss_sha = float(lss_sh[1:].replace(',', ''))
        if  lss_sha == 0:
            st.write("Please insert information")
        else:
            rate = st.text_input("Return/Risk ratio: (> 1)", value=pro_sha/lss_sha, placeholder="Type a number...")
            rr_ac = float(rate)
    
    if  lss_sha == 0 or c_acc == 0:
        st.write("Please insert information")
    else:
        nbs = (c_acc * riskpt/100)/lss_sha
        retu = (nbs*pro_sha)/c_acc
        center_button_css = """
        <style>
        div.stButton > button {
            display: block;
            margin-left: auto;
            margin-right: auto;
        }
        </style>
        """
        # Apply the CSS
        st.markdown(center_button_css, unsafe_allow_html=True)
        if st.button('Solve'):
            st.write('Number of Shares: ', "{:,.2f}".format(nbs))
            st.write('Return on Account Size:', "{:,.2f}%".format(retu*100))
elif page=="Chatbot":

    print("RELOAD PAGE Chatbot")

    # initialize chat session in streamlit if not already present
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # streamlit page title
    st.title("🤖 GPT-5 Mini - ChatBot")

    # display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


    # input field for user's message
    user_prompt = st.chat_input("Ask GPT-5...")

    if user_prompt:
        # add user's message to chat and display it
        st.chat_message("user").markdown(user_prompt)
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})

        # send user's message to GPT-4o and get a response
        with st.spinner("🤖 I am thinking..."):
            assistant_response = chatBot_answer(st)

        # display GPT-4o's response
        with st.chat_message("assistant"):
            st.markdown(assistant_response)
    # CSS cho chữ ở góc phải dưới
    corner_text = """
    <style>
    .corner-text {
    position: fixed;
    bottom: 10px;
    right: 20px;
    background: rgba(0,0,0,0.7);
    color: white;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 16px;
    z-index: 9999;
    }
    </style>

    <div class="corner-text">
    📢 Để được tư vấn trực tiếp liện hệ số điện thoại: 0972792882
    </div>
    """

    st.markdown(corner_text, unsafe_allow_html=True)


        