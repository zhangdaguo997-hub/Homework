import os
import re
import json
import time
from datetime import datetime
from core import interface
from utils import construct_system_message
from tools import global_tool_orchestrator
from .enhanced_role import EnhancedRole

class ProjectDeveloper(EnhancedRole):
    def __init__(self, team_description, developer_description, requirement, project_type,
                 model='deepseek-chat', majority=1, max_tokens=1024, temperature=0.2, top_p=0.95):
        super().__init__()
        
        self.model = model
        self.majority = majority
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.history_message = []
        self.requirement = requirement
        self.project_type = project_type
        self.feedback_history = []
        
        self.tool_orchestrator = global_tool_orchestrator

        self.itf = interface.ProgramInterface(
            stop='',
            verbose=False,
            model=self.model,
        )

        system_message = construct_system_message(requirement, developer_description, team_description)
        self.history_message_append(system_message)

    def _analyze_requirement_features(self, requirement):
        """深度分析需求特征，识别项目类型和功能需求"""
        requirement_lower = requirement.lower()
        
        features = {
            'project_type': 'generic',
            'primary_functions': [],
            'technical_requirements': [],
            'ui_components': [],
            'data_handling': 'static',
            'interactivity_level': 'basic'
        }
        
        # 作品集特征识别
        portfolio_keywords = ['portfolio', '作品集', 'showcase', 'personal website', '个人网站', '项目展示']
        if any(keyword in requirement_lower for keyword in portfolio_keywords):
            features.update({
                'project_type': 'portfolio',
                'primary_functions': ['project_display', 'contact_form', 'responsive_layout'],
                'ui_components': ['project_cards', 'navigation', 'contact_form', 'footer'],
                'data_handling': 'static',
                'interactivity_level': 'medium'
            })
        
        # 仪表板特征识别
        dashboard_keywords = ['dashboard', '仪表板', 'analytics', 'sales', '销售', 'chart', 'filter', 'real-time']
        if any(keyword in requirement_lower for keyword in dashboard_keywords):
            features.update({
                'project_type': 'dashboard',
                'primary_functions': ['data_visualization', 'filtering', 'real_time_updates', 'kpi_display'],
                'ui_components': ['charts_grid', 'filters_panel', 'kpi_cards', 'data_table'],
                'data_handling': 'dynamic',
                'interactivity_level': 'high'
            })
        
        # 数据探索器特征识别
        explorer_keywords = ['explorer', '探索', 'data visualization', 'interactive', 'multiple chart', 'chart types']
        if any(keyword in requirement_lower for keyword in explorer_keywords):
            features.update({
                'project_type': 'explorer',
                'primary_functions': ['multi_chart_display', 'interactive_filtering', 'data_exploration', 'chart_linking'],
                'ui_components': ['multiple_charts', 'control_panel', 'data_filters', 'detail_view'],
                'data_handling': 'dynamic',
                'interactivity_level': 'high'
            })
        
        # 根据关键词细化功能需求
        if 'contact' in requirement_lower or '联系' in requirement_lower:
            features['primary_functions'].append('contact_form')
        if 'real-time' in requirement_lower or '实时' in requirement_lower:
            features['data_handling'] = 'real_time'
        if 'responsive' in requirement_lower or '响应式' in requirement_lower:
            features['ui_components'].append('responsive_design')
        
        return features

    def implement_project(self, architecture_plan, ui_design=None, existing_files=None, is_initial=True):
        """修复版本：需求感知的项目实现"""
        
        requirement_features = self._analyze_requirement_features(self.requirement)
        print(f"🎯 需求特征分析: {requirement_features['project_type']}类型项目")
        
        if is_initial:
            implementation_prompt = self._create_customized_prompt(requirement_features, architecture_plan, ui_design)
        else:
            implementation_prompt = self._create_iteration_prompt(requirement_features, existing_files)
        
        self.history_message_append(implementation_prompt)
        
        try:
            responses = self.itf.run(prompt=self.history_message, majority_at=self.majority,
                                   max_tokens=self.max_tokens, temperature=self.temperature, top_p=self.top_p)
        except Exception as e:
            print(f"❌ 项目实现失败: {e}")
            return self._create_demand_aware_fallback(requirement_features)
        
        implementation = responses[0]
        self.history_message_append(implementation, "assistant")
        
        project_files = self._deep_enhanced_parse(implementation, requirement_features)
        
        return project_files

    def _create_customized_prompt(self, features, architecture_plan, ui_design):
        """创建需求定制的提示词"""
        
        project_type = features['project_type']
        base_prompt = f"""
        CRITICAL: 根据需求特征生成{project_type}类型的专用代码！

        需求分析结果: {features}
        架构计划: {architecture_plan}
        {f"UI设计: {ui_design}" if ui_design else ""}

        必须生成完整的、功能差异化的代码！
        """
        
        type_specific_prompts = {
            'portfolio': self._get_portfolio_prompt(),
            'dashboard': self._get_dashboard_prompt(), 
            'explorer': self._get_explorer_prompt(),
            'generic': self._get_generic_prompt()
        }
        
        prompt = base_prompt + type_specific_prompts.get(project_type, self._get_generic_prompt())
        return prompt

    def _get_portfolio_prompt(self):
        """作品集专用提示词"""
        return """
        ## 作品集网站核心要求：
        - 项目卡片网格布局（CSS Grid）
        - 联系表单带验证功能
        - 响应式导航菜单
        - 项目详情模态框
        - 技能展示区域

        必须包含：
        === FILENAME: index.html ===
        [包含项目网格和联系表单的完整HTML]
        === END FILE ===

        === FILENAME: css/portfolio.css ===
        [作品集专用样式：卡片布局、表单样式、响应式设计]
        === END FILE ===

        === FILENAME: js/portfolio.js ===
        [作品集交互：模态框、表单验证、平滑滚动]
        === END FILE ===
        """

    def _get_dashboard_prompt(self):
        """仪表板专用提示词"""
        return """
        ## 销售仪表板核心要求：
        - 多种图表类型（折线图、柱状图、饼图）
        - 实时数据更新机制
        - 交互式数据过滤器
        - KPI指标卡片展示

        必须包含：
        === FILENAME: index.html ===
        [包含图表容器和过滤控件的仪表板HTML]
        === END FILE ===

        === FILENAME: css/dashboard.css ===
        [仪表板专用样式：图表网格、过滤器面板、KPI卡片]
        === END FILE ===

        === FILENAME: js/dashboard.js ===
        [仪表板逻辑：Chart.js集成、实时数据、过滤功能]
        === END FILE ===

        === FILENAME: data/sample-data.js ===
        [示例销售数据用于演示]
        === END FILE ===
        """

    def _get_explorer_prompt(self):
        """数据探索器专用提示词"""
        return """
        ## 数据探索器核心要求：
        - 多图表联动交互
        - 动态数据过滤
        - 图表类型切换
        - 数据详情面板

        必须包含：
        === FILENAME: index.html ===
        [多图表布局和控制面板的探索器HTML]
        === END FILE ===

        === FILENAME: css/explorer.css ===
        [探索器专用样式：多面板布局、交互控件]
        === END FILE ===

        === FILENAME: js/explorer.js ===
        [探索器逻辑：图表联动、动态过滤、数据加载]
        === END FILE ===
        """

    def _get_generic_prompt(self):
        """通用项目提示词"""
        return """
        ## 通用项目要求：
        - 现代Web标准
        - 响应式设计
        - 基础交互功能

        必须包含核心文件：
        === FILENAME: index.html ===
        [标准HTML结构]
        === END FILE ===

        === FILENAME: css/style.css ===
        [基础样式表]
        === END FILE ===

        === FILENAME: js/app.js ===
        [基础JavaScript逻辑]
        === END FILE ===
        """

    def _deep_enhanced_parse(self, implementation, features):
        """深度增强解析 - 优先提取定制化内容"""
        project_files = {}
        
        print(f"🔍 深度解析开始，需求类型: {features['project_type']}")
        
        standard_files = self._parse_standard_format(implementation)
        if standard_files:
            project_files.update(standard_files)
            print(f"✅ 标准格式解析: {len(standard_files)}文件")
        
        deepseek_files = self._parse_deepseek_enhanced(implementation, features)
        if deepseek_files:
            project_files.update(deepseek_files)
            print(f"✅ DeepSeek增强解析: {len(deepseek_files)}文件")
        
        if len(project_files) < 3:
            smart_files = self._parse_intelligent_content(implementation, features)
            if smart_files:
                project_files.update(smart_files)
                print(f"✅ 智能内容提取: {len(smart_files)}文件")
        
        missing_files = self._identify_missing_files(project_files, features)
        if missing_files:
            fallback_files = self._create_targeted_fallback(missing_files, features)
            project_files.update(fallback_files)
            print(f"🔄 需求感知回退: 补充{len(fallback_files)}个文件")
        
        return project_files

    def _parse_deepseek_enhanced(self, implementation, features):
        """DeepSeek响应增强解析"""
        project_files = {}
        
        md_patterns = {
            'html': r'```(?:html)?\s*(<!DOCTYPE html>.*?)```',
            'css': r'```(?:css|scss)?\s*((?:\.[a-zA-Z]|body|#|[a-zA-Z-]+\s*\{).*?)```',
            'js': r'```(?:javascript|js)?\s*((?:function|const|let|var|class|document).*?)```'
        }
        
        for file_type, pattern in md_patterns.items():
            matches = re.findall(pattern, implementation, re.DOTALL | re.IGNORECASE)
            if matches:
                content = matches[0]
                file_path = self._get_file_path_by_type(file_type, features)
                if self._validate_specialized_content(content, file_type, features):
                    project_files[file_path] = content
        
        return project_files

    def _get_file_path_by_type(self, file_type, features):
        """根据文件类型和项目特征生成专用文件路径"""
        project_type = features['project_type']
        
        path_mapping = {
            'portfolio': {
                'html': 'index.html',
                'css': 'css/portfolio.css',
                'js': 'js/portfolio.js'
            },
            'dashboard': {
                'html': 'index.html', 
                'css': 'css/dashboard.css',
                'js': 'js/dashboard.js',
                'data': 'data/sample-data.js'
            },
            'explorer': {
                'html': 'index.html',
                'css': 'css/explorer.css', 
                'js': 'js/explorer.js'
            }
        }
        
        return path_mapping.get(project_type, {}).get(file_type, f'{file_type}/default.{file_type}')

    def _validate_specialized_content(self, content, file_type, features):
        """验证内容是否符合项目类型特征"""
        content_lower = content.lower()
        project_type = features['project_type']
        
        validation_rules = {
            'portfolio': {
                'html': lambda c: 'project' in c and 'contact' in c,
                'css': lambda c: 'grid' in c and 'card' in c,
                'js': lambda c: 'modal' in c or 'form' in c
            },
            'dashboard': {
                'html': lambda c: 'chart' in c and 'filter' in c,
                'css': lambda c: 'chart' in c or 'grid' in c,
                'js': lambda c: 'chart' in c and 'data' in c
            },
            'explorer': {
                'html': lambda c: 'chart' in c and 'control' in c,
                'css': lambda c: 'panel' in c and 'interactive' in c,
                'js': lambda c: 'filter' in c and 'update' in c
            }
        }
        
        rules = validation_rules.get(project_type, {})
        validator = rules.get(file_type, lambda c: True)
        return validator(content_lower)

    def _identify_missing_files(self, project_files, features):
        """识别缺失的核心文件"""
        project_type = features['project_type']
        
        required_files = {
            'portfolio': ['index.html', 'css/portfolio.css', 'js/portfolio.js'],
            'dashboard': ['index.html', 'css/dashboard.css', 'js/dashboard.js', 'data/sample-data.js'],
            'explorer': ['index.html', 'css/explorer.css', 'js/explorer.js']
        }
        
        required = required_files.get(project_type, ['index.html', 'css/style.css', 'js/app.js'])
        existing = set(project_files.keys())
        
        return [file for file in required if file not in existing]

    def _create_targeted_fallback(self, missing_files, features):
        """创建目标明确的回退文件"""
        fallback_files = {}
        project_type = features['project_type']
        
        fallback_templates = {
            'portfolio': self._create_portfolio_fallback,
            'dashboard': self._create_dashboard_fallback,
            'explorer': self._create_explorer_fallback
        }
        
        template_creator = fallback_templates.get(project_type, self._create_generic_fallback)
        full_template = template_creator(features)
        
        for file_path in missing_files:
            if file_path in full_template:
                fallback_files[file_path] = full_template[file_path]
        
        return fallback_files

    def _create_portfolio_fallback(self, features):
        """作品集专用回退模板"""
        return {
            'index.html': '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>个人作品集</title>
    <link rel="stylesheet" href="css/portfolio.css">
</head>
<body>
    <nav class="portfolio-nav">
        <div class="nav-brand">我的作品集</div>
        <ul class="nav-menu">
            <li><a href="#projects">项目</a></li>
            <li><a href="#skills">技能</a></li>
            <li><a href="#contact">联系</a></li>
        </ul>
    </nav>
    
    <main class="portfolio-main">
        <section id="projects" class="projects-grid">
            <h2>项目展示</h2>
            <div class="projects-container">
                <div class="project-card">
                    <h3>项目标题</h3>
                    <p>项目描述...</p>
                    <button class="view-details">查看详情</button>
                </div>
            </div>
        </section>
        
        <section id="contact" class="contact-section">
            <h2>联系我</h2>
            <form class="contact-form">
                <input type="text" placeholder="姓名" required>
                <input type="email" placeholder="邮箱" required>
                <textarea placeholder="消息" required></textarea>
                <button type="submit">发送消息</button>
            </form>
        </section>
    </main>
    
    <script src="js/portfolio.js"></script>
</body>
</html>
            ''',
            'css/portfolio.css': '''
/* 作品集专用样式 */
.projects-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    padding: 2rem;
}

.project-card {
    border: 1px solid #e1e5e9;
    border-radius: 8px;
    padding: 1.5rem;
    transition: transform 0.3s ease;
}

.project-card:hover {
    transform: translateY(-5px);
}

.contact-form {
    max-width: 600px;
    margin: 0 auto;
}

.contact-form input,
.contact-form textarea {
    width: 100%;
    padding: 0.75rem;
    margin-bottom: 1rem;
    border: 1px solid #ddd;
    border-radius: 4px;
}
            ''',
            'js/portfolio.js': '''
// 作品集专用交互
document.addEventListener('DOMContentLoaded', function() {
    // 项目详情模态框
    const detailButtons = document.querySelectorAll('.view-details');
    detailButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            alert('项目详情功能待实现');
        });
    });
    
    // 联系表单验证
    const contactForm = document.querySelector('.contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            alert('消息发送成功！');
            this.reset();
        });
    }
});
            '''
        }

    def _create_dashboard_fallback(self, features):
        """修复：生成纯静态HTML销售仪表板（无需构建）"""
        return {
        'index.html': '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>销售分析仪表板</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="css/dashboard.css">
</head>
<body>
    <div class="dashboard-container">
        <header class="dashboard-header">
            <h1>销售分析仪表板</h1>
            <div class="dashboard-controls">
                <select id="timeRange">
                    <option value="day">今日</option>
                    <option value="week">本周</option>
                    <option value="month">本月</option>
                </select>
                <select id="regionFilter">
                    <option value="all">所有区域</option>
                    <option value="north">北部</option>
                    <option value="south">南部</option>
                </select>
                <button id="refreshBtn">刷新数据</button>
            </div>
        </header>
        
        <div class="kpi-cards">
            <div class="kpi-card">
                <h3>总销售额</h3>
                <div class="kpi-value" id="totalSales">¥0</div>
                <div class="kpi-change" id="salesChange">+0%</div>
            </div>
            <div class="kpi-card">
                <h3>订单数量</h3>
                <div class="kpi-value" id="totalOrders">0</div>
                <div class="kpi-change" id="ordersChange">+0%</div>
            </div>
            <div class="kpi-card">
                <h3>平均订单价</h3>
                <div class="kpi-value" id="avgOrder">¥0</div>
                <div class="kpi-change" id="avgOrderChange">+0%</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <h3>销售趋势</h3>
                <canvas id="salesTrendChart" width="400" height="200"></canvas>
            </div>
            <div class="chart-container">
                <h3>产品分布</h3>
                <canvas id="productDistributionChart" width="400" height="200"></canvas>
            </div>
            <div class="chart-container">
                <h3>区域销售</h3>
                <canvas id="regionSalesChart" width="400" height="200"></canvas>
            </div>
            <div class="chart-container">
                <h3>实时交易</h3>
                <div id="realtimeTransactions">
                    <div class="transaction-list">
                        <!-- 交易记录将通过JS动态添加 -->
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="js/dashboard.js"></script>
    <script src="data/sample-data.js"></script>
</body>
</html>
        ''',
        'css/dashboard.css': '''
/* 销售仪表板专用样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    color: #333;
}

.dashboard-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

.dashboard-header {
    background: rgba(255, 255, 255, 0.95);
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(10px);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
}

.dashboard-header h1 {
    color: #2c3e50;
    margin: 0;
}

.dashboard-controls {
    display: flex;
    gap: 15px;
    align-items: center;
}

.dashboard-controls select,
.dashboard-controls button {
    padding: 10px 15px;
    border: 1px solid #ddd;
    border-radius: 8px;
    background: white;
    cursor: pointer;
}

.dashboard-controls button {
    background: #3498db;
    color: white;
    border: none;
    transition: background 0.3s;
}

.dashboard-controls button:hover {
    background: #2980b9;
}

.kpi-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 20px;
}

.kpi-card {
    background: rgba(255, 255, 255, 0.95);
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(10px);
    transition: transform 0.3s;
}

.kpi-card:hover {
    transform: translateY(-5px);
}

.kpi-value {
    font-size: 2.5em;
    font-weight: bold;
    color: #2c3e50;
    margin: 10px 0;
}

.kpi-change {
    font-size: 1.1em;
    font-weight: bold;
}

.kpi-change.positive {
    color: #27ae60;
}

.kpi-change.negative {
    color: #e74c3c;
}

.charts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
}

.chart-container {
    background: rgba(255, 255, 255, 0.95);
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(10px);
}

.chart-container h3 {
    margin-bottom: 15px;
    color: #2c3e50;
}

#realtimeTransactions {
    max-height: 300px;
    overflow-y: auto;
}

.transaction-item {
    padding: 10px;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
}

.transaction-item:last-child {
    border-bottom: none;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .dashboard-header {
        flex-direction: column;
        gap: 15px;
    }
    
    .dashboard-controls {
        width: 100%;
        justify-content: center;
    }
    
    .charts-grid {
        grid-template-columns: 1fr;
    }
    
    .kpi-cards {
        grid-template-columns: 1fr;
    }
}
        ''',
        'js/dashboard.js': '''
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
        ''',
        'data/sample-data.js': '''
    // 示例销售数据
    window.sampleSalesData = {
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
            '''
    }

    def _create_explorer_fallback(self, features):
        """数据探索器专用回退模板"""
        return {
            'index.html': '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>交互式数据探索器</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="css/explorer.css">
</head>
<body>
    <div class="explorer-container">
        <div class="control-panel">
            <h3>数据控制</h3>
            <div class="filters">
                <input type="text" id="searchFilter" placeholder="搜索...">
                <select id="chartType">
                    <option value="bar">柱状图</option>
                    <option value="line">折线图</option>
                    <option value="pie">饼图</option>
                </select>
            </div>
        </div>
        
        <div class="charts-panel">
            <div class="main-chart">
                <canvas id="primaryChart"></canvas>
            </div>
            <div class="secondary-charts">
                <div class="chart-wrapper">
                    <canvas id="secondaryChart1"></canvas>
                </div>
                <div class="chart-wrapper">
                    <canvas id="secondaryChart2"></canvas>
                </div>
            </div>
        </div>
    </div>
    
    <script src="js/explorer.js"></script>
</body>
</html>
            ''',
            'css/explorer.css': '''
/* 探索器专用样式 */
.explorer-container {
    display: grid;
    grid-template-columns: 300px 1fr;
    gap: 2rem;
    padding: 2rem;
}

.control-panel {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.charts-panel {
    display: grid;
    grid-template-rows: 1fr 1fr;
    gap: 2rem;
}

.main-chart {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.secondary-charts {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
}
            ''',
            'js/explorer.js': '''
// 数据探索器专用逻辑
class DataExplorer {
    constructor() {
        this.initCharts();
        this.setupControls();
    }
    
    initCharts() {
        // 主图表
        this.primaryChart = new Chart(document.getElementById('primaryChart'), {
            type: 'bar',
            data: {
                labels: ['数据集A', '数据集B', '数据集C'],
                datasets: [{
                    label: '数据值',
                    data: [65, 59, 80],
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            }
        });
    }
    
    setupControls() {
        document.getElementById('chartType').addEventListener('change', (e) => {
            this.changeChartType(e.target.value);
        });
    }
    
    changeChartType(type) {
        console.log('切换图表类型:', type);
        // 实际项目中这里会更新图表类型
    }
}

new DataExplorer();
            '''
        }

    def _create_generic_fallback(self, features):
        """通用项目回退模板"""
        return {
            'index.html': '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>通用项目</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header>
        <nav>
            <div class="logo">项目名称</div>
            <ul class="nav-links">
                <li><a href="#home">首页</a></li>
                <li><a href="#about">关于</a></li>
                <li><a href="#contact">联系</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <section id="home">
            <h1>欢迎</h1>
            <p>这是一个通用项目模板。</p>
        </section>
    </main>
    
    <script src="js/app.js"></script>
</body>
</html>
            ''',
            'css/style.css': '''
/* 通用样式 */
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
}

header {
    background: #f8f9fa;
    padding: 1rem;
}

.nav-links {
    display: flex;
    list-style: none;
    gap: 2rem;
}
            ''',
            'js/app.js': '''
// 通用交互逻辑
document.addEventListener('DOMContentLoaded', function() {
    console.log('项目加载完成');
});
            '''
        }

    def _create_iteration_prompt(self, features, existing_files):
        """创建迭代改进的提示词"""
        feedback_text = self.feedback_history[-1] if self.feedback_history else "需要改进现有实现"
        
        return f"""
        根据测试反馈改进现有项目：

        反馈问题: {feedback_text}
        当前文件: {list(existing_files.keys())}
        项目类型: {features['project_type']}

        请针对性地修复以下问题：
        === FILENAME: path/to/file.ext ===
        [修复后的内容]
        === END FILE ===

        专注于解决具体问题，保持项目类型特性。
        """

    def _parse_standard_format(self, implementation):
        """标准格式解析"""
        project_files = {}
        file_pattern = r'=== FILENAME: ([^\n]+?) ===\s*(.*?)\s*=== END FILE ==='
        matches = re.findall(file_pattern, implementation, re.DOTALL)
        
        for file_path, content in matches:
            clean_path = self._clean_file_path(file_path.strip())
            clean_content = self._clean_file_content(content.strip())
            if clean_content:
                project_files[clean_path] = clean_content
        
        return project_files

    def _parse_intelligent_content(self, implementation, features):
        """智能内容提取"""
        project_files = {}
        
        # HTML内容识别
        html_patterns = [
            r'<!DOCTYPE html>.*?</html>',
            r'<html.*?</html>'
        ]
        
        for pattern in html_patterns:
            matches = re.findall(pattern, implementation, re.DOTALL | re.IGNORECASE)
            if matches:
                file_path = self._get_file_path_by_type('html', features)
                project_files[file_path] = matches[0]
                break
        
        # CSS内容识别
        css_pattern = r'([.#]?[a-zA-Z][^{]*\{[^}]+\})'
        css_matches = re.findall(css_pattern, implementation, re.DOTALL)
        if css_matches:
            file_path = self._get_file_path_by_type('css', features)
            project_files[file_path] = '\n'.join(css_matches)
        
        # JS内容识别
        js_pattern = r'(function\s+[^{]*\{[^}]+\}|const\s+[^=]*=|[^=]*function[^{]*\{[^}]+\})'
        js_matches = re.findall(js_pattern, implementation, re.DOTALL)
        if js_matches:
            file_path = self._get_file_path_by_type('js', features)
            project_files[file_path] = '\n'.join(js_matches)
        
        return project_files

    def _clean_file_path(self, file_path):
        """清理文件路径"""
        # 移除Markdown标记和特殊字符
        clean_path = file_path.replace('`', '').replace('*', '').replace('_', '')
        clean_path = re.sub(r'[<>:"|?*]', '', clean_path)
        clean_path = clean_path.replace('\\', '/').strip('/')
        clean_path = re.sub(r'\s+', '_', clean_path)
        return clean_path

    def _clean_file_content(self, content):
        """清理文件内容"""
        if not content:
            return content
        
        # 移除代码块标记
        content = content.strip()
        if content.startswith('```'):
            lines = content.split('\n')
            if len(lines) > 1:
                content = '\n'.join(lines[1:])
            if content.endswith('```'):
                content = content[:-3].strip()
        
        return content

    def history_message_append(self, message, role="user"):
        """添加消息到历史"""
        self.history_message.append({
            "role": role,
            "content": message
        })
        
    def receive_feedback(self, feedback):
        """接收反馈"""
        self.feedback_history.append(feedback)
        return "反馈已接收，准备改进"