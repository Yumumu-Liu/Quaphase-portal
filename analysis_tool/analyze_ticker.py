import yfinance as yf
import pandas as pd
import argparse
import os
from datetime import datetime
import mplfinance as mpf
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT

# Attempt to import fetch_news, provide fallback if missing
try:
    from update_news import fetch_news
except ImportError:
    print("Warning: update_news module not found. News fetching disabled.")
    def fetch_news(*args, **kwargs): return []

# --- Technical Indicators Class ---
class TechnicalIndicators:
    @staticmethod
    def calculate_rsi(data, window=14):
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_macd(data, slow=26, fast=12, signal=9):
        exp1 = data['Close'].ewm(span=fast, adjust=False).mean()
        exp2 = data['Close'].ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        return macd, signal_line

    @staticmethod
    def calculate_bollinger_bands(data, window=20, num_std=2):
        sma = data['Close'].rolling(window=window).mean()
        std = data['Close'].rolling(window=window).std()
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        return upper_band, sma, lower_band

# --- Chart Generation Class ---
class ChartGenerator:
    @staticmethod
    def create_technical_chart(df, title, filename):
        try:
            # Prepare styles
            mc = mpf.make_marketcolors(up='g', down='r', inherit=True)
            s = mpf.make_mpf_style(marketcolors=mc)
            
            # Copy df to avoid modifying original
            df = df.copy()
            
            # Calculate Indicators for Plotting
            df['RSI'] = TechnicalIndicators.calculate_rsi(df)
            df['MACD'], df['Signal'] = TechnicalIndicators.calculate_macd(df)
            df['UpperBB'], df['SMA20'], df['LowerBB'] = TechnicalIndicators.calculate_bollinger_bands(df)
            df['SMA50'] = df['Close'].rolling(window=50).mean()
            
            # Support/Resistance Lines (20 period High/Low)
            recent_high = df['High'].tail(20).max()
            recent_low = df['Low'].tail(20).min()
            
            apds = [
                # Main Chart Overlays
                mpf.make_addplot(df['SMA20'], color='blue', width=0.7, panel=0, label='SMA20'),
                mpf.make_addplot(df['SMA50'], color='orange', width=0.7, panel=0, label='SMA50'),
                mpf.make_addplot(df['UpperBB'], color='gray', linestyle='--', width=0.5, panel=0),
                mpf.make_addplot(df['LowerBB'], color='gray', linestyle='--', width=0.5, panel=0),
                
                # Indicators Panels
                mpf.make_addplot(df['RSI'], panel=2, color='purple', ylabel='RSI', ylim=(0,100)),
                mpf.make_addplot(df['MACD'], panel=3, color='blue', ylabel='MACD'),
                mpf.make_addplot(df['Signal'], panel=3, color='orange'),
            ]
            
            # Hlines for Support/Resistance
            hlines_dict = dict(hlines=[recent_high, recent_low], colors=['red', 'green'], linestyle='-.', linewidths=1.0)
            
            mpf.plot(df, type='candle', addplot=apds, volume=True, 
                     hlines=hlines_dict,
                     style=s, title=title,
                     savefig=filename, figsize=(12, 6),
                     panel_ratios=(4,1,1,1)) # Price:Vol:RSI:MACD
                     
            print(f"Chart saved to: {filename}")
            return filename
        except Exception as e:
            print(f"Error creating chart {filename}: {e}")
            return None

    @classmethod
    def generate_charts(cls, ticker_symbol, daily_df, hourly_df):
        print(f"\nGenerating technical charts for {ticker_symbol}...")
        charts = {}
        
        # 1. Daily Chart
        if daily_df is not None and not daily_df.empty:
            daily_filename = f"{ticker_symbol}_daily_analysis.png"
            charts['daily'] = cls.create_technical_chart(daily_df, f"{ticker_symbol} Daily Analysis", daily_filename)
            
        # 2. Hourly Chart
        if hourly_df is not None and not hourly_df.empty:
            hourly_filename = f"{ticker_symbol}_hourly_analysis.png"
            charts['hourly'] = cls.create_technical_chart(hourly_df, f"{ticker_symbol} Hourly Analysis", hourly_filename)
            
        return charts

# --- PDF Report Generator Class ---
class PDFReportGenerator:
    def __init__(self, filename):
        self.filename = filename
        self.font_name = self._register_chinese_font()
        self.doc = SimpleDocTemplate(filename, pagesize=A4,
                                     rightMargin=30, leftMargin=30,
                                     topMargin=30, bottomMargin=30)
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
        
    def _register_chinese_font(self):
        try:
            # Try macOS standard font
            font_path = "/System/Library/Fonts/STHeiti Light.ttc"
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('STHeiti', font_path))
                return 'STHeiti'
            return 'Helvetica'
        except Exception as e:
            print(f"Font registration warning: {e}")
            return 'Helvetica'

    def _create_custom_styles(self):
        # 1. Header Styles
        self.brand_style = ParagraphStyle(
            'BrandStyle', parent=self.styles['Normal'],
            fontName='Helvetica-Bold', fontSize=20, leading=24,
            textColor=colors.black, spaceAfter=4
        )
        self.mixed_header_style = ParagraphStyle(
            'MixedHeader', parent=self.styles['Normal'],
            leading=24, spaceAfter=4
        )
        self.date_style = ParagraphStyle(
            'DateStyle', parent=self.styles['Normal'],
            fontName='Times-Italic', fontSize=9, leading=12,
            textColor=colors.gray, spaceAfter=15
        )
        self.ticker_header_style = ParagraphStyle(
            'TickerHeader', parent=self.styles['Heading2'],
            fontName='Helvetica-Bold', fontSize=14, leading=18,
            textColor=colors.darkblue, spaceAfter=12
        )
        self.headline_style = ParagraphStyle(
            'HeadlineStyle', parent=self.styles['Heading1'],
            fontName='Times-Roman', fontSize=24, leading=30,
            textColor=colors.black, spaceAfter=25
        )

        # 2. Body Styles
        self.normal_style = ParagraphStyle(
            'NormalStyle', parent=self.styles['Normal'],
            fontName=self.font_name, fontSize=10.5, leading=18,
            spaceAfter=8, alignment=TA_LEFT, wordWrap='CJK'
        )
        self.news_summary_style = ParagraphStyle(
            'NewsSummary', parent=self.normal_style,
            leftIndent=10, fontSize=9, textColor=colors.darkgrey
        )
        self.heading_style = ParagraphStyle(
            'HeadingStyle', parent=self.styles['Heading2'],
            fontName='Helvetica-Bold', fontSize=11, leading=14,
            textColor=colors.black, spaceBefore=15, spaceAfter=8,
            textTransform='uppercase', wordWrap='CJK'
        )

    def generate(self, data):
        print(f"Generating PDF report: {self.filename}...")
        story = []
        
        # --- 1. HEADER SECTION ---
        header_html = f'<font face="Helvetica-Bold" size=20>Yumumu</font>  <font size=14 color=gray>|</font>  <font face="Helvetica" size=10>RESEARCH</font>'
        story.append(Paragraph(header_html, self.mixed_header_style))
        
        date_str = datetime.now().strftime('%B %d, %Y %H:%M GMT')
        story.append(Paragraph(date_str, self.date_style))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph(f"{data['ticker']} | Global Equities", self.ticker_header_style))
        
        headline_text = f"Analysis: {data['action']} Rating with Score {data['score']:.1f}/10"
        story.append(Paragraph(headline_text, self.headline_style))
        
        # --- 2. SUMMARY BOX ---
        t_data = [
            ['SUMMARY'],
            [f"Price: ${data['price']:.2f}", f"Rating: {data['action']}", f"Score: {data['score']:.1f}/10"]
        ]
        
        t = Table(t_data, colWidths=[2.2*inch, 2.2*inch, 2.2*inch])
        t.setStyle(TableStyle([
            ('SPAN', (0,0), (-1,0)),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 8),
            ('BOTTOMPADDING', (0,0), (-1,0), 4),
            ('TOPPADDING', (0,0), (-1,0), 4),
            ('FONTNAME', (0,1), (-1,1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,1), 9),
            ('ALIGN', (0,1), (-1,1), 'CENTER'),
            ('LINEBELOW', (0,1), (-1,1), 0.5, colors.black),
            ('LINEABOVE', (0,0), (-1,0), 0.5, colors.black),
        ]))
        story.append(t)
        story.append(Spacer(1, 20))
        
        # --- 3. BODY CONTENT ---
        if 'custom_content' in data and data['custom_content']:
            self._parse_custom_content(story, data['custom_content'])
        else:
            self._generate_default_content(story, data)
            
        story.append(Spacer(1, 20))

        # --- 4. CHARTS ---
        chart_width = 7.5 * inch
        chart_height = 3.5 * inch
        
        if data.get('chart_path') and os.path.exists(data['chart_path']):
            story.append(Paragraph("DAILY CHART", self.heading_style))
            story.append(Image(data['chart_path'], width=chart_width, height=chart_height))
            story.append(Spacer(1, 5))
            
        if data.get('chart_path_hourly') and os.path.exists(data['chart_path_hourly']):
            story.append(Paragraph("HOURLY CHART", self.heading_style))
            story.append(Image(data['chart_path_hourly'], width=chart_width, height=chart_height))
            story.append(Spacer(1, 10))
            
        # --- 5. NEWS SECTION ---
        story.append(Paragraph("RECENT NEWS & EVENTS", self.heading_style))
        
        if data.get('news_summary'):
            cleaned_summary = " ".join(data['news_summary'].split())
            story.append(Paragraph(cleaned_summary, self.normal_style))
            story.append(Spacer(1, 10))
            
        for news in data.get('news', []):
            title = news.get('title_zh', news['title'])
            pub_time = news.get('publish_time', 0)
            date_str = datetime.fromtimestamp(pub_time).strftime('%Y-%m-%d') if pub_time else ""
            
            story.append(Paragraph(f"<b>[{date_str}] {title}</b>", self.normal_style))
            
            summary = news.get('summary_zh', news['summary'])
            if summary:
                story.append(Paragraph(summary, self.news_summary_style))
            story.append(Spacer(1, 5))
            
        # Build
        self.doc.build(story)
        print(f"PDF Report saved: {self.filename}")

    def _parse_custom_content(self, story, content):
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line: continue
            
            if line.startswith('### '):
                header_text = line.replace('### ', '').upper()
                story.append(Paragraph(header_text, self.heading_style))
            elif line.startswith('#### '):
                header_text = line.replace('#### ', '')
                h4_style = ParagraphStyle('H4', parent=self.heading_style, fontSize=10)
                story.append(Paragraph(header_text, h4_style))
            elif line.startswith('- ') or line.startswith('* '):
                bullet_text = line[2:]
                if '**' in bullet_text:
                    parts = bullet_text.split('**')
                    bullet_text = "".join([f"<b>{p}</b>" if i % 2 == 1 else p for i, p in enumerate(parts)])
                story.append(Paragraph(f"• {bullet_text}", self.normal_style))
            else:
                story.append(Paragraph(line, self.normal_style))

    def _generate_default_content(self, story, data):
        story.append(Paragraph("TECHNICAL ANALYSIS SUMMARY", self.heading_style))
        story.append(Paragraph(f"<b>RSI (14):</b> {data['rsi']:.2f}", self.normal_style))
        story.append(Paragraph(f"<b>MACD:</b> {data['macd']:.4f} (Signal: {data['macd_signal']:.4f})", self.normal_style))
        story.append(Paragraph(f"<b>Bollinger Bands:</b> Upper {data['upper_bb']:.2f} | Lower {data['lower_bb']:.2f}", self.normal_style))
        story.append(Paragraph(f"<b>Volume:</b> {data['volume']:,} (Avg: {data['avg_volume']:,})", self.normal_style))
        
        story.append(Paragraph("KEY LEVELS", self.heading_style))
        story.append(Paragraph(f"<b>Resistance:</b> {data['resistance_high']:.2f} (Recent High), {data['upper_bb']:.2f} (BB Upper)", self.normal_style))
        story.append(Paragraph(f"<b>Support:</b> {data['support_low']:.2f} (Recent Low), {data['lower_bb']:.2f} (BB Lower)", self.normal_style))
        if data.get('sma200'):
            story.append(Paragraph(f"<b>SMA 200:</b> {data['sma200']:.2f}", self.normal_style))

import glob

# --- Main Logic ---

def cleanup_files(ticker_symbol):
    """Clean up old analysis files (PDFs and PNGs) for the given ticker."""
    patterns = [
        f"{ticker_symbol}_analysis.pdf",
        f"{ticker_symbol}_*_analysis.png"
    ]
    
    for pattern in patterns:
        for filepath in glob.glob(pattern):
            try:
                os.remove(filepath)
                print(f"Cleaned up old file: {filepath}")
            except OSError as e:
                print(f"Error deleting {filepath}: {e}")

def analyze_stock(ticker_symbol):
    # 1. Cleanup old files before starting
    cleanup_files(ticker_symbol)

    pdf_filename = f"{ticker_symbol}_analysis.pdf"
    
    print(f"Analyzing {ticker_symbol}...")
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="1y") 
        if hist.empty:
            print(f"No data found for {ticker_symbol}")
            return

        # Fetch Charts
        hist_hourly = ticker.history(period="1mo", interval="1h")
        charts = ChartGenerator.generate_charts(ticker_symbol, hist, hist_hourly)
        
        # Analysis
        current_price = hist['Close'].iloc[-1]
        rsi = TechnicalIndicators.calculate_rsi(hist).iloc[-1]
        macd, signal = TechnicalIndicators.calculate_macd(hist)
        macd_val, signal_val = macd.iloc[-1], signal.iloc[-1]
        upper_bb, sma20, lower_bb = TechnicalIndicators.calculate_bollinger_bands(hist)
        upper_bb_val, lower_bb_val = upper_bb.iloc[-1], lower_bb.iloc[-1]
        volume = hist['Volume'].iloc[-1]
        avg_volume = hist['Volume'].rolling(window=20).mean().iloc[-1]
        sma200 = hist['Close'].rolling(window=200).mean().iloc[-1]
        recent_high = hist['High'].tail(20).max()
        recent_low = hist['Low'].tail(20).min()
        
        # Simple Scoring Logic
        score = 5.0
        if rsi < 30: score += 2
        elif rsi > 70: score -= 2
        
        if macd_val > signal_val: score += 1
        else: score -= 1
        
        score = max(0, min(10, score))
        action = "BUY" if score >= 7 else "SELL" if score <= 3 else "HOLD"
        
        # Fetch News
        print("\nFetching news...")
        news = fetch_news([ticker_symbol], limit=3, strict_providers=True)
        
        # Prepare Data
        pdf_data = {
            'ticker': ticker_symbol,
            'price': current_price,
            'score': score,
            'action': action,
            'rsi': rsi,
            'macd': macd_val,
            'macd_signal': signal_val,
            'upper_bb': upper_bb_val,
            'lower_bb': lower_bb_val,
            'volume': volume,
            'avg_volume': avg_volume,
            'resistance_high': recent_high,
            'support_low': recent_low,
            'sma200': sma200,
            'news': news,
            'chart_path': charts.get('daily'),
            'chart_path_hourly': charts.get('hourly'),
            'custom_content': None # Default mode
        }
        
        # Generate PDF
        generator = PDFReportGenerator(pdf_filename)
        generator.generate(pdf_data)
        
        # Cleanup temporary chart images
        print("Cleaning up temporary chart images...")
        if charts.get('daily') and os.path.exists(charts['daily']):
            os.remove(charts['daily'])
        if charts.get('hourly') and os.path.exists(charts['hourly']):
            os.remove(charts['hourly'])
        
    except Exception as e:
        print(f"Error analyzing {ticker_symbol}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze a stock ticker.')
    parser.add_argument('ticker', type=str, help='Stock ticker symbol (e.g., AAPL)')
    args = parser.parse_args()
    
    analyze_stock(args.ticker)
