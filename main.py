import asyncio
import time
from datetime import datetime, timezone
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI(title="FinancePro")
YAHOO = "https://query1.finance.yahoo.com"
HEADERS = {"User-Agent": "Mozilla/5.0 FinancePro/1.0"}
UNIVERSE = [
    {"symbol":"BTC-USD","name":"Bitcoin","category":"Crypto"},{"symbol":"ETH-USD","name":"Ethereum","category":"Crypto"},{"symbol":"SOL-USD","name":"Solana","category":"Crypto"},{"symbol":"BNB-USD","name":"BNB","category":"Crypto"},{"symbol":"XRP-USD","name":"XRP","category":"Crypto"},{"symbol":"ADA-USD","name":"Cardano","category":"Crypto"},{"symbol":"DOGE-USD","name":"Dogecoin","category":"Crypto"},{"symbol":"AVAX-USD","name":"Avalanche","category":"Crypto"},
    {"symbol":"AAPL","name":"Apple","category":"Stocks"},{"symbol":"MSFT","name":"Microsoft","category":"Stocks"},{"symbol":"NVDA","name":"NVIDIA","category":"Stocks"},{"symbol":"GOOGL","name":"Alphabet","category":"Stocks"},{"symbol":"AMZN","name":"Amazon","category":"Stocks"},{"symbol":"META","name":"Meta Platforms","category":"Stocks"},{"symbol":"TSLA","name":"Tesla","category":"Stocks"},{"symbol":"BRK-B","name":"Berkshire Hathaway","category":"Stocks"},{"symbol":"LLY","name":"Eli Lilly","category":"Stocks"},{"symbol":"JPM","name":"JPMorgan Chase","category":"Banks"},{"symbol":"BAC","name":"Bank of America","category":"Banks"},{"symbol":"WFC","name":"Wells Fargo","category":"Banks"},{"symbol":"GS","name":"Goldman Sachs","category":"Banks"},{"symbol":"MS","name":"Morgan Stanley","category":"Banks"},{"symbol":"SAN","name":"Banco Santander","category":"Banks"},{"symbol":"BBVA","name":"BBVA","category":"Banks"},
    {"symbol":"GC=F","name":"Gold Futures","category":"Commodities"},{"symbol":"SI=F","name":"Silver Futures","category":"Commodities"},{"symbol":"CL=F","name":"WTI Crude Oil","category":"Commodities"},{"symbol":"BZ=F","name":"Brent Crude Oil","category":"Commodities"},{"symbol":"HG=F","name":"Copper Futures","category":"Commodities"},{"symbol":"PL=F","name":"Platinum Futures","category":"Commodities"},
    {"symbol":"SPY","name":"S&P 500 ETF","category":"ETFs"},{"symbol":"QQQ","name":"Nasdaq 100 ETF","category":"ETFs"},{"symbol":"DIA","name":"Dow Jones ETF","category":"ETFs"},{"symbol":"VTI","name":"Total US Market ETF","category":"ETFs"},{"symbol":"VEA","name":"Developed Markets ETF","category":"ETFs"},{"symbol":"AGG","name":"US Bond ETF","category":"Bonds"},{"symbol":"TLT","name":"20+ Year Treasury ETF","category":"Bonds"},{"symbol":"BND","name":"Total Bond Market ETF","category":"Bonds"},
    {"symbol":"^GSPC","name":"S&P 500","category":"Indices"},{"symbol":"^IXIC","name":"NASDAQ Composite","category":"Indices"},{"symbol":"^DJI","name":"Dow Jones","category":"Indices"},{"symbol":"^STOXX50E","name":"Euro Stoxx 50","category":"Indices"},{"symbol":"^FTSE","name":"FTSE 100","category":"Indices"},{"symbol":"^GDAXI","name":"DAX","category":"Indices"},
    {"symbol":"EURUSD=X","name":"EUR / USD","category":"Forex"},{"symbol":"GBPUSD=X","name":"GBP / USD","category":"Forex"},{"symbol":"JPY=X","name":"USD / JPY","category":"Forex"},{"symbol":"EURGBP=X","name":"EUR / GBP","category":"Forex"}
]
LOOKUP = {a["symbol"]:a for a in UNIVERSE}

async def yahoo_chart(client, symbol, period="1d", interval="5m"):
    url = f"{YAHOO}/v8/finance/chart/{symbol}"
    response = await client.get(url, params={"range":period,"interval":interval}, headers=HEADERS)
    response.raise_for_status()
    result = response.json()["chart"]["result"]
    if not result: raise ValueError("No market data")
    item = result[0]
    quote = item["indicators"]["quote"][0]
    closes = quote.get("close") or []
    valid = [x for x in closes if x is not None]
    price = item["meta"].get("regularMarketPrice") or (valid[-1] if valid else None)
    previous = item["meta"].get("chartPreviousClose") or item["meta"].get("previousClose")
    change = ((price-previous)/previous*100) if price is not None and previous else None
    return {"price":price,"previous":previous,"change":change,"currency":item["meta"].get("currency","USD"),"timestamps":item.get("timestamp",[]),"closes":closes}

@app.get("/health")
def health(): return {"status":"ok"}

@app.get("/api/market")
async def market():
    async with httpx.AsyncClient(timeout=15) as client:
        async def one(a):
            try:
                d=await yahoo_chart(client,a["symbol"])
                return {**a,**{k:d[k] for k in ("price","previous","change","currency")}}
            except Exception:
                return {**a,"price":None,"previous":None,"change":None,"currency":"USD"}
        rows=await asyncio.gather(*(one(a) for a in UNIVERSE))
    valid=[x for x in rows if x["change"] is not None]
    return {"assets":rows,"gainers":sorted(valid,key=lambda x:x["change"],reverse=True)[:5],"losers":sorted(valid,key=lambda x:x["change"])[:5],"updated":int(time.time())}

@app.get("/api/chart/{symbol:path}")
async def chart(symbol:str, period:str="1mo", interval:str="1d"):
    symbol=symbol.upper()
    if symbol not in LOOKUP: raise HTTPException(404,"Unsupported symbol")
    allowed={"1d":{"1m","5m","15m","30m"},"5d":{"5m","15m","30m","1h"},"1mo":{"30m","1h","1d"},"3mo":{"1h","1d"},"6mo":{"1d","1wk"},"1y":{"1d","1wk"},"5y":{"1wk","1mo"}}
    if period not in allowed or interval not in allowed[period]: raise HTTPException(400,"Unsupported period or interval")
    try:
        async with httpx.AsyncClient(timeout=18) as client: d=await yahoo_chart(client,symbol,period,interval)
        return {"symbol":symbol,"timestamps":d["timestamps"],"prices":d["closes"],"currency":d["currency"]}
    except Exception as e: raise HTTPException(502,"Market data provider unavailable")

@app.get("/", response_class=HTMLResponse)
def home(): return PAGE

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#080d15"><title>FinancePro — Global Market Intelligence</title><script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
:root{color-scheme:dark;--bg:#080d15;--panel:#101a27;--panel2:#142233;--line:#26384b;--muted:#8da0b5;--green:#4de0a0;--red:#ff7185;--blue:#83b5ff}*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 70% -15%,#173c3c 0,transparent 35%),var(--bg);color:#eef4fb;font:14px Inter,system-ui,sans-serif}.shell{max-width:1440px;margin:auto;padding:22px 26px}header{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line);padding:8px 0 20px}.brand{font-size:21px;font-weight:850;letter-spacing:-.6px}.brand span{color:var(--green)}.sub{font-size:9px;color:var(--muted);letter-spacing:2px;margin-top:4px}.live{color:var(--green);font-size:10px;letter-spacing:1.5px}.hero{display:flex;justify-content:space-between;align-items:end;padding:35px 0 25px}.eyebrow{font-size:10px;color:var(--green);font-weight:800;letter-spacing:1.8px}.hero h1{font-size:clamp(32px,4vw,48px);margin:8px 0;letter-spacing:-1.5px}.hero p,.muted{color:var(--muted)}.toolbar{display:flex;gap:9px;align-items:center}.btn,select,input{background:#132235;border:1px solid var(--line);color:#eef4fb;border-radius:9px;padding:10px 12px}.btn{cursor:pointer}.btn.primary{background:var(--green);color:#07140f;border:0;font-weight:800}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.card,.panel{background:linear-gradient(145deg,#142131,#0e1722);border:1px solid var(--line);border-radius:14px;padding:17px}.metric{font-size:24px;font-weight:800;margin:9px 0 3px}.positive{color:var(--green)}.negative{color:var(--red)}.section{display:flex;justify-content:space-between;align-items:end;margin:25px 0 12px}.section h2{margin:5px 0;font-size:21px}.layout{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(280px,.8fr);gap:14px}.chartbox{height:310px;position:relative}.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:12px 0}.tab{border:1px solid var(--line);background:#101a27;color:var(--muted);border-radius:8px;padding:8px 12px;cursor:pointer}.tab.active{background:#1c493c;color:var(--green);border-color:#286c55}.tablewrap{overflow:auto}table{width:100%;border-collapse:collapse;min-width:570px}th,td{text-align:left;padding:12px 9px;border-bottom:1px solid #233447}th{font-size:10px;color:var(--muted);letter-spacing:1px}td:last-child,th:last-child{text-align:right}.asset{font-weight:750}.ticker{font-size:11px;color:var(--muted);margin-top:3px}.row{display:flex;justify-content:space-between;gap:12px;padding:12px 0;border-bottom:1px solid var(--line)}.row:last-child{border:0}.search{width:min(260px,45vw)}.portfolio-form{display:grid;grid-template-columns:1fr 1fr 1fr auto;gap:8px;margin:12px 0}.portfolio-form input{min-width:0;width:100%}.small{font-size:11px;color:var(--muted)}.footer{color:var(--muted);font-size:11px;padding:24px 0}.tag{font-size:10px;padding:4px 7px;background:#203246;border-radius:6px;color:#bdd0e5}.loading{color:var(--muted);padding:24px}.watchlist{max-height:300px;overflow:auto}.disclaimer{font-size:11px;color:var(--muted);line-height:1.6}@media(max-width:900px){.cards{grid-template-columns:repeat(2,1fr)}.layout{grid-template-columns:1fr}}@media(max-width:600px){.shell{padding:14px}.hero{align-items:start;gap:12px;flex-direction:column}.toolbar{width:100%;flex-wrap:wrap}.portfolio-form{grid-template-columns:1fr 1fr}.cards{gap:8px}.metric{font-size:20px}}
</style></head><body><div class="shell">
<header><div><div class="brand">↗ Finance<span>Pro</span></div><div class="sub">GLOBAL MARKET INTELLIGENCE PLATFORM</div></div><div class="live">● LIVE DATA · <span id="clock">CONNECTING</span></div></header>
<section class="hero"><div><div class="eyebrow">YOUR GLOBAL FINANCIAL COMMAND CENTER</div><h1>See the whole market.</h1><p>Track crypto, stocks, banks, commodities, ETFs, bonds, indices and currencies.</p></div><div class="toolbar"><input id="search" class="search" placeholder="Search assets or tickers…"><button class="btn primary" onclick="refresh()">↻ Refresh</button></div></section>
<div class="cards"><div class="card"><div class="small">TRACKED MARKETS</div><div class="metric" id="count">—</div><div class="small">Across 7 asset classes</div></div><div class="card"><div class="small">TOP DAILY GAINER</div><div class="metric positive" id="topGain">—</div><div class="small" id="topGainName">Waiting for data</div></div><div class="card"><div class="small">TOP DAILY LOSER</div><div class="metric negative" id="topLoss">—</div><div class="small" id="topLossName">Waiting for data</div></div><div class="card"><div class="small">LAST MARKET UPDATE</div><div class="metric" style="font-size:18px" id="updated">—</div><div class="small">Auto-refresh every 60 seconds</div></div></div>
<div class="section"><div><div class="eyebrow">MARKET EXPLORER</div><h2>Global assets</h2></div><span class="small">Indicative market quotes · USD where available</span></div>
<div class="tabs" id="tabs"></div><div class="panel tablewrap"><table><thead><tr><th>ASSET</th><th>PRICE</th><th>DAY CHANGE</th><th>ASSET CLASS</th></tr></thead><tbody id="assets"><tr><td colspan="4" class="loading">Loading global markets…</td></tr></tbody></table></div>
<div class="section"><div><div class="eyebrow">PRICE ACTION</div><h2 id="chartTitle">Bitcoin · BTC-USD</h2></div><div class="toolbar"><select id="period"><option value="1d">1 Day</option><option value="5d">5 Days</option><option value="1mo" selected>1 Month</option><option value="3mo">3 Months</option><option value="6mo">6 Months</option><option value="1y">1 Year</option><option value="5y">5 Years</option></select></div></div>
<div class="layout"><div class="panel"><div class="chartbox"><canvas id="priceChart"></canvas></div><div class="small" id="chartNote">Select any supported asset in the market table to inspect its price history.</div></div><div class="panel"><div class="eyebrow">MARKET LEADERS</div><h3>Top movers today</h3><div id="movers" class="watchlist"><div class="loading">Calculating market movers…</div></div><div class="eyebrow" style="margin-top:22px">LONG-TERM VIEW</div><p class="disclaimer">Use the 6-month, 1-year and 5-year chart ranges to compare longer-term price trends. Past performance does not predict future returns.</p></div></div>
<div class="section"><div><div class="eyebrow">PERSONAL TRACKER</div><h2>My portfolio</h2></div><span class="small">Saved locally in this browser</span></div><div class="panel"><form class="portfolio-form" id="add"><input id="pSymbol" placeholder="Ticker (AAPL, BTC-USD)" required><input id="pQty" type="number" min="0.000001" step="any" placeholder="Quantity" required><input id="pCost" type="number" min="0" step="any" placeholder="Average buy price (USD)" required><button class="btn primary">Add position</button></form><div id="portfolio"></div><div class="row"><b>Estimated portfolio value</b><b id="portfolioValue">—</b></div></div>
<div class="footer"><b>FINANCEPRO</b> · Global markets, one view. Data provided by Yahoo Finance public chart endpoints. Coverage is a curated watchlist, not every security or bank worldwide. Some exchanges may be delayed or unavailable. This is an information tool, not financial advice. No automatic buy/sell signals or guaranteed “best investments”.</div></div>
<script>
const $=id=>document.getElementById(id),money=(n,c='USD')=>n==null?'—':new Intl.NumberFormat('en-US',{style:'currency',currency:c,maximumFractionDigits:n<1?6:2}).format(n),pct=n=>n==null?'—':(n>=0?'+':'')+n.toFixed(2)+'%',esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let all=[],category='All',selected='BTC-USD',chart=null,portfolio=JSON.parse(localStorage.getItem('fp_portfolio_v2')||'[]');
const cats=['All','Crypto','Stocks','Banks','Commodities','ETFs','Bonds','Indices','Forex'];
$('tabs').innerHTML=cats.map(c=>'<button class="tab '+(c==='All'?'active':'')+'" data-cat="'+c+'">'+c+'</button>').join('');
$('tabs').addEventListener('click',e=>{let b=e.target.closest('button[data-cat]');if(!b)return;category=b.dataset.cat;document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x===b));renderAssets();});
$('search').addEventListener('input',renderAssets);
function renderAssets(){let q=$('search').value.toLowerCase();let rows=all.filter(a=>(category==='All'||a.category===category)&&((a.name+' '+a.symbol+' '+a.category).toLowerCase().includes(q)));$('assets').innerHTML=rows.map(a=>'<tr data-symbol="'+esc(a.symbol)+'" style="cursor:pointer"><td><div class="asset">'+esc(a.name)+'</div><div class="ticker">'+esc(a.symbol)+'</div></td><td>'+money(a.price,a.currency)+'</td><td class="'+(a.change>=0?'positive':'negative')+'">'+pct(a.change)+'</td><td><span class="tag">'+a.category+'</span></td></tr>').join('')||'<tr><td colspan="4" class="loading">No matching assets found.</td></tr>';}
$('assets').addEventListener('click',e=>{let tr=e.target.closest('tr[data-symbol]');if(tr)selectAsset(tr.dataset.symbol);});
async function refresh(){ $('updated').textContent='Updating…';try{let d=await fetch('/api/market').then(r=>{if(!r.ok)throw Error();return r.json()});all=d.assets;$('count').textContent=all.filter(a=>a.price!=null).length;$('topGain').textContent=d.gainers[0]?pct(d.gainers[0].change):'—';$('topGainName').textContent=d.gainers[0]?.name||'—';$('topLoss').textContent=d.losers[0]?pct(d.losers[0].change):'—';$('topLossName').textContent=d.losers[0]?.name||'—';$('updated').textContent=new Date(d.updated*1000).toLocaleTimeString();$('clock').textContent='UPDATED';$('movers').innerHTML=[...d.gainers.slice(0,3),...d.losers.slice(0,3)].map(a=>'<div class="row"><span><b>'+esc(a.symbol)+'</b><br><span class="small">'+esc(a.name)+'</span></span><b class="'+(a.change>=0?'positive':'negative')+'">'+pct(a.change)+'</b></div>').join('');renderAssets();renderPortfolio();}catch(e){$('updated').textContent='Data unavailable';$('clock').textContent='RETRY';}}
async function selectAsset(symbol){selected=symbol;let a=all.find(x=>x.symbol===symbol);$('chartTitle').textContent=(a?.name||symbol)+' · '+symbol;await loadChart();}
async function loadChart(){let p=$('period').value;try{let d=await fetch('/api/chart/'+encodeURIComponent(selected)+'?period='+p+'&interval='+ (p==='1d'?'5m':p==='5d'?'15m':p==='5y'?'1wk':'1d')).then(r=>{if(!r.ok)throw Error();return r.json()});let points=d.timestamps.map((t,i)=>({x:new Date(t*1000),y:d.prices[i]})).filter(x=>x.y!=null);if(chart)chart.destroy();chart=new Chart($('priceChart'),{type:'line',data:{datasets:[{data:points,borderColor:'#4de0a0',backgroundColor:'rgba(77,224,160,.10)',fill:true,tension:.22,pointRadius:0,borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,parsing:false,plugins:{legend:{display:false},tooltip:{mode:'index',intersect:false}},scales:{x:{type:'time',time:{unit:p==='1d'?'hour':'day'},ticks:{color:'#8da0b5',maxTicksLimit:7},grid:{color:'#1d2b3b'}},y:{ticks:{color:'#8da0b5'},grid:{color:'#1d2b3b'}}}}});$('chartNote').textContent='Historical market prices · '+p+' · '+points.length+' observations';}catch(e){$('chartNote').textContent='Historical chart is temporarily unavailable for this asset.';}}
$('period').addEventListener('change',loadChart);
function renderPortfolio(){let total=0;$('portfolio').innerHTML=portfolio.map((p,i)=>{let a=all.find(x=>x.symbol===p.symbol),price=a?.price??p.cost,value=price*p.qty;total+=value;let pnl=(price-p.cost)*p.qty;return '<div class="row"><span><b>'+esc(p.symbol)+'</b><br><span class="small">'+p.qty+' units · cost '+money(p.cost)+'</span></span><span style="text-align:right"><b>'+money(value)+'</b><br><span class="'+(pnl>=0?'positive':'negative')+' small">'+(pnl>=0?'+':'')+money(pnl)+'</span></span><button class="btn" data-remove="'+i+'">Remove</button></div>'}).join('')||'<p class="muted">No positions yet. Add a ticker and quantity above.</p>';$('portfolioValue').textContent=money(total);}
$('add').addEventListener('submit',e=>{e.preventDefault();let symbol=$('pSymbol').value.trim().toUpperCase(),qty=Number($('pQty').value),cost=Number($('pCost').value);if(!symbol||qty<=0||cost<0)return;portfolio.push({symbol,qty,cost});localStorage.setItem('fp_portfolio_v2',JSON.stringify(portfolio));$('add').reset();renderPortfolio();});
$('portfolio').addEventListener('click',e=>{let b=e.target.closest('[data-remove]');if(!b)return;portfolio.splice(Number(b.dataset.remove),1);localStorage.setItem('fp_portfolio_v2',JSON.stringify(portfolio));renderPortfolio();});
refresh().then(()=>loadChart());setInterval(refresh,60000);setInterval(()=>$('clock').textContent='LIVE',1000);
</script></body></html>"""
