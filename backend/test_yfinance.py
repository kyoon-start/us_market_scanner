import yfinance as yf

data = yf.download("AAPL", period="1y", auto_adjust=True)
print(data.tail())