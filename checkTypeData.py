import yfinance as yf
import json
from pathlib import Path

from datetime import datetime as dt
from datetime import timedelta
import datetime

import pandas as pd
import crawl_mck



def should_crawl(meta_path="crawl_date.json", max_age_days=90) -> bool:
    meta_file = Path(meta_path)

    # Chưa từng crawl → crawl ngay
    if not meta_file.exists():
        return True

    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    last_crawled = dt.fromisoformat(meta["last_crawled"])
    return dt.now(datetime.timezone.utc) - last_crawled >= timedelta(days=max_age_days)

def update_crawl_time(meta_path="crawl_date.json"):
    meta = {
        "last_crawled": dt.now(datetime.timezone.utc).isoformat()
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

# if should_crawl("crawl_date.json", 90):
#     print("Data outdated – updating...")
#     # crawl here
#     update_crawl_time("crawl_date.json")
# else:
#     print("data up to date")

# ticker = "MSFT"

# mck = yf.Ticker(ticker)

#-----json------

# mck_info = mck.info
# print(f"mck_info: {type(mck_info)}")

# crprice = float(mck.history(period='1d')['Close'].iloc[0])
# print(f"crprice: {type(crprice)}")

# comp_list = ["LNT",
# "ALL",
# "GOOGL",
# "GOOG",
# "MO",
# "AMZN"
# ]



def save_mck_info(ticker: str, base_dir="./database"):
    mck = yf.Ticker(ticker)

    # Lấy info
    mck_info = mck.info

    # Lấy giá hiện tại (close của ngày gần nhất)
    hist = mck.history(period="1d")
    if hist.empty:
        crprice = None
    else:
        crprice = float(hist["Close"].iloc[0])

    # Gộp vào 1 dict
    output = {
        "ticker": ticker,
        "crprice": crprice,
        "mck_info": mck_info
    }

    # Tạo thư mục
    path = Path(base_dir) / ticker
    path.mkdir(parents=True, exist_ok=True)

    # Lưu JSON
    with open(path / "mck_info.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    # print("DONE!")
    return path / "mck_info.json"

# save_mck_info("MSFT")
def load_mck_info(ticker: str, base_dir="database"):
    path = Path(base_dir) / ticker / "mck_info.json"

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data
# mck_info_data = load_mck_info("MSFT")
# mck_info = mck_info_data["mck_info"]

# for c in comp_list:
#     save_mck_info(c)


# beta_value = mck_info['mck_info']['beta'] if 'beta' in mck_info['mck_info'] else 0
# print(beta_value)
#---------------

#-----parquet------

def save_parquet(df, ticker: str, filename: str, base_dir="database"):
    """
    df       : pandas DataFrame
    ticker   : ticker symbol (e.g. 'MCK')
    filename : file name without extension
    """
    if df is None or df.empty:
        return None

    path = Path(base_dir) / ticker
    path.mkdir(parents=True, exist_ok=True)

    file_path = path / f"{filename}.parquet"
    df.to_parquet(file_path)

    return file_path

# current = datetime.today().date()
# start_date = current - timedelta(days=365)
# end_date = current

# data = yf.download(ticker, start_date, end_date)

# print(f"data: {type(data)}")

# save_parquet(data, ticker, filename="data")

# income = mck.income_stmt

# print(f"income: {type(income)}")

# save_parquet(income, ticker, filename="income")

# quarter_bsheet = mck.quarterly_balance_sheet

# print(f"quarter_bsheet: {type(quarter_bsheet)}")

# save_parquet(quarter_bsheet, ticker, filename="quarter_bsheet")

# bsheet = mck.balance_sheet

# print(f"bsheet: {type(bsheet)}")

# save_parquet(bsheet, ticker, filename="bsheet")

# quarter_cfs = mck.quarterly_cashflow

# print(f"quarter_cfs: {type(quarter_cfs)}")

# save_parquet(quarter_cfs, ticker, filename="quarter_cfs")

# quarter_income = mck.quarterly_income_stmt

# print(f"quarter_income: {type(quarter_income)}")
# save_parquet(quarter_income, ticker, filename="quater_income")

# cfs = mck.cash_flow

# print(f"cfs: {type(cfs)}")
# save_parquet(cfs, ticker, filename="cfs")


# dataa = pd.read_parquet("./database/MSFT/data.parquet")

# dataa['EMA20'] = dataa['Close'][ticker].ewm(span=20, adjust=False).mean()
# dataa['MA50'] = dataa['Close'][ticker].rolling(50).mean()
# dataa['MA100'] = dataa['Close'][ticker].rolling(100).mean()
# dataa['MA150'] = dataa['Close'][ticker].rolling(150).mean()

# income = pd.read_parquet("./database/MSFT/income.parquet")

# years_val = income.columns[-5:-1]

# quarter_bsheet = pd.read_parquet("./database/MSFT/quarter_bsheet.parquet")

# first_column_index = quarter_bsheet.columns[0]
# # print(first_column_index)
# TTM_bsheet = quarter_bsheet[first_column_index]
# # print(TTM_bsheet)
# second_column_index = quarter_bsheet.columns[1]
# # print(second_column_index)
# TTM_bsheet2 = quarter_bsheet[second_column_index]
# TTM_bsheet3 = quarter_bsheet.iloc[:, :4].sum(axis=1)
# five_column_index = quarter_bsheet.columns[len(years_val)]
# TTM_bsheet4 = quarter_bsheet[five_column_index]
# print("DONE~!")



#---------------

def save_fast_info(ticker: str, mck, base_dir="database"):

    fast_info = mck.fast_info

    # Convert FastInfo -> dict
    fast_info_dict = dict(fast_info)

    path = Path(base_dir) / ticker
    path.mkdir(parents=True, exist_ok=True)

    file_path = path / "fast_info.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(fast_info_dict, f, ensure_ascii=False, indent=2)

    return file_path

def load_fast_info(ticker: str, base_dir="database"):
    path = Path(base_dir) / ticker / "fast_info.json"

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data

# save_fast_info("MSFT")

# fast_info = load_fast_info("MSFT")
# fast_info['currency']
# shares_outstanding = fast_info['shares']
# market_cap = fast_info['marketCap'] 

# fast_info = mck.fast_info

# fast_info_dict = dict(fast_info)

# print(f"fast_info: {type(fast_info)}")







import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# secDict = crawl_mck.run_selenium("MSFT", fullExchangeName=mck_info['fullExchangeName'])
# print(secDict)

def run_selenium(ticker, fullExchangeName: str, driver):
	results = {}

	if ".VN" not in ticker:
		urlAnalysis = f'https://fiscal.ai/company/{fullExchangeName}-{ticker}/'
	else:
		urlAnalysis = f'https://fiscal.ai/company/{fullExchangeName}-{ticker[:-3]}/'
	urlStatistics = f'https://finance.yahoo.com/quote/{ticker}/key-statistics?p={ticker}'


	urls = [urlAnalysis, urlStatistics]
	
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
	return results

def save_selenium(ticker, results, base_dir = "database"):
    """
    Convert BeautifulSoup Tag -> HTML string
    """
    serialized = {}

    for url, value in results.items():
        if hasattr(value, "name"):  # BeautifulSoup Tag
            serialized[url] = {
                "__type__": "bs4_tag",
                "html": value.prettify()
            }
        else:
            serialized[url] = value
    path = Path(base_dir) / ticker / "save_selenium.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(serialized, f, ensure_ascii=False, indent=2)

def deserialize_results(data: dict) -> dict:
    """
    Convert HTML string -> BeautifulSoup Tag
    """
    restored = {}

    for url, value in data.items():
        if isinstance(value, dict) and value.get("__type__") == "bs4_tag":
            soup = BeautifulSoup(value["html"], "html.parser")
            restored[url] = soup.find()  # trả lại Tag
        else:
            restored[url] = value

    return restored
      
      


# # Khởi tạo driver 1 lần
# options = Options()
# options.add_argument("--headless")
# options.add_argument("--disable-gpu")
# options.add_argument("--disable-dev-shm-usage")
# driver = webdriver.Chrome(options=options)

# mck_info_data = load_mck_info("MSFT")
# mck_info = mck_info_data["mck_info"]


# rs = run_selenium("MSFT", fullExchangeName=mck_info['fullExchangeName'], driver=driver)
# print(type(rs))
# print(rs)

# driver.quit()

# save_selenium("MSFT", results=rs)


# with open("database/MSFT/save_selenium.json", "r", encoding="utf-8") as f:
#     raw = json.load(f)

# results = deserialize_results(raw)
# # print(results)

# growth_rate1, growth_rate2, growth_rate3 = crawl_mck.analysis("MSFT", results, fullExchangeName=mck_info['fullExchangeName'])

# print(growth_rate1, growth_rate2, growth_rate3)

# daf, daf2, daf3, daf4, peg=crawl_mck.discounted_Cash_Flow_Method_10_years("MSFT", results)

# pDe = round(float(daf3.iloc[0, 1]),2) if '--' not in daf3.iloc[0, 1] else 0
# b = [round(float(daf.iloc[0, 1]),2) if '--' not in daf.iloc[0, 1] else '']
# a = [round(float(daf4.iloc[0, 1]),2) if '--' not in daf4.iloc[0, 1] else '']

# print(pDe, b, a)
