import time
import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="FinancePro")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/market")
async def market():
    assets = []
    async with httpx.AsyncClient(timeout=12) as client:
        for symbol in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
            try:
                response = await client.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": symbol})
                response.raise_for_status()
                assets.append({"symbol": symbol[:-4], "price": float(response.json()["price"])})
            except Exception:
                assets.append({"symbol": symbol[:-4], "price": None})
        try:
            response = await client.get("https://api.frankfurter.app/latest", params={"from": "USD", "to": "EUR"})
            response.raise_for_status()
            fx = response.json()["rates"]["EUR"]
        except Exception:
            fx = None
    return {"assets": assets, "usd_eur": fx, "updated": int(time.time())}

@app.get("/", response_class=HTMLResponse)
def home():
    return PAGE

PAGE = r"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#090e16"><meta name="description" content="FinancePro — инвестиции, рынок и портфель под контролем"><title>FinancePro — Investment Intelligence</title>
<style>
:root{color-scheme:dark;--bg:#090e16;--panel:#111b28;--line:#263649;--muted:#8d9caf;--green:#56e1a2;--blue:#85b4ff}*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 78% -8%,#1b3b45 0,transparent 39%),var(--bg);color:#f3f6fb;font:15px Inter,system-ui,-apple-system,sans-serif}.wrap{max-width:1180px;margin:auto;padding:26px 22px}header{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line);padding-bottom:20px}.brand{display:flex;gap:12px;align-items:center;font-size:20px;font-weight:800}.logo{background:#173b35;color:var(--green);border-radius:12px;padding:10px;font-size:22px}.sub{display:block;color:var(--muted);font-size:9px;letter-spacing:2px;margin-top:3px}.live,.eyebrow{color:var(--green);font-size:10px;letter-spacing:1.8px;font-weight:750}.hero{display:flex;justify-content:space-between;align-items:center;padding:56px 0 38px}.hero h1{font-size:clamp(42px,6vw,70px);line-height:1.02;letter-spacing:-2px;margin:13px 0}.hero h1 em{font-style:normal;color:var(--green)}.hero p{color:var(--muted);font-size:17px}.orb{width:145px;height:145px;border:1px solid #397b68;border-radius:50%;display:grid;place-items:center;font-size:75px;color:var(--green);box-shadow:0 0 80px #1a735444,inset 0 0 30px #1a735422}.section{display:flex;justify-content:space-between;align-items:end;margin:24px 0 14px}h2{font-size:24px;margin:5px 0}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.panel{background:linear-gradient(145deg,#152131,#101823);border:1px solid var(--line);border-radius:17px;padding:20px}.quote{display:flex;align-items:center;gap:13px}.coin{width:42px;height:42px;border-radius:13px;background:#20364a;display:grid;place-items:center;color:var(--blue);font-weight:800;font-size:19px}.meta{flex:1}.meta b{display:block}.muted,small{color:var(--muted)}.price{font-size:20px;font-weight:800}.content{display:grid;grid-template-columns:1.35fr 1fr;gap:16px;margin-top:25px}.form{display:grid;grid-template-columns:1fr 1fr 1fr auto;gap:8px;margin:15px 0}input{background:#0a111b;border:1px solid var(--line);border-radius:10px;color:white;padding:12px;min-width:0;width:100%}button{border:0;border-radius:10px;background:var(--green);color:#08140f;font-weight:800;padding:12px 16px;cursor:pointer}button.secondary{background:#203246;color:#eaf1fb}.row{display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid var(--line)}.delete{background:transparent;color:#ff9292;padding:5px}.note{color:var(--green);min-height:22px;font-size:13px}.foot{margin:34px 0 8px;color:var(--muted);font-size:11px;display:flex;justify-content:space-between}.disclaimer{font-size:12px;color:var(--muted);line-height:1.6}@media(max-width:760px){.grid{grid-template-columns:1fr}.content{grid-template-columns:1fr}.orb{width:92px;height:92px;font-size:48px}.form{grid-template-columns:1fr 1fr}.hero{padding:40px 0 20px}.hero p{font-size:14px}}
</style></head><body><div class="wrap">
<header><div class="brand"><div class="logo">↗</div><div>FinancePro<span class="sub">INVESTMENT INTELLIGENCE</span></div></div><div class="live">● LIVE MARKET DATA</div></header>
<section class="hero"><div><div class="eyebrow">YOUR FINANCIAL COMMAND CENTER</div><h1>Инвестиции.<br><em>Под контролем.</em></h1><p>Рынки, портфель и аналитика — в одном пространстве.</p></div><div class="orb">€</div></section>
<div class="section"><div><div class="eyebrow">LIVE SNAPSHOT</div><h2>Рынок сегодня</h2></div><button onclick="load()">↻ Обновить</button></div><div class="grid" id="market"><div class="panel">Загружаем котировки…</div></div>
<div class="content"><section><div class="section"><div><div class="eyebrow">PORTFOLIO TRACKER</div><h2>Мой портфель</h2></div></div><div class="panel"><div class="muted">Добавить актив в портфель</div><form class="form" id="add"><input id="symbol" placeholder="Тикер (BTC, AAPL)" maxlength="12" required><input id="qty" type="number" min="0.000001" step="any" placeholder="Количество" required><input id="cost" type="number" min="0" step="any" placeholder="Средняя цена USD"><button>Добавить</button></form><div id="positions"></div><div class="note" id="note"></div></div></section>
<aside><div class="eyebrow">MARKET INTELLIGENCE</div><h2>Обзор</h2><div class="panel"><h3>Криптовалютный рынок</h3><p class="muted">Публичные спотовые котировки BTC, ETH и SOL.</p><div class="row"><span>USD → EUR</span><b id="fx">—</b></div><div class="row"><span>Источники</span><b>Binance · Frankfurter</b></div><p class="disclaimer">Котировки ориентировочные. FinancePro не является брокером и не предоставляет персональные инвестиционные рекомендации. Позиции портфеля сохраняются в браузере на этом устройстве.</p></div></aside></div>
<footer class="foot"><span>FINANCEPRO © 2026</span><span id="updated">Подключение к рынку…</span></footer></div>
<script>
const $=id=>document.getElementById(id),fmt=n=>n==null?'—':'$'+Number(n).toLocaleString('en-US',{maximumFractionDigits:2});let positions=JSON.parse(localStorage.getItem('fp_positions')||'[]');
function render(){ $('positions').innerHTML=positions.length?positions.map((p,i)=>'<div class="row"><span><b>'+esc(p.symbol)+'</b><br><small>'+p.qty+' units · средняя цена '+fmt(p.cost)+'</small></span><b>'+fmt(p.qty*p.cost)+'</b><button class="delete" onclick="removePosition('+i+')">✕</button></div>').join(''):'<p class="muted">Пока нет активов. Добавьте первую позицию.</p>'; }
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function removePosition(i){positions.splice(i,1);save();}
function save(){localStorage.setItem('fp_positions',JSON.stringify(positions));render();}
$('add').addEventListener('submit',e=>{e.preventDefault();const symbol=$('symbol').value.trim().toUpperCase(),qty=Number($('qty').value),cost=Number($('cost').value||0);if(!symbol||qty<=0||cost<0)return;$('note').textContent='Актив добавлен';positions.push({symbol,qty,cost});save();$('add').reset();});
async function load(){try{const d=await fetch('/api/market').then(r=>{if(!r.ok)throw Error();return r.json()});$('market').innerHTML=d.assets.map(a=>'<article class="panel quote"><div class="coin">'+(a.symbol==='BTC'?'₿':a.symbol==='ETH'?'◆':'◎')+'</div><div class="meta"><b>'+a.symbol+'/USDT</b><small>Криптовалюта</small></div><strong class="price">'+fmt(a.price)+'</strong></article>').join('');$('fx').textContent=d.usd_eur?Number(d.usd_eur).toFixed(4):'—';$('updated').textContent='Обновлено: '+new Date(d.updated*1000).toLocaleString();}catch(e){$('market').innerHTML='<div class="panel">Не удалось получить котировки. Попробуйте обновить.</div>'}}
render();load();setInterval(load,60000);
</script></body></html>"""
