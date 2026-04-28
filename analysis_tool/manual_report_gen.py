
import sys
import os
from datetime import datetime

# Import the PDF generation classes
from analyze_ticker import PDFReportGenerator, ChartGenerator, cleanup_files
import yfinance as yf

def create_manual_report():
    ticker_symbol = "GOOGL"
    
    # Cleanup old files
    cleanup_files(ticker_symbol)
    
    # 1. User Provided Analysis Content (Cleaned and Formatted)
    custom_report_text = """
### 核心数据
- **最新收盘价**: $322.86
- **综合评分**: 3.5 / 10
- **操作建议**: 持有 (HOLD)

### 支撑位与压力位参考
- **压力位 (Resistance)**:
  - $349.00 : 近 20 日高点 (强阻力位)
  - $343.47 : 布林带上轨
- **支撑位 (Support)**:
  - $321.98 : 布林带下轨 (当前价格正测试此支撑)
  - $321.70 : 50 日均线 (关键中期支撑)
  - $306.46 : 近 20 日最低点 (若跌破上述支撑，将看至此位)

### 技术指标状态
- **RSI**: 43.65 (中性偏弱)。市场情绪较弱，但未进入极度恐慌的超卖区。
- **MACD**: 死叉 状态 (4.02 < 5.69)，且缺口未收敛，显示短期仍有下行压力。
- **布林带**: 股价目前在布林带下轨附近运行，关注能否在 $322 一线企稳。
- **成交量**: 56.3M (平均 37.2M)，放量下跌，说明抛压较重。

### 定投 (DCA) 价值分析
- **评价**: [☆ 良好]
- **注意**: 脚本显示的股息率 (26.00%) 为数据源错误，实际上 Google 的股息率通常很低（< 1%）或主要通过回购回馈股东。
- **估值**: 市盈率 (PE) 约 29.8 倍，Forward PE 24.2 倍。考虑到其在 AI 和搜索领域的统治地位，估值处于合理偏高区间。
- **策略**: 对于看好 AI 长期发展的投资者，GOOGL 具备长期配置价值，但目前技术面偏弱，建议 **分批定投**，不要一次性大额买入。

### 交易区间建议
- **买入关注**: 密切关注 321.70 - 322.00 区域。这是 50 日均线和布林带下轨的 **双重支撑位**。如果能在此位置缩量企稳，是极佳的博反弹买点。
- **卖出关注**: 短期反弹目标看 $343.50 附近。

### 总结
GOOGL 目前正处于一个关键的十字路口，正在测试重要的技术支撑位 ($322)。
- **策略**: 观望/轻仓尝试。
  - 如果收盘价跌破 321，建议离场观望，等待 306 附近的更低点。
  - 如果能在 $322 获得支撑并反弹，可轻仓参与。
  - 对于定投者，目前价格适中，可按计划执行。
"""

    # 2. Generate a Chart (Optional, but good for visual)
    # Note: The chart will show CURRENT data, which might not match the text's historical/example data.
    # We'll generate it anyway for completeness, but user should be aware.
    print("Generating Charts (Current Data)...")
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="1y")
        hist_hourly = ticker.history(period="1mo", interval="1h")
        
        if not hist.empty:
            charts = ChartGenerator.generate_charts(ticker_symbol, hist, hist_hourly)
            chart_path = charts.get('daily')
            chart_path_hourly = charts.get('hourly')
        else:
            chart_path = None
            chart_path_hourly = None
            
    except Exception as e:
        print(f"Chart generation failed: {e}")
        chart_path = None
        chart_path_hourly = None

    # 3. Construct PDF Data Dictionary
    
    news_summary_text = """
    Alphabet Inc. (GOOGL) 近期面临着机遇与挑战并存的复杂局面。在人工智能领域，公司持续发力，Gemini 模型的迭代更新显示了其在生成式 AI 方面的雄厚技术积累，旨在稳固其在搜索和云服务市场的领导地位。然而，市场对 AI 变现能力的担忧依然存在，投资者密切关注巨额资本支出能否转化为实际利润增长。与此同时，监管压力仍是悬在头顶的达摩克利斯之剑，美国及欧盟的反垄断调查持续对公司股价构成潜在威胁。尽管核心广告业务保持稳健，但宏观经济的不确定性可能会抑制企业广告支出。总体而言，市场目前对 GOOGL 持谨慎乐观态度，期待其在保持核心竞争力的同时，能在 AI 新赛道上取得突破性进展，以提振长期增长预期。
    """
    
    pdf_data = {
        'ticker': ticker_symbol,
        'price': 322.86,   # From text
        'score': 3.5,      # From text
        'action': 'HOLD',  # From text
        'rsi': 43.65,      # From text
        'macd': 4.02,      # From text
        'macd_signal': 5.69, # From text
        'upper_bb': 343.47, # From text
        'lower_bb': 321.98, # From text
        'volume': 56300000, # From text
        'avg_volume': 37200000, # From text
        'resistance_high': 349.00, # From text
        'support_low': 306.46,     # From text
        'sma200': None,    # Not explicitly in text summary
        'news': [],        # No news provided in text
        'news_summary': news_summary_text,
        'chart_path': chart_path,
        'chart_path_hourly': chart_path_hourly,
        'custom_content': custom_report_text
    }

    # 4. Generate PDF
    output_filename = "GOOGL_Analysis_Report_Manual.pdf"
    
    # Ensure manual report filename is also cleaned if it differs from standard pattern
    if os.path.exists(output_filename):
        os.remove(output_filename)
        
    generator = PDFReportGenerator(output_filename)
    generator.generate(pdf_data)
    
    # Cleanup chart images
    if chart_path and os.path.exists(chart_path):
        os.remove(chart_path)
    if chart_path_hourly and os.path.exists(chart_path_hourly):
        os.remove(chart_path_hourly)
        
    print(f"Done! Report generated: {output_filename}")

if __name__ == "__main__":
    create_manual_report()
