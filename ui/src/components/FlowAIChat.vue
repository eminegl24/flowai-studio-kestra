<template>
    <aside v-if="canChat" class="flowai-chat">
        <section v-if="openedOnce" v-show="open" id="flowai-chat-panel" aria-label="Copilot Sohbet">
            <AiCopilot chat flow="" conversation-id="" @close="closeChat" @minimize="minimizeChat" />
        </section>
        <AITriggerButton
            show
            :opened="open"
            :icon-only="minimized"
            :label="minimized ? 'Sohbeti aç' : 'Copilot Sohbet'"
            @click="openChat"
        />
    </aside>
</template>

<script setup lang="ts">
    import {onMounted, ref} from "vue";
    import AiCopilot from "./ai/AiCopilot.vue";
    import AITriggerButton from "./ai/AITriggerButton.vue";

    const canChat = ref(false);
    const open = ref(false);
    const openedOnce = ref(false);
    const minimized = ref(false);

    onMounted(async () => {
        try {
            const response = await fetch("/studio/me");
            canChat.value = response.ok && (await response.json()).role === "admin";
        } catch {
            canChat.value = false;
        }
    });

    function closeChat() {
        minimized.value = false;
        open.value = false;
    }

    function minimizeChat() {
        minimized.value = true;
        open.value = false;
    }

    function openChat() {
        openedOnce.value = true;
        open.value = true;
    }
</script>

<style scoped>
    .flowai-chat {
        position: fixed;
        right: 1rem;
        bottom: 1rem;
        z-index: 1050;
        display: grid;
        justify-items: end;
    }

    section { width: min(31rem, calc(100vw - 2rem)); }
</style>
