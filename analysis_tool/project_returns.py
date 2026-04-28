import yfinance as yf
import pandas as pd
import numpy as np
import argparse
from datetime import datetime, timedelta

def calculate_cagr(start_price, end_price, years):
    if start_price == 0: return 0
    return (end_price / start_price) ** (1 / years) - 1

def project_returns(ticker_symbol, monthly_investment, target_year):
    print(f"正在为 {ticker_symbol} 计算定投收益预测...")
    print(f"每月定投: ${monthly_investment}")
    print(f"目标年份: {target_year} 年底")
    
    ticker = yf.Ticker(ticker_symbol)
    
    # 1. Fetch historical data (5 years) to estimate growth
    hist = ticker.history(period="5y")
    if hist.empty:
        print("Error: Could not fetch historical data.")
        return

    current_price = hist['Close'].iloc[-1]
    start_price_5y = hist['Close'].iloc[0]
    
    # Calculate 5-year CAGR (Price Appreciation)
    cagr_price = calculate_cagr(start_price_5y, current_price, 5)
    
    # Get Dividend Yield
    # Note: yfinance data can be buggy (e.g., 386%). We use a heuristic limit.
    try:
        div_yield = ticker.info.get('dividendYield', 0)
        if div_yield > 0.10: # If > 10%, it's likely an error for a bank like OCBC, cap it or use average
            # Fallback: estimate from last year's dividends if possible, or use conservative 5%
            print(f"Warning: Detected abnormal yield ({div_yield*100:.2f}%), using conservative 5.5% estimate.")
            div_yield = 0.055
    except:
        div_yield = 0.05 # Default fallback
        
    if div_yield is None: div_yield = 0.05

    # Total Expected Annual Return = Price CAGR + Dividend Yield
    # Conservative adjustment: If CAGR is negative (unlikely for banks long term), assume 0 growth and just dividends? 
    # Or just use the calculated one. Let's use the calculated one but clamp it to be realistic.
    
    total_annual_return = cagr_price + div_yield
    
    # Clamp return for realistic projection (e.g., between 0% and 15%)
    # Banks usually 8-12% total return.
    if total_annual_return > 0.15:
        total_annual_return = 0.15
        print("Note: Capping projected total annual return at 15% for conservative estimate.")
    elif total_annual_return < 0.04:
        total_annual_return = 0.04
        print("Note: Adjusting projected total annual return to min 4% (assuming base dividend yield).")

    print(f"\n--- 参考数据 (基于过去5年) ---")
    print(f"当前价格: {current_price:.2f}")
    print(f"过去5年股价年化增长 (CAGR): {cagr_price*100:.2f}%")
    print(f"当前股息率 (估算): {div_yield*100:.2f}%")
    print(f"预估综合年化回报率: {total_annual_return*100:.2f}%")
    
    # 2. Simulation
    today = datetime.now()
    end_date = datetime(target_year, 12, 31)
    
    months_remaining = (end_date.year - today.year) * 12 + (end_date.month - today.month)
    
    if months_remaining <= 0:
        print("Error: Target date is in the past.")
        return

    total_invested = 0
    current_value = 0
    monthly_rate = (1 + total_annual_return) ** (1/12) - 1
    
    print(f"\n--- 定投模拟 (共 {months_remaining} 个月) ---")
    
    for i in range(months_remaining):
        # Add investment
        total_invested += monthly_investment
        current_value += monthly_investment
        # Grow
        current_value *= (1 + monthly_rate)
        
    profit = current_value - total_invested
    roi = (profit / total_invested) * 100
    
    print(f"到 {target_year} 年底:")
    print(f"总投入本金: ${total_invested:,.2f}")
    print(f"预估总资产: ${current_value:,.2f}")
    print(f"预估收益: ${profit:,.2f}")
    print(f"预估收益率: {roi:.2f}%")
    
    print(f"\n注意: 此预测基于历史数据线性推演，包含股息再投资假设，不代表未来实际收益。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('ticker', type=str)
    parser.add_argument('amount', type=float)
    parser.add_argument('year', type=int)
    args = parser.parse_args()
    
    project_returns(args.ticker, args.amount, args.year)
