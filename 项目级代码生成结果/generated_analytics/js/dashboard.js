
// 销售仪表板核心逻辑
class SalesDashboard {
    constructor() {
        this.charts = {};
        this.currentData = {};
        this.init();
    }
    
    init() {
        this.loadSampleData();
        this.initCharts();
        this.setupEventListeners();
        this.startRealTimeUpdates();
    }
    
    loadSampleData() {
        // 使用示例数据或从API加载
        this.currentData = window.sampleSalesData || this.generateSampleData();
        this.updateKPIs();
    }
    
    generateSampleData() {
        return {
            sales: {
                total: 125430,
                change: 12.5,
                trend: [12000, 19000, 15000, 18000, 22000, 25000, 30000]
            },
            orders: {
                total: 1234,
                change: 8.3,
                trend: [1000, 1100, 1200, 1150, 1300, 1250, 1234]
            },
            products: [
                { name: '产品A', value: 35, color: '#FF6384' },
                { name: '产品B', value: 25, color: '#36A2EB' },
                { name: '产品C', value: 20, color: '#FFCE56' },
                { name: '产品D', value: 20, color: '#4BC0C0' }
            ],
            regions: [
                { name: '北部', value: 40, color: '#9966FF' },
                { name: '南部', value: 35, color: '#FF9F40' },
                { name: '东部', value: 25, color: '#FF6384' }
            ]
        };
    }
    
    initCharts() {
        // 销售趋势图
        this.charts.salesTrend = new Chart(
            document.getElementById('salesTrendChart'),
            {
                type: 'line',
                data: {
                    labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
                    datasets: [{
                        label: '销售额',
                        data: this.currentData.sales.trend,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            }
        );
        
        // 产品分布图
        this.charts.productDistribution = new Chart(
            document.getElementById('productDistributionChart'),
            {
                type: 'doughnut',
                data: {
                    labels: this.currentData.products.map(p => p.name),
                    datasets: [{
                        data: this.currentData.products.map(p => p.value),
                        backgroundColor: this.currentData.products.map(p => p.color)
                    }]
                }
            }
        );
        
        // 区域销售图
        this.charts.regionSales = new Chart(
            document.getElementById('regionSalesChart'),
            {
                type: 'bar',
                data: {
                    labels: this.currentData.regions.map(r => r.name),
                    datasets: [{
                        label: '销售额',
                        data: this.currentData.regions.map(r => r.value),
                        backgroundColor: this.currentData.regions.map(r => r.color)
                    }]
                }
            }
        );
    }
    
    updateKPIs() {
        document.getElementById('totalSales').textContent = 
            '¥' + this.currentData.sales.total.toLocaleString();
        document.getElementById('totalOrders').textContent = 
            this.currentData.orders.total.toLocaleString();
        document.getElementById('avgOrder').textContent = 
            '¥' + Math.round(this.currentData.sales.total / this.currentData.orders.total).toLocaleString();
        
        // 更新变化百分比
        this.updateChangeIndicator('salesChange', this.currentData.sales.change);
        this.updateChangeIndicator('ordersChange', this.currentData.orders.change);
    }
    
    updateChangeIndicator(elementId, change) {
        const element = document.getElementById(elementId);
        element.textContent = (change > 0 ? '+' : '') + change + '%';
        element.className = 'kpi-change ' + (change >= 0 ? 'positive' : 'negative');
    }
    
    setupEventListeners() {
        // 时间范围筛选
        document.getElementById('timeRange').addEventListener('change', (e) => {
            this.filterData('timeRange', e.target.value);
        });
        
        // 区域筛选
        document.getElementById('regionFilter').addEventListener('change', (e) => {
            this.filterData('region', e.target.value);
        });
        
        // 刷新按钮
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.refreshData();
        });
    }
    
    filterData(type, value) {
        console.log('筛选数据:', type, value);
        // 实际项目中这里会调用API或过滤数据
        this.simulateDataUpdate();
    }
    
    refreshData() {
        this.simulateDataUpdate();
        // 显示加载状态
        const btn = document.getElementById('refreshBtn');
        btn.textContent = '刷新中...';
        btn.disabled = true;
        
        setTimeout(() => {
            btn.textContent = '刷新数据';
            btn.disabled = false;
        }, 1000);
    }
    
    startRealTimeUpdates() {
        // 模拟实时数据更新
        setInterval(() => {
            this.simulateRealTimeTransaction();
        }, 5000);
    }
    
    simulateRealTimeTransaction() {
        const transactionsContainer = document.querySelector('.transaction-list');
        if (transactionsContainer) {
            const products = ['产品A', '产品B', '产品C', '产品D'];
            const regions = ['北部', '南部', '东部'];
            const amount = Math.floor(Math.random() * 1000) + 100;
            
            const transaction = document.createElement('div');
            transaction.className = 'transaction-item';
            transaction.innerHTML = `
                <span>${products[Math.floor(Math.random() * products.length)]}</span>
                <span>¥${amount}</span>
                <span>${regions[Math.floor(Math.random() * regions.length)]}</span>
            `;
            
            transactionsContainer.insertBefore(transaction, transactionsContainer.firstChild);
            
            // 限制显示数量
            if (transactionsContainer.children.length > 10) {
                transactionsContainer.removeChild(transactionsContainer.lastChild);
            }
        }
    }
    
    simulateDataUpdate() {
        // 模拟数据更新
        const change = (Math.random() - 0.5) * 10;
        this.currentData.sales.change = parseFloat(change.toFixed(1));
        this.updateKPIs();
    }
}

// 页面加载完成后初始化仪表板
document.addEventListener('DOMContentLoaded', function() {
    new SalesDashboard();
});
        