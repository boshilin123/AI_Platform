<script setup lang="ts">
defineProps<{ message: string; requestId?: string }>();
</script>

<template>
  <div class="error-notice" role="alert">
    <strong>请求未完成</strong>
    <span>{{ message }}</span>
    <small v-if="requestId">请求编号：{{ requestId }}</small>
  </div>
</template>
