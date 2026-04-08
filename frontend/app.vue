<template>
  <NuxtPage />
</template>

<script setup lang="ts">
onMounted(() => {
  if (!('serviceWorker' in navigator)) {
    return
  }

  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch((error) => {
      console.error('Service worker registration failed', error)
    })
  }, { once: true })
})
</script>
