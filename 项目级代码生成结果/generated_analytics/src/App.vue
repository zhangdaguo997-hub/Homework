<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App',
  mounted() {
    // Initialize real-time data connections
    this.$nextTick(() => {
      this.initializeRealTimeServices()
    })
  },
  methods: {
    initializeRealTimeServices() {
      // WebSocket connection will be established by the store
      console.log('Initializing real-time analytics services...')
    }
  }
}
</script>

<style lang="scss">
#app {
  min-height: 100vh;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

// Global scrollbar styling
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  
  &:hover {
    background: rgba(255, 255, 255, 0.5);
  }
}
</style>