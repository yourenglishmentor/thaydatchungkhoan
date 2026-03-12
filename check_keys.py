import pandas as pd

keys = ["Current Assets",
"Current Liabilities",
"Inventory",
"Cash And Cash Equivalents",
"Accounts Receivable",
"Share Issued",
"Total Assets",
"Accounts Payable",
"Total Equity Gross Minority Interest",
"Cash Cash Equivalents And Short Term Investments",
"Total Capitalization",
"Total Liabilities Net Minority Interest",
"Tangible Book Value",
"Receivables",
"Free Cash Flow",
"Depreciation Amortization Depletion",
"Cost Of Revenue",
"Total Revenue",
"Operating Income",
"EBIT",
"EBITDA",
"Net Income",
"Basic EPS",
"Interest Expense",
"shares",
"marketCap",
"trailingAnnualDividendYield",
"payoutRatio",
"fiveYearAvgDividendYield",
"dividendYield",
"trailingPE",
"priceToBook",
"marketCap",
"beta",
"RSI",
"Total Revenue",
"Operating Income",
"Cost Of Revenue",
"Gross Profit",
"EBIT",
"EBITDA",
"Net Income",
"Net Income Continuous Operations",
"Selling General And Administration",
"Interest Expense",
"Current Assets",
"Current Liabilities",
"Inventory",
"Cash And Cash Equivalents",
"Accounts Receivable",
"Total Equity Gross Minority Interest",
"Accounts Payable",
"Cash Cash Equivalents And Short Term Investments",
"Total Assets",
"Tangible Book Value",
"Share Issued",
"Long Term Debt And Capital Lease Obligation",
"Long Term Debt",
"Receivables",
"Operating Cash Flow",
"Free Cash Flow",
"Depreciation Amortization Depletion",
"Working Capital",
"Total Debt"]

def ensure_key(obj, name:str):
    for key in keys:
        if isinstance(obj, pd.Series):
            if key not in obj.index or pd.isna(obj.get(key, None)) or obj.get(key, 0) == 0:
                print(f'Feature bị thiếu: {key}')
                if key == 'Current Assets' or key == 'Total Assets':
                    obj.loc[key] = 3
                    print(f'-- Feature {name}:{key} được gán: {obj.loc[key]}')
                else:
                    obj.loc[key] = 1
                    print(f'-- Feature {name}:{key} được gán: {obj.loc[key]}')
        elif isinstance(obj, pd.DataFrame):
            if key not in obj.index or pd.isna(obj.loc[key]).any() or (obj.loc[key] == 0).any():
                print(f'Feature bị thiếu: {key}')
                if key == 'Current Assets' or key == 'Total Assets':
                    obj.loc[key] = [3] * len(obj.columns)
                    print(f'-- Feature {name}:{key} được gán: {obj.loc[key]}')
                else:
                    obj.loc[key] = [1] * len(obj.columns)
                    print(f'-- Feature {name}:{key} được gán: {obj.loc[key]}')
    
        else:
            raise TypeError("Object must be a pandas Series or DataFrame")