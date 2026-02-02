from flask import Flask, render_template, jsonify, request
import requests
import random
import json
import time
from datetime import datetime

app = Flask(__name__)

# ==================== SAMPLE DATA (Works offline) ====================
SAMPLE_CRYPTOS = [
    {
        'id': 'bitcoin', 'symbol': 'BTC', 'name': 'Bitcoin',
        'price': 45230.50, 'change_24h': 2.5, 'market_cap': 885000000000,
        'volume': 28000000000, 'rank': 1,
        'image': 'https://cryptologos.cc/logos/bitcoin-btc-logo.png',
        'high_24h': 45500, 'low_24h': 44800
    },
    {
        'id': 'ethereum', 'symbol': 'ETH', 'name': 'Ethereum',
        'price': 2420.75, 'change_24h': 1.8, 'market_cap': 291000000000,
        'volume': 15000000000, 'rank': 2,
        'image': 'https://cryptologos.cc/logos/ethereum-eth-logo.png',
        'high_24h': 2450, 'low_24h': 2380
    },
    {
        'id': 'tether', 'symbol': 'USDT', 'name': 'Tether',
        'price': 1.00, 'change_24h': 0.0, 'market_cap': 95000000000,
        'volume': 50000000000, 'rank': 3,
        'image': 'https://cryptologos.cc/logos/tether-usdt-logo.png',
        'high_24h': 1.01, 'low_24h': 0.99
    },
    {
        'id': 'binance-coin', 'symbol': 'BNB', 'name': 'Binance Coin',
        'price': 305.20, 'change_24h': 3.2, 'market_cap': 47000000000,
        'volume': 1200000000, 'rank': 4,
        'image': 'https://cryptologos.cc/logos/binance-coin-bnb-logo.png',
        'high_24h': 310, 'low_24h': 300
    },
    {
        'id': 'solana', 'symbol': 'SOL', 'name': 'Solana',
        'price': 98.75, 'change_24h': 5.6, 'market_cap': 42000000000,
        'volume': 3500000000, 'rank': 5,
        'image': 'https://cryptologos.cc/logos/solana-sol-logo.png',
        'high_24h': 102, 'low_24h': 95
    },
    {
        'id': 'ripple', 'symbol': 'XRP', 'name': 'XRP',
        'price': 0.58, 'change_24h': -1.2, 'market_cap': 31000000000,
        'volume': 1200000000, 'rank': 6,
        'image': 'https://cryptologos.cc/logos/xrp-xrp-logo.png',
        'high_24h': 0.60, 'low_24h': 0.56
    },
    {
        'id': 'cardano', 'symbol': 'ADA', 'name': 'Cardano',
        'price': 0.52, 'change_24h': 0.8, 'market_cap': 18500000000,
        'volume': 450000000, 'rank': 7,
        'image': 'https://cryptologos.cc/logos/cardano-ada-logo.png',
        'high_24h': 0.53, 'low_24h': 0.50
    },
    {
        'id': 'avalanche', 'symbol': 'AVAX', 'name': 'Avalanche',
        'price': 36.80, 'change_24h': 2.3, 'market_cap': 13000000000,
        'volume': 600000000, 'rank': 8,
        'image': 'https://cryptologos.cc/logos/avalanche-avax-logo.png',
        'high_24h': 38, 'low_24h': 35
    },
    {
        'id': 'dogecoin', 'symbol': 'DOGE', 'name': 'Dogecoin',
        'price': 0.082, 'change_24h': 1.5, 'market_cap': 11700000000,
        'volume': 650000000, 'rank': 9,
        'image': 'https://cryptologos.cc/logos/dogecoin-doge-logo.png',
        'high_24h': 0.085, 'low_24h': 0.080
    },
    {
        'id': 'polkadot', 'symbol': 'DOT', 'name': 'Polkadot',
        'price': 7.20, 'change_24h': 2.1, 'market_cap': 9200000000,
        'volume': 280000000, 'rank': 10,
        'image': 'https://cryptologos.cc/logos/polkadot-new-dot-logo.png',
        'high_24h': 7.5, 'low_24h': 7.0
    }
]

# ==================== FREE API FUNCTIONS ====================
def get_live_crypto_data():
    """Try to get real data, fallback to sample data"""
    try:
        # Try CoinGecko (free, no API key needed)
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 50,
            'page': 1,
            'sparkline': 'false'
        }
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            formatted_data = []
            for coin in data[:20]:  # Limit to 20 coins
                formatted_data.append({
                    'id': coin['id'],
                    'symbol': coin['symbol'].upper(),
                    'name': coin['name'],
                    'price': coin['current_price'],
                    'change_24h': coin['price_change_percentage_24h'],
                    'market_cap': coin['market_cap'],
                    'volume': coin['total_volume'],
                    'rank': coin['market_cap_rank'],
                    'image': coin['image'],
                    'high_24h': coin['high_24h'],
                    'low_24h': coin['low_24h']
                })
            return formatted_data
    except:
        pass
    
    # Fallback: Sample data with small random variations (simulates live data)
    return get_sample_with_variations()

def get_sample_with_variations():
    """Return sample data with random variations"""
    result = []
    for coin in SAMPLE_CRYPTOS:
        # Add small random variation to simulate live data
        variation = random.uniform(-0.02, 0.02)
        price_change = coin['change_24h'] + random.uniform(-0.5, 0.5)
        
        result.append({
            'id': coin['id'],
            'symbol': coin['symbol'],
            'name': coin['name'],
            'price': coin['price'] * (1 + variation),
            'change_24h': round(price_change, 2),
            'market_cap': coin['market_cap'],
            'volume': coin['volume'],
            'rank': coin['rank'],
            'image': coin['image'],
            'high_24h': coin['high_24h'],
            'low_24h': coin['low_24h']
        })
    
    # Sort by rank
    result.sort(key=lambda x: x['rank'])
    return result

def get_crypto_detail(coin_id):
    """Get detailed info for a specific crypto"""
    try:
        # Try CoinGecko API
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        params = {'localization': 'false', 'tickers': 'false', 'market_data': 'true'}
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'id': data['id'],
                'symbol': data['symbol'].upper(),
                'name': data['name'],
                'price': data['market_data']['current_price']['usd'],
                'change_24h': data['market_data']['price_change_percentage_24h'],
                'market_cap': data['market_data']['market_cap']['usd'],
                'volume': data['market_data']['total_volume']['usd'],
                'rank': data['market_cap_rank'],
                'image': data['image']['large'],
                'description': data['description']['en'][:500] + '...' if data['description']['en'] else 'No description available',
                'high_24h': data['market_data']['high_24h']['usd'],
                'low_24h': data['market_data']['low_24h']['usd'],
                'ath': data['market_data']['ath']['usd'],
                'atl': data['market_data']['atl']['usd']
            }
    except:
        pass
    
    # Fallback to sample data
    for coin in SAMPLE_CRYPTOS:
        if coin['id'] == coin_id:
            return {
                **coin,
                'description': f"{coin['name']} is a leading cryptocurrency with strong market presence.",
                'ath': coin['price'] * 1.5,
                'atl': coin['price'] * 0.7
            }
    
    # Default if not found
    return SAMPLE_CRYPTOS[0]

def get_market_stats():
    """Get overall market statistics"""
    cryptos = get_live_crypto_data()
    
    total_market_cap = sum(c['market_cap'] for c in cryptos if c['market_cap'])
    total_volume = sum(c['volume'] for c in cryptos if c['volume'])
    
    # Calculate market sentiment
    positive = sum(1 for c in cryptos if c['change_24h'] > 0)
    negative = sum(1 for c in cryptos if c['change_24h'] < 0)
    
    sentiment = "Bullish" if positive > negative else "Bearish"
    
    return {
        'total_market_cap': total_market_cap,
        'total_volume': total_volume,
        'total_cryptos': len(cryptos),
        'market_cap_change': 1.8,  # Sample
        'sentiment': sentiment,
        'btc_dominance': 52.3,
        'fear_greed': 68,
        'positive_coins': positive,
        'negative_coins': negative
    }

# ==================== ROUTES ====================
@app.route('/')
def home():
    """Home page"""
    market_stats = get_market_stats()
    cryptos = get_live_crypto_data()[:10]  # Show top 10
    
    # Get top gainers and losers
    gainers = sorted(cryptos, key=lambda x: x['change_24h'], reverse=True)[:5]
    losers = sorted(cryptos, key=lambda x: x['change_24h'])[:5]
    
    return render_template('index.html',
                         market_stats=market_stats,
                         cryptos=cryptos[:6],
                         gainers=gainers,
                         losers=losers)

@app.route('/market')
def market():
    """All cryptocurrencies market"""
    cryptos = get_live_crypto_data()
    
    # Sorting
    sort_by = request.args.get('sort', 'rank')
    order = request.args.get('order', 'asc')
    
    if sort_by == 'name':
        cryptos.sort(key=lambda x: x['name'].lower(), reverse=(order == 'desc'))
    elif sort_by == 'price':
        cryptos.sort(key=lambda x: x['price'], reverse=(order == 'desc'))
    elif sort_by == 'change':
        cryptos.sort(key=lambda x: x['change_24h'], reverse=(order == 'desc'))
    elif sort_by == 'volume':
        cryptos.sort(key=lambda x: x['volume'], reverse=(order == 'desc'))
    else:  # rank
        cryptos.sort(key=lambda x: x['rank'])
    
    return render_template('market.html',
                         cryptos=cryptos,
                         sort_by=sort_by,
                         order=order)

@app.route('/crypto/<coin_id>')
def crypto_detail(coin_id):
    """Individual cryptocurrency page"""
    coin = get_crypto_detail(coin_id)
    
    # Generate price history (simulated)
    days = 30
    base_price = coin['price']
    history = []
    
    for i in range(days, -1, -1):
        date = datetime.now().timestamp() - (i * 86400)
        # Simulate price movement
        if i == days:
            price = base_price * 0.9  # Start lower
        else:
            change = random.uniform(-0.05, 0.05)
            price = history[-1]['price'] * (1 + change)
        
        history.append({
            'time': date * 1000,  # Milliseconds for JavaScript
            'price': round(price, 2)
        })
    
    return render_template('crypto.html',
                         coin=coin,
                         history=history)

@app.route('/portfolio')
def portfolio():
    """Portfolio tracker (demo version)"""
    # Demo portfolio data
    demo_portfolio = [
        {'symbol': 'BTC', 'name': 'Bitcoin', 'amount': 0.5, 'buy_price': 42000, 'current_price': 45230},
        {'symbol': 'ETH', 'name': 'Ethereum', 'amount': 3.2, 'buy_price': 2300, 'current_price': 2420},
        {'symbol': 'SOL', 'name': 'Solana', 'amount': 25, 'buy_price': 85, 'current_price': 98.75},
        {'symbol': 'ADA', 'name': 'Cardano', 'amount': 1000, 'buy_price': 0.45, 'current_price': 0.52},
        {'symbol': 'DOGE', 'name': 'Dogecoin', 'amount': 5000, 'buy_price': 0.075, 'current_price': 0.082}
    ]
    
    # Calculate portfolio stats
    total_invested = 0
    total_current = 0
    
    for coin in demo_portfolio:
        invested = coin['amount'] * coin['buy_price']
        current = coin['amount'] * coin['current_price']
        
        coin['invested'] = round(invested, 2)
        coin['current_value'] = round(current, 2)
        coin['profit'] = round(current - invested, 2)
        coin['profit_percent'] = round(((current - invested) / invested) * 100, 2) if invested > 0 else 0
        
        total_invested += invested
        total_current += current
    
    total_profit = total_current - total_invested
    total_profit_percent = (total_profit / total_invested * 100) if total_invested > 0 else 0
    
    return render_template('portfolio.html',
                         portfolio=demo_portfolio,
                         total_invested=round(total_invested, 2),
                         total_current=round(total_current, 2),
                         total_profit=round(total_profit, 2),
                         total_profit_percent=round(total_profit_percent, 2))

# ==================== API ENDPOINTS ====================
@app.route('/api/crypto')
def api_crypto():
    """API endpoint for crypto data"""
    cryptos = get_live_crypto_data()
    return jsonify(cryptos)

@app.route('/api/crypto/<coin_id>')
def api_crypto_detail(coin_id):
    """API endpoint for specific crypto"""
    coin = get_crypto_detail(coin_id)
    return jsonify(coin)

@app.route('/api/search')
def search():
    """Search cryptocurrencies"""
    query = request.args.get('q', '').lower()
    if len(query) < 2:
        return jsonify([])
    
    cryptos = get_live_crypto_data()
    results = []
    
    for coin in cryptos:
        if (query in coin['name'].lower() or 
            query in coin['symbol'].lower() or
            query in coin['id'].lower()):
            results.append(coin)
    
    return jsonify(results[:10])

@app.route('/api/market/stats')
def market_stats_api():
    """API endpoint for market statistics"""
    stats = get_market_stats()
    return jsonify(stats)

# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# ==================== MAIN ====================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
