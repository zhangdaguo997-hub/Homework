<template>
  <div class="dashboard-layout" :class="{ 'mobile-sidebar-open': mobileSidebarOpen }">
    <!-- Sidebar Navigation -->
    <Sidebar 
      :is-mobile-open="mobileSidebarOpen"
      @close="mobileSidebarOpen = false"
    />
    
    <!-- Main Content Area -->
    <div class="dashboard-main">
      <!-- Header -->
      <Header @toggle-sidebar="mobileSidebarOpen = !mobileSidebarOpen" />
      
      <!-- Dashboard Content -->
      <main class="dashboard-content">
        <!-- KPI Metrics Row -->
        <div class="metrics-row">
          <div class="metric-card">
            <div class="metric-value">{{ formatNumber(analyticsStore.totalPageViews) }}</div>
            <div class="metric-label">Total Page Views</div>
            <div class="metric-trend" :class="getTrendClass(analyticsStore.pageViewsTrend)">
              <span class="trend-icon">{{ getTrendIcon(analyticsStore.pageViewsTrend) }}</span>
              {{ Math.abs(analyticsStore.pageViewsTrend) }}%
            </div>
          </div>
          
          <div class="metric-card">
            <div class="metric-value">{{ formatNumber(analyticsStore.activeSessions) }}</div>
            <div class="metric-label">Active Sessions</div>
            <div class="metric-trend" :class="getTrendClass(analyticsStore.sessionsTrend)">
              <span class="trend-icon">{{ getTrendIcon(analyticsStore.sessionsTrend) }}</span>
              {{ Math.abs(analyticsStore.sessionsTrend) }}%
            </div>
          </div>
          
          <div class="metric-card">
            <div class="metric-value">{{ analyticsStore.bounceRate }}%</div>
            <div class="metric-label">Bounce Rate</div>
            <div class="metric-trend" :class="getTrendClass(-analyticsStore.bounceRateTrend)">
              <span class="trend-icon">{{ getTrendIcon(-analyticsStore.bounceRateTrend) }}</span>
              {{ Math.abs(analyticsStore.bounceRateTrend) }}%
            </div>
          </div>
          
          <div class="metric-card">
            <div class="metric-value">{{ formatNumber(analyticsStore.uniqueVisitors) }}</div>
            <div class="metric-label">Unique Visitors</div>
            <div class="metric-trend" :class="getTrendClass(analyticsStore.visitorsTrend)">
              <span class="trend-icon">{{ getTrendIcon(analyticsStore.visitorsTrend) }}</span>
              {{ Math.abs(analyticsStore.visitorsTrend) }}%
            </div>
          </div>
        </div>
        
        <!-- Charts Grid -->
        <div class="charts-grid">
          <!-- Page Views Chart -->
          <WidgetContainer title="Page Views Over Time" :widget-id="'page-views'">
            <PageViewsChart />
          </WidgetContainer>
          
          <!-- User Sessions Chart -->
          <WidgetContainer title="User Sessions" :widget-id="'user-sessions'">
            <UserSessionsChart />
          </WidgetContainer>
          
          <!-- Bounce Rate Gauge -->
          <WidgetContainer title="Bounce Rate" :widget-id="'bounce-rate'">
            <BounceRateGauge />
          </WidgetContainer>
          
          <!-- Geographic Distribution -->
          <WidgetContainer title="Geographic Distribution" :widget-id="'geo-map'" :width="2">
            <GeoMap />
          </WidgetContainer>
          
          <!-- Real-time Notifications -->
          <WidgetContainer title="Real-time Notifications" :widget-id="'notifications'">
            <NotificationWidget />
          </WidgetContainer>
        </div>
      </main>
    </div>
    
    <!-- Mobile Overlay -->
    <div 
      v-if="mobileSidebarOpen" 
      class="mobile-overlay"
      @click="mobileSidebarOpen = false"
    ></div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { useAnalyticsStore } from '../stores/analytics'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
import WidgetContainer from './widgets/WidgetContainer.vue'
import PageViewsChart from './charts/PageViewsChart.vue'
import UserSessionsChart from './charts/UserSessionsChart.vue'
import BounceRateGauge from './charts/BounceRateGauge.vue'
import GeoMap from './charts/GeoMap.vue'
import NotificationWidget from './widgets/NotificationWidget.vue'

export default {
  name: 'DashboardLayout',
  components: {
    Sidebar,
    Header,
    WidgetContainer,
    PageViewsChart,
    UserSessionsChart,
    BounceRateGauge,
    GeoMap,
    NotificationWidget
  },
  setup() {
    const analyticsStore = useAnalyticsStore()
    const mobileSidebarOpen = ref(false)
    
    const formatNumber = (num) => {
      return new Intl.NumberFormat().format(num)
    }
    
    const getTrendClass = (trend) => {
      return trend >= 0 ? 'positive' : 'negative'
    }
    
    const getTrendIcon = (trend) => {
      return trend >= 0 ? '↗' : '↘'
    }
    
    onMounted(() => {
      analyticsStore.initializeData()
    })
    
    onUnmounted(() => {
      analyticsStore.cleanup()
    })
    
    return {
      analyticsStore,
      mobileSidebarOpen,
      formatNumber,
      getTrendClass,
      getTrendIcon
    }
  }
}
</script>

<style lang="scss" scoped>
.dashboard-layout {
  display: grid;
  grid-template-columns: minmax(250px, 300px) 1fr;
  grid-template-rows: auto 1fr;
  grid-template-areas: 
    "sidebar header"
    "sidebar main";
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  
  &.mobile-sidebar-open {
    .sidebar {
      transform: translateX(0);
    }
    
    .mobile-overlay {
      opacity: 1;
      pointer-events: auto;
    }
  }
}

.dashboard-main {
  grid-area: main;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.dashboard-content {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

.metrics-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.metric-card {
  background: var(--gradient-primary);
  color: white;
  border-radius: var(--border-radius-lg);
  padding: 1.5rem;
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow-glass);
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
    pointer-events: none;
  }
}

.metric-value {
  font-size: 2.25rem;
  font-weight: 700;
  margin: 0.5rem 0;
}

.metric-label {
  font-size: 0.875rem;
  opacity: 0.9;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.metric-trend {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.2);
  margin-top: 0.5rem;
  
  &.positive {
    color: #4caf50;
  }
  
  &.negative {
    color: #f44336;
  }
}

.trend-icon {
  font-size: 0.75rem;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
  align-content: start;
}

.mobile-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 998;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
}

// Responsive Design
@media (max-width: 1024px) {
  .dashboard-layout {
    grid-template-columns: 1fr;
    grid-template-areas: 
      "header"
      "main";
  }
  
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: 300px;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    z-index: 999;
  }
  
  .dashboard-content {
    padding: 1rem;
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .metrics-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .metrics-row {
    grid-template-columns: 1fr;
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>