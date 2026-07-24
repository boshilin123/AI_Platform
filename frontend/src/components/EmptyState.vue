<script setup lang="ts">
defineProps<{ title: string; description: string }>();
</script>

<template>
  <div class="empty-state">
    <div class="empty-icon">·</div>
    <strong>{{ title }}</strong>
    <p>{{ description }}</p>
  </div>
</template>
