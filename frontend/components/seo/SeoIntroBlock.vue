<template>
  <section class="space-y-4 text-slate-700">
    <p v-for="(paragraph, index) in paragraphs" :key="index" class="leading-7">
      {{ paragraph }}
    </p>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  paragraphs: string[]
}>()
</script>
