import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from selenium import webdriver
import time
from selenium.webdriver.chrome.options import Options
import streamlit as st

headers = { 
		'User-Agent'      : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
		# 'User-Agent'      : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
		'Accept'          : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 
		'Accept-Language' : 'en-US,en;q=0.5',
		'DNT'             : '1', # Do Not Track Request Header 
		'Connection'      : 'close'
	}

@st.cache_resource
def mck_info(ticker, headers = headers):
	ticker = ticker.upper()
	mck_info = dict()

	#summary
	url_summary = f'https://finance.yahoo.com/quote/{ticker}'

	response_summary = requests.get(url_summary, headers=headers)

	if response_summary.status_code == 200:
		soup = BeautifulSoup(response_summary.text, 'html.parser')

		#company name
		company_tag = soup.find('h1', class_='yf-4vbjci')
		company_name = company_tag.text
		mck_info['comp_name'] = company_name

		#beta value
		beta_tag = soup.find('span', title= 'Beta (5Y Monthly)')
		if beta_tag:
			next_span = beta_tag.find_next_sibling('span')
			if '--' in next_span.text:
				beta_value = 0
			else:
				beta_value = float(next_span.text)
			mck_info['beta']= beta_value

		# trailingAnnualDividendYield, HTML/Summary/Forward Dividend & Yield (/100)
		tADY_tag = soup.find('span', title= 'Forward Dividend & Yield')
		if tADY_tag:
			next_span = tADY_tag.find_next_sibling('span')
			if '--' in next_span.text:
				percentage = 0
			else:
				percent_str = next_span.text.split('(')[1].replace('%)', '')
				percentage = float(percent_str) / 100
			mck_info['trailingAnnualDividendYield']= percentage
	response_summary.close()

	#statistics
	url_statistics = f'https://finance.yahoo.com/quote/{ticker}/key-statistics/'

	response_statistics = requests.get(url_statistics, headers=headers)

	if response_statistics.status_code == 200:
		soup = BeautifulSoup(response_statistics.text, 'html.parser')

		for td in soup.find_all('td', class_='label yf-vaowmx'):
			#payoutRatio
			if 'Payout Ratio' in td.get_text(strip=True):
				next_td = td.find_next_sibling('td')
				if '--' in next_td.text:
					payoutRatio = 0
				else:
					payoutRatio = float(next_td.text.split('%')[0])/100
				mck_info['payoutRatio'] = payoutRatio
			#fiveYearAvgDividendYield
			elif '5 Year Average Dividend Yield' in td.get_text(strip=True):
				next_td = td.find_next_sibling('td')
				if '--' in next_td.text:
					fiveYearAvgDividendYield = 0
				else:
					fiveYearAvgDividendYield = float(next_td.text)
				mck_info['fiveYearAvgDividendYield'] = fiveYearAvgDividendYield
			elif 'Forward Annual Dividend Yield' in td.get_text(strip=True):
				next_td = td.find_next_sibling('td')
				if '--' in next_td.text:
					dividendYield = 0
				else:
					dividendYield = float(next_td.text.split('%')[0])
				mck_info['dividendYield'] = dividendYield
		for td in soup.find_all('td', class_='yf-kbx2lo'):
			if 'Market Cap' in td.get_text(strip=True):
				next_td = td.find_next_sibling('td')
				if '--' in next_td.text:
					marketCap = 0
				else:
					marketCap = float(next_td.text.split("T")[0])* 1000000000000
				mck_info['marketCap'] = marketCap
			if 'Trailing P/E' in td.get_text(strip=True):
				next_td = td.find_next_sibling('td')
				if '--' in next_td.text:
					trailingPE = 0
				else:
					trailingPE = float(next_td.text)
				mck_info['trailingPE'] = trailingPE
			elif 'Price/Book' in td.get_text(strip=True):
				next_td = td.find_next_sibling('td')
				if '--' in next_td.text:
					priceToBook = 0
				else:
					priceToBook = float(next_td.text)
				mck_info['priceToBook'] = priceToBook


	response_statistics.close()

	return mck_info

@st.cache_resource
def run_selenium(ticker, fullExchangeName: str):
	results = {}

	if ticker[-3:] != ".VN":
		urlAnalysis = f'https://fiscal.ai/company/{fullExchangeName}-{ticker}/'
	else:
		urlAnalysis = f'https://fiscal.ai/company/{fullExchangeName}-{ticker[:-3]}/'
	urlStatistics = f'https://finance.yahoo.com/quote/{ticker}/key-statistics?p={ticker}'


	urls = [urlAnalysis, urlStatistics]


	options = Options()
	options.add_argument("--headless")  
	options.add_argument("--disable-gpu")
	options.add_argument("--disable-dev-shm-usage")

	driver = webdriver.Chrome(options=options)
	
	for url in urls:
		driver.get(url)
		time.sleep(30)
		soup = BeautifulSoup(driver.page_source, "html.parser")
		if 'fiscal.ai' in url:
			for div in soup.find_all("div", class_="col-span-3 mb-4 inline-block w-full min-w-full"):
				h3 = div.find("h3")
				print(h3.get_text(strip=True))
				if h3 and "Growth (CAGR)" in h3.get_text(strip=True):
					target_div = div
					ul = target_div.find("ul")
					section = {}
					if ul:
						for li in ul.find_all("li"):
							ps = li.find_all("p")
							if len(ps) >= 2:
								key = ps[0].get_text(strip=True)
								value = ps[1].get_text(strip=True)
								section[key] = value
				else:
					continue
			results[url] = section
			print(f"Crawl Analysis Url: DONE + {type(section)}")
		elif 'statistics' in url:
			section = soup.find('section', attrs={'data-testid':'qsp-statistics'})
			print(f"Crawl Statistics Url: DONE + {type(section)}")
			results[url] = section
	driver.quit()
	return results

# @st.cache_resource
def analysis(ticker, rsSel, fullExchangeName: str):
	if ticker[-3:] != ".VN":
		urlAnalysis = f'https://fiscal.ai/company/{fullExchangeName}-{ticker}/'
	else:
		urlAnalysis = f'https://fiscal.ai/company/{fullExchangeName}-{ticker[:-3]}/'

	section = rsSel[urlAnalysis]
	print(type(section))
	if section == None:
		growth_rate1 = growth_rate2 = growth_rate3 = 1
	else:
		growth_rate1 = section.get("EPS LT Growth Est")
		if "—" in growth_rate1:
			growth_rate1 = 1
		else:
			growth_rate1 = float(growth_rate1.split("%")[0])
		if growth_rate1 >= 15:
			growth_rate2 = 15
		else:
			growth_rate2 = growth_rate1

		growth_rate3 = 4

	
	return growth_rate1, growth_rate2, growth_rate3

# @st.cache_resource
def discounted_Cash_Flow_Method_10_years(ticker, rsSel):
	urlStatistics = f'https://finance.yahoo.com/quote/{ticker}/key-statistics?p={ticker}'

	# response = requests.get(urlStatistics, headers=headers)
	# html_content = response.text

	# # Parse the HTML content
	# soup = BeautifulSoup(html_content, 'html.parser')
	soup = rsSel[urlStatistics]
	# table = soup.find('table', attrs={'class':'table yf-18eg72q'})
	table = soup.find(
		"table",
		class_=lambda x: x and "table" in x
	)
	da = []
	da2 = []
	da3 = []
	da4 = []
	title = []
	ths = table.find_all('th')
	for th in ths:
		title.append(th.text)
	tr = table.find_all('tr')
	row_data = []
	row_data2 = []
	row_data3 = []
	row_data4 = []
	for cell in tr[7]:
		if cell.text.strip():
			row_data.append(cell.text)
	for ce in tr[5]:
		if ce.text.strip():
			row_data2.append(ce.text) 
	for cel in tr[3]:
		if cel.text.strip():
			row_data3.append(cel.text) 
	for c in tr[4]:
		if c.text.strip():
			row_data4.append(c.text)        
	da.append(row_data)
	daf = pd.DataFrame(da, columns = title)
	da2.append(row_data2)
	daf2 = pd.DataFrame(da2, columns = title)
	da3.append(row_data3)
	daf3 = pd.DataFrame(da3, columns = title)
	da4.append(row_data4)
	daf4 = pd.DataFrame(da4, columns = title)

	if '--' in daf2.iloc[0, 1]:
		peg = ''
	else:
		peg = round(float(daf2.iloc[0, 1]),2)
	return daf, daf2, daf3, daf4, peg

@st.cache_resource
def save_to_csv(data, filename='ticker_data.csv'):
    if os.path.exists(filename):
        existing_data = pd.read_csv(filename)
        if data["Ticker"].iloc[0] in existing_data["Ticker"].values:
            # Update the existing ticker's data
            existing_data.set_index("Ticker", inplace=True)
            data.set_index("Ticker", inplace=True)
            existing_data.update(data)
            final_data = existing_data.reset_index()
        else:
            # Append new ticker's data
            final_data = pd.concat([existing_data, data], ignore_index=True)
    final_data.to_csv(filename, index=False)
	
# print(mck_info("MSFT"))