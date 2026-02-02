// Crypto Hunter JavaScript

// Auto-refresh data every 30 seconds
let refreshInterval;

function startAutoRefresh() {
    if (refreshInterval) clearInterval(refreshInterval);
    
    refreshInterval = setInterval(() => {
        if (window.location.pathname === '/' || window.location.pathname === '/market') {
            location.reload();
        }
    }, 30000); // 30 seconds
}

// Format numbers
function formatNumber(num) {
    if (num >= 1000000000) {
        return '$' + (num / 1000000000).toFixed(2) + 'B';
    }
    if (num >= 1000000) {
        return '$' + (num / 1000000).toFixed(2) + 'M';
    }
    if (num >= 1000) {
        return '$' + (num / 1000).toFixed(2) + 'K';
    }
    return '$' + num.toFixed(2);
}

// Format percentage
function formatPercent(num) {
    const color = num >= 0 ? 'success' : 'danger';
    const icon = num >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';
    return `<span class="text-${color}"><i class="fas ${icon}"></i> ${Math.abs(num).toFixed(2)}%</span>`;
}

// Update prices in real-time (simulated)
function simulatePriceUpdates() {
    const priceElements = document.querySelectorAll('.crypto-price');
    
    priceElements.forEach(element => {
        const currentPrice = parseFloat(element.textContent.replace(/[^0-9.-]+/g, ""));
        const change = (Math.random() - 0.5) * 0.02; // ±1% change
        const newPrice = currentPrice * (1 + change);
        
        element.textContent = formatNumber(newPrice);
        
        // Update change indicator
        const changeElement = element.parentElement.querySelector('.price-change');
        if (changeElement) {
            changeElement.innerHTML = formatPercent(change * 100);
        }
    });
}

// Portfolio calculations
function calculatePortfolioStats() {
    const rows = document.querySelectorAll('.portfolio-row');
    let totalValue = 0;
    let totalInvested = 0;
    
    rows.forEach(row => {
        const quantity = parseFloat(row.dataset.quantity);
        const avgPrice = parseFloat(row.dataset.avgPrice);
        const currentPrice = parseFloat(row.dataset.currentPrice);
        
        const invested = quantity * avgPrice;
        const value = quantity * currentPrice;
        const profit = value - invested;
        const profitPercent = (profit / invested) * 100;
        
        totalInvested += invested;
        totalValue += value;
        
        // Update row
        const profitElement = row.querySelector('.profit-loss');
        if (profitElement) {
            profitElement.textContent = formatNumber(profit);
            profitElement.className = 'profit-loss ' + (profit >= 0 ? 'text-success' : 'text-danger');
        }
        
        const percentElement = row.querySelector('.profit-percent');
        if (percentElement) {
            percentElement.innerHTML = formatPercent(profitPercent);
        }
    });
    
    // Update totals
    const totalProfit = totalValue - totalInvested;
    const totalProfitPercent = (totalProfit / totalInvested) * 100;
    
    document.getElementById('totalValue').textContent = formatNumber(totalValue);
    document.getElementById('totalProfit').innerHTML = formatPercent(totalProfitPercent);
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    startAutoRefresh();
    
    // Start simulated updates on market page
    if (window.location.pathname === '/market') {
        setInterval(simulatePriceUpdates, 10000); // Update every 10 seconds
    }
    
    // Calculate portfolio stats
    if (window.location.pathname === '/portfolio') {
        calculatePortfolioStats();
    }
    
    // Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Favorite functionality
function toggleFavorite(coinId) {
    let favorites = JSON.parse(localStorage.getItem('cryptoFavorites') || '[]');
    
    if (favorites.includes(coinId)) {
        favorites = favorites.filter(id => id !== coinId);
        localStorage.setItem('cryptoFavorites', JSON.stringify(favorites));
        return false;
    } else {
        favorites.push(coinId);
        localStorage.setItem('cryptoFavorites', JSON.stringify(favorites));
        return true;
    }
}

// Get favorites
function getFavorites() {
    return JSON.parse(localStorage.getItem('cryptoFavorites') || '[]');
          }
