document.addEventListener('DOMContentLoaded', function () {
    let currentLang = 'en';

    const translations = {
        en: {
            title: "Daily Financial Report",
            financialReport: "Daily Financial Report",
            lastUpdated: "Last updated",
            marketOverview: "Market Overview",
            newsAnalysis: "News & Analysis",
            recentIPOsMA: "Recent IPOs & M&A",
            recentUpcomingIPOs: "Recent & Upcoming IPOs",
            maActivity: "M&A Activity",
            source: "Source",
            langToggle: "中文"
        },
        zh: {
            title: "每日财经摘要",
            financialReport: "每日财经摘要",
            lastUpdated: "最后更新",
            marketOverview: "市场概览",
            newsAnalysis: "新闻与分析",
            recentIPOsMA: "近期IPO与并购",
            recentUpcomingIPOs: "近期及即将进行的IPO",
            maActivity: "并购活动",
            source: "来源",
            langToggle: "English"
        }
    };

    const marqueeTranslations = {
        'NVDA': '英伟达',
        'MSFT': '微软',
        'AAPL': '苹果',
        'GOOGL': '谷歌',
        'AMZN': '亚马逊',
        'META': 'Meta',
        'AVGO': '博通',
        'TSM': '台积电',
        'TSLA': '特斯拉',
        'LLY': '礼来',
        '0700.HK': '腾讯控股',
        '1299.HK': '友邦保险',
        '0005.HK': '汇丰控股',
        '0941.HK': '中国移动',
        '0883.HK': '中国海洋石油',
        '0857.HK': '中国石油股份',
        '3988.HK': '中国银行',
        '1398.HK': '工商银行',
        '0939.HK': '建设银行',
        '3690.HK': '美团'
    };

    let marketData = [];
    let marqueeData = [];
    let newsData = [];
    let ipoData = [];
    let maData = [];

    function fetchMarqueeData() {
        return fetch('./marquee_data.json')
            .then(response => response.json())
            .then(data => {
                marqueeData = data;
                populateMarquee();
            })
            .catch(error => console.error('Error fetching marquee data:', error));
    }

    function fetchNewsData() {
        return fetch('./news_data.json')
            .then(response => response.json())
            .then(data => {
                newsData = data;
                populateNews();
            })
            .catch(error => console.error('Error fetching news data:', error));
    }

    function fetchIPOData() {
        return fetch('./ipo_data.json')
            .then(response => response.json())
            .then(data => {
                ipoData = data;
                renderIPOList();
            })
            .catch(error => console.error('Error fetching IPO data:', error));
    }

    function fetchMAData() {
        return fetch('./ma_data.json')
            .then(response => response.json())
            .then(data => {
                maData = data;
                renderMAList();
            })
            .catch(error => console.error('Error fetching M&A data:', error));
    }



    function fetchMarketData() {
        const translationsMap = {
            '^GSPC': { name: '标准普尔500指数', reasons: ['科技板块表现强劲。', '尽管市场波动，但势头良好。'] },
            '^IXIC': { name: '纳斯达克指数', reasons: ['英伟达等AI相关股票带动上涨。', '科技行业整体看涨情绪。'] },
            'JPY=X': { name: '美元/日元', reasons: ['日本政局不稳导致日元走强。', '不确定性中投资者寻求日元避险。'] },
            'CNY=X': { name: '美元/人民币', reasons: ['对美联储独立性的担忧导致美元走弱。', '小幅上涨表明市场情绪复杂。'] },
            'SGDCNY=X': { name: '新元/人民币', reasons: ['区域经济数据影响货币对。', '更广泛的市场趋势影响新兴市场货币。'] },
            '^FVX': { name: '2年期美国国债', reasons: ['投资者寻求避险资产导致收益率下降。', '地缘政治紧张局势增加了对短期债券的需求。'] },
            '^TNX': { name: '10年期美国国债', reasons: ['全球不确定性下的避险需求。', '对欧美地缘政治事件的担忧。'] },
            'BZ=F': { name: '布伦特原油', reasons: ['伊朗供应中断的担忧已计入价格。', '委内瑞拉增加供应的前景使价格回落。'] },
            'GC=F': { name: '黄金', reasons: ['地缘政治紧张局势推动金价创下历史新高。', '美元走弱以及资金从美国国债流出。'] },
            'SI=F': { name: '白银', reasons: ['作为避险资产，与黄金一同飙升。', '市场不确定性中投资者需求强劲。'] }
        };

        const enNamesMap = {
            '^GSPC': 'S&P 500',
            '^IXIC': 'Nasdaq',
            'JPY=X': 'USD/JPY',
            'CNY=X': 'USD/CNY',
            'SGDCNY=X': 'SGD/CNY',
            '^FVX': '2Y UST',
            '^TNX': '10Y UST',
            'BZ=F': 'Brent',
            'GC=F': 'Gold',
            'SI=F': 'Silver'
        };

        const enReasonsMap = {
            '^GSPC': ['Tech sector showing strong performance.', 'Good momentum despite market volatility.'],
            '^IXIC': ['Boosted by AI-related stocks like Nvidia.', 'Overall bullish sentiment in the tech industry.'],
            'JPY=X': ['Yen strengthened due to political instability in Japan.', 'Investors seeking safe haven in yen amid uncertainty.'],
            'CNY=X': ['Dollar weakened on concerns about Fed independence.', 'Slight gain indicates mixed market sentiment.'],
            'SGDCNY=X': ['Regional economic data influencing the currency pair.', 'Broader market trends affecting emerging market currencies.'],
            '^FVX': ['Yields dropped as investors sought safe-haven assets.', 'Geopolitical tensions increased demand for short-term bonds.'],
            '^TNX': ['Safe-haven demand amid global uncertainty.', 'Concerns over geopolitical events in Europe and the US.'],
            'BZ=F': ['Concerns about supply disruptions from Iran priced in.', 'Prices eased on prospects of increased supply from Venezuela.'],
            'GC=F': ['Geopolitical tensions pushed gold to record highs.', 'Weakening dollar and flight from US Treasuries.'],
            'SI=F': ['Surged along with gold as a safe-haven asset.', 'Strong investor demand amid market uncertainty.']
        };

        return fetch('./market_data.json')
            .then(response => response.json())
            .then(data => {
                marketData = data.map(item => {
                    const symbol = item.symbol;
                    const enName = enNamesMap[symbol] || item.en.name || symbol;
                    const zhTranslation = translationsMap[symbol] || { name: enName, reasons: [] };
                    const enReasons = enReasonsMap[symbol] || [];

                    return {
                        ...item,
                        en: { name: enName, reasons: enReasons },
                        zh: { name: zhTranslation.name, reasons: zhTranslation.reasons }
                    };
                });
                renderMarketOverviewAndCharts();
                updateContent();
            })
            .catch(error => console.error('Error fetching market data:', error));
    }

    function renderIPOList() {
        const ipoList = document.getElementById('ipo-list');
        const t = translations[currentLang];
        if (!ipoData || !ipoData.length) {
            ipoList.innerHTML = `<li class="text-gray-400 text-sm">No recent IPO news found.</li>`;
            return;
        }
        ipoList.innerHTML = ipoData.map(item => {
            const title = currentLang === 'zh' ? (item.title_zh || item.title) : item.title;
            const summary = currentLang === 'zh' ? (item.summary_zh || item.summary) : item.summary;
            let dateStr = "";
            if (item.publish_time) {
                dateStr = new Date(item.publish_time * 1000).toLocaleDateString();
            }
            return `
            <li class="bg-gray-800 p-4 rounded-lg">
                <div class="mb-2">
                    <span class="font-bold text-lg"><a href="${item.link}" target="_blank" class="hover:text-blue-400">${title}</a></span>
                </div>
                ${summary ? `<p class="text-gray-300 text-sm mb-2 line-clamp-2">${summary}</p>` : ''}
                <div class="text-xs text-gray-500 flex justify-between mt-2">
                    <span>${dateStr}</span>
                    <a href="${item.link}" target="_blank" class="hover:text-blue-400 hover:underline">
                        ${t.source}: ${item.publisher}
                    </a>
                </div>
            </li>
            `;
        }).join('');
    }

    function renderMAList() {
        const maList = document.getElementById('ma-list');
        const t = translations[currentLang];
        if (!maData || !maData.length) {
            maList.innerHTML = `<li class="text-gray-400 text-sm">No recent M&A news found.</li>`;
            return;
        }
        maList.innerHTML = maData.map(item => {
            const title = currentLang === 'zh' ? (item.title_zh || item.title) : item.title;
            const summary = currentLang === 'zh' ? (item.summary_zh || item.summary) : item.summary;
            let dateStr = "";
            if (item.publish_time) {
                dateStr = new Date(item.publish_time * 1000).toLocaleDateString();
            }
            return `
            <li class="bg-gray-800 p-4 rounded-lg">
                <div class="mb-2">
                    <span class="font-bold text-lg"><a href="${item.link}" target="_blank" class="hover:text-blue-400">${title}</a></span>
                </div>
                ${summary ? `<p class="text-gray-300 text-sm mb-2 line-clamp-2">${summary}</p>` : ''}
                <div class="text-xs text-gray-500 flex justify-between mt-2">
                    <span>${dateStr}</span>
                    <a href="${item.link}" target="_blank" class="hover:text-blue-400 hover:underline">
                        ${t.source}: ${item.publisher}
                    </a>
                </div>
            </li>
            `;
        }).join('');
    }

    function getColor(change) {
        if (change.startsWith('+')) return 'text-green-500';
        if (change.startsWith('-')) return 'text-red-500';
        return 'text-gray-400';
    }

    function getChartColor(change) {
        if (change.startsWith('+')) return '#22c55e'; // green-500
        if (change.startsWith('-')) return '#ef4444'; // red-500
        return '#9ca3af'; // gray-400
    }

    function renderMarketOverviewAndCharts() {
        const marketOverview = document.querySelector('#market-overview .grid');
        marketOverview.innerHTML = marketData.map((item, index) => `
            <div class="bg-gray-800 p-4 rounded-lg">
                <h3 class="font-bold text-lg"></h3>
                <p class="text-2xl font-semibold">${item.price}</p>
                <p class="text-lg ${getColor(item.changePercent)}">${item.change} (${item.changePercent})</p>
                <div id="chart-${index}" class="mt-2"></div>
                <ul class="mt-3 text-sm text-gray-400 space-y-1"></ul>
            </div>
        `).join('');

        marketData.forEach((item, index) => {
            const options = {
                chart: { type: 'area', height: 50, sparkline: { enabled: true } },
                series: [{ data: item.sparkline }],
                stroke: { curve: 'smooth', width: 2 },
                colors: [getChartColor(item.changePercent)],
                fill: {
                    type: 'gradient',
                    gradient: {
                        shadeIntensity: 1,
                        opacityFrom: 0.7,
                        opacityTo: 0.3,
                        stops: [0, 90, 100]
                    }
                },
                tooltip: { enabled: false }
            };
            const chart = new ApexCharts(document.querySelector(`#chart-${index}`), options);
            chart.render();
        });
    }

    function populateNews() {
        const newsSection = document.querySelector('#news .grid');
        newsSection.innerHTML = newsData.map(item => {
            const title = currentLang === 'zh' ? (item.title_zh || item.title) : item.title;
            const summary = currentLang === 'zh' ? (item.summary_zh || item.summary) : item.summary;
            const sourceLabel = translations[currentLang].source;
            // Format timestamp if available, else use publisher
            let dateStr = "";
            if (item.publish_time) {
                dateStr = new Date(item.publish_time * 1000).toLocaleDateString();
            }
            
            return `
            <div class="bg-gray-800 p-6 rounded-lg h-full flex flex-col">
                <h3 class="font-bold text-xl mb-2"><a href="${item.link}" target="_blank" class="hover:text-blue-400">${title}</a></h3>
                ${summary ? `<div class="text-gray-300 text-sm mb-4 line-clamp-5 flex-grow">${summary}</div>` : '<div class="flex-grow"></div>'}
                <div class="text-sm text-gray-400 mt-auto flex justify-between">
                    <a href="${item.link}" target="_blank" class="hover:text-blue-400 hover:underline">
                        ${sourceLabel}: ${item.publisher}
                    </a>
                    <span>${dateStr}</span>
                </div>
            </div>
            `;
        }).join('');
    }

    function updateContent() {
        const t = translations[currentLang];
        document.title = t.title;

        // Update header
        document.querySelector('h1').textContent = t.financialReport;
        const now = new Date();
        const timeString = now.toTimeString().split(' ')[0];
        document.querySelector('.text-sm.text-gray-400 span').textContent = `${t.lastUpdated}: ${now.toLocaleDateString()} ${timeString}`;
        document.getElementById('lang-toggle').textContent = t.langToggle;

        // Update section titles
        document.querySelector('#market-overview h2').textContent = t.marketOverview;
        document.querySelector('#news h2').textContent = t.newsAnalysis;
        
        const dealsHeader = document.querySelector('#deals > h2') || document.querySelector('#deals h2');
        if (dealsHeader) dealsHeader.textContent = t.recentIPOsMA;
        
        document.getElementById('ipo-header').textContent = t.recentUpcomingIPOs;
        document.getElementById('ma-header').textContent = t.maActivity;

        // Update Market Overview text
        document.querySelectorAll('#market-overview .grid > div').forEach((card, index) => {
            if (marketData[index]) {
                const item = marketData[index];
                const nameEl = card.querySelector('h3');
                if (nameEl) nameEl.textContent = item[currentLang].name;
                
                const ulEl = card.querySelector('ul');
                if (ulEl) ulEl.innerHTML = item[currentLang].reasons.map(reason => `<li>- ${reason}</li>`).join('');
            }
        });

        // Re-render components that depend on language
        populateMarquee();
        populateNews();
        
        // Update IPO and M&A lists
        renderIPOList();
        renderMAList();
    }

    function populateMarquee() {
        const marqueeContent = document.querySelector('.marquee-content');
        if (!marqueeData.length) return;
        const marqueeItems = [...marqueeData, ...marqueeData]; // Duplicate for seamless loop
        marqueeContent.innerHTML = marqueeItems.map(item => {
            let displayName = item.name;
            if (currentLang === 'zh' && marqueeTranslations[item.symbol]) {
                displayName = marqueeTranslations[item.symbol];
            }
            
            return `
            <div class="flex items-center space-x-4">
                <span class="font-semibold"><span class="text-nowrap">${displayName}</span></span>
                <span class="${getColor(item.change)}">${item.price}</span>
                <span class="${getColor(item.change)}">${item.change}</span>
            </div>
            `;
        }).join('');
    }

    document.getElementById('lang-toggle').addEventListener('click', () => {
        currentLang = currentLang === 'en' ? 'zh' : 'en';
        updateContent();
    });

    fetchMarketData();
    fetchMarqueeData();
    fetchNewsData();
    fetchIPOData();
    fetchMAData();
});
