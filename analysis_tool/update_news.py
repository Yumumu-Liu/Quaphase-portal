import yfinance as yf
import json
import time
from pathlib import Path
from deep_translator import GoogleTranslator
from datetime import datetime
import re

def clean_html(raw_html):
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def smart_truncate(text, max_chars):
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    
    # Try to split by sentences (period followed by space)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = ""
    
    for s in sentences:
        if len(result) + len(s) + 1 <= max_chars:
            result += s + " "
        else:
            break
            
    result = result.strip()
    
    # Fallback if even the first sentence is too long or no sentences found
    if not result:
        return text[:max_chars-3] + "..."
        
    return result

def parse_iso_date(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        return int(dt.timestamp())
    except Exception:
        return 0

def save_json(data, filename):
    output_path = Path(__file__).parent / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Successfully updated {filename}")

def get_price_data(ticker_symbol, retries=3):
    while retries > 0:
        try:
            ticker = yf.Ticker(ticker_symbol)
            
            # Try fast_info first
            try:
                price = ticker.fast_info.last_price
                prev_close = ticker.fast_info.previous_close
            except:
                info = ticker.info
                price = info.get('regularMarketPrice') or info.get('currentPrice') or info.get('previousClose')
                prev_close = info.get('previousClose')
            
            if price is None:
                raise ValueError(f"Price is None for {ticker_symbol}")

            if prev_close is None:
                change = 0
                prev_close = price 
            else:
                change = price - prev_close
            
            change_percent = (change / prev_close) * 100 if prev_close else 0
            
            return {
                "price": price,
                "change": change,
                "change_percent": change_percent,
                "ticker_obj": ticker # Return object if needed for history/info
            }
        except Exception as e:
            # print(f"Error fetching {ticker_symbol}: {e}. Retries left: {retries-1}")
            retries -= 1
            time.sleep(1)
    return None

def update_market_data():
    print("Fetching Market Overview Data...")
    tickers = [
        "^GSPC", "^IXIC", "JPY=X", "CNY=X", "SGDCNY=X",
        "^FVX", "^TNX", "BZ=F", "GC=F", "SI=F"
    ]
    
    data = []
    for symbol in tickers:
        market_info = get_price_data(symbol)
        if not market_info:
            print(f"Failed to fetch data for {symbol}")
            continue
            
        # Fetch sparkline (history)
        try:
            hist = market_info["ticker_obj"].history(period="1mo")
            sparkline = [] if hist.empty else hist['Close'].tolist()
        except:
            sparkline = []

        data.append({
            "symbol": symbol,
            "price": f"{market_info['price']:,.2f}",
            "change": f"{market_info['change']:+.2f}",
            "changePercent": f"{market_info['change_percent']:+.2f}%",
            "sparkline": sparkline,
        })
    
    if data:
        save_json(data, 'market_data.json')

def update_marquee_data():
    print("Fetching Marquee Data...")
    us_tickers = ["NVDA", "MSFT", "AAPL", "GOOGL", "AMZN", "META", "AVGO", "TSM", "TSLA", "LLY"]
    hk_tickers = ["0700.HK", "1299.HK", "0005.HK", "0941.HK", "0883.HK", "0857.HK", "3988.HK", "1398.HK", "0939.HK", "3690.HK"]
    all_tickers = us_tickers + hk_tickers
    
    data = []
    for symbol in all_tickers:
        market_info = get_price_data(symbol)
        if not market_info:
            print(f"Failed to fetch data for {symbol}")
            continue
            
        # Get name
        try:
            name = market_info["ticker_obj"].info.get('shortName', symbol)
        except:
            name = symbol

        data.append({
            "symbol": symbol,
            "name": name,
            "price": f"{market_info['price']:,.2f}",
            "change": f"{market_info['change']:+.2f}",
        })

    if data:
        save_json(data, 'marquee_data.json')

def fetch_news(tickers, limit=10, keywords=None, strict_providers=True):
    all_news = []
    seen_titles = set()
    translator = GoogleTranslator(source='auto', target='zh-CN')

    for ticker_symbol in tickers:
        try:
            ticker = yf.Ticker(ticker_symbol)
            news_items = ticker.news
            
            for item in news_items:
                title = None
                link = None
                publisher = None
                publish_time = 0
                summary = None

                if 'content' in item and isinstance(item['content'], dict):
                    content = item['content']
                    title = content.get('title')
                    summary = clean_html(content.get('summary') or content.get('description'))
                    
                    if content.get('clickThroughUrl'):
                        link = content['clickThroughUrl'].get('url')
                    elif content.get('canonicalUrl'):
                        link = content['canonicalUrl'].get('url')
                    
                    if content.get('provider'):
                        publisher = content['provider'].get('displayName')
                    
                    if content.get('pubDate'):
                        publish_time = parse_iso_date(content['pubDate'])
                else:
                    title = item.get('title')
                    link = item.get('link')
                    publisher = item.get('publisher')
                    publish_time = item.get('providerPublishTime')
                    summary = clean_html(item.get('summary'))

                if not title or not link:
                    continue
                
                if strict_providers:
                    allowed_providers = ['yahoo', 'reuters', 'bloomberg']
                    if not publisher:
                        continue
                    pub_lower = publisher.lower()
                    if not any(p in pub_lower for p in allowed_providers):
                        continue

                if title in seen_titles:
                    continue
                
                if keywords:
                    if not any(k.lower() in title.lower() for k in keywords):
                        continue

                seen_titles.add(title)
                
                # Translate title
                try:
                    title_zh = translator.translate(title)
                except Exception:
                    title_zh = title 

                # Truncate and Translate summary
                if summary:
                    summary = smart_truncate(summary, 280)
                
                summary_zh = ""
                if summary:
                    try:
                        summary_zh = translator.translate(summary)
                        summary_zh = smart_truncate(summary_zh, 140)
                    except Exception:
                        summary_zh = summary

                all_news.append({
                    'title': title,
                    'title_zh': title_zh,
                    'summary': summary,
                    'summary_zh': summary_zh,
                    'link': link,
                    'publisher': publisher,
                    'publish_time': publish_time,
                    'type': 'News'
                })
        except Exception as e:
            print(f"Error fetching news for {ticker_symbol}: {e}")
    
    all_news.sort(key=lambda x: x.get('publish_time', 0), reverse=True)
    return all_news[:limit]

def update_news_data():
    # General News
    print("Fetching General News...")
    news_tickers = ['^GSPC', '^IXIC', 'NVDA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META']
    news_data = fetch_news(news_tickers, limit=9, strict_providers=True)
    save_json(news_data, 'news_data.json')

    # M&A News
    print("Fetching M&A News...")
    ma_tickers = [
        'MNA', 'ARB', 'MRGR',   # M&A ETFs
        '^GSPC', '^DJI', '^IXIC', # Major Indices
        'XLK', 'XLF', 'XLV', 'XLC', # Sector ETFs
        'MSFT', 'GOOG', 'AMZN', 'AAPL', 'NVDA', # Big Tech
        'JPM', 'GS', 'MS', # Big Banks
        'BX', 'KKR', 'APO', 'CG', # Private Equity
        'CSCO', 'INTC', 'CRM', 'ORCL' # Enterprise Tech
    ]
    ma_keywords = ['Merger', 'Acquisition', 'Takeover', 'Buyout', 'Deal', 'Offer']
    ma_data = fetch_news(ma_tickers, limit=20, keywords=ma_keywords, strict_providers=False)
    
    if ma_data:
        ma_data = ma_data[:5] # Ensure max 5
    else:
        print("Warning: No M&A news found.")
        
    save_json(ma_data, 'ma_data.json')

    # IPO News
    print("Fetching IPO News...")
    ipo_tickers = ['IPO', 'FPX', '^GSPC']
    ipo_keywords = ['IPO', 'Initial Public Offering', 'Listing', 'Public Debut']
    ipo_data = fetch_news(ipo_tickers, limit=5, keywords=ipo_keywords, strict_providers=False)
    
    if ipo_data:
        ipo_data = ipo_data[:5]
    else:
        print("Warning: No IPO news found.")
        
    save_json(ipo_data, 'ipo_data.json')

import sys

def main():
    print("Starting Data Update...")
    has_error = False
    
    try:
        update_market_data()
    except Exception as e:
        print(f"Error in update_market_data: {e}")
        has_error = True
        
    try:
        update_marquee_data()
    except Exception as e:
        print(f"Error in update_marquee_data: {e}")
        has_error = True
        
    try:
        update_news_data()
    except Exception as e:
        print(f"Error in update_news_data: {e}")
        has_error = True
        
    if has_error:
        print("Update completed with errors.")
        sys.exit(1)
    else:
        print("All updates completed successfully.")

if __name__ == '__main__':
    main()
