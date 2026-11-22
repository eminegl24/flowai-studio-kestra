<!-- Modified for FlowAI Studio. See FLOWAI-NOTICE.txt. -->
<template>
    <SidebarMenu
        ref="sideBarRef"
        id="side-menu"
        :menu
        @update:collapsed="onToggleCollapse"
        width="280px"
        :collapsed="collapsed"
        linkComponentName="LeftMenuLink"
        hideToggle
        showOneChild
    >
        <template #header>
            <SidebarToggleButton
                @toggle="collapsed = onToggleCollapse(!collapsed)"
            />
            <div class="logo">
                <component :is="props.showLink ? 'router-link' : 'div'" :to="{name: 'welcome'}">
                    <span class="img" />
                </component>
            </div>
            <Environment />
            <a v-if="!collapsed" class="studio-link" href="/studio">Studio tools</a>
        </template>

        <template #footer>
            <slot name="footer" />
        </template>
    </SidebarMenu>
</template>

<script setup lang="ts">
    import {onUpdated, computed, h, watch} from "vue";
    import {useI18n} from "vue-i18n";
    import {useRoute} from "vue-router";
    import {useMediaQuery} from "@vueuse/core";
    import {SidebarMenu} from "vue-sidebar-menu";
    import StarOutline from "vue-material-design-icons/StarOutline.vue";

    import Environment from "./Environment.vue";
    import BookmarkLinkList from "./BookmarkLinkList.vue";
    import {useBookmarksStore} from "../../stores/bookmarks";
    import type {MenuItem} from "override/components/useLeftMenu";
    import {useLayoutStore} from "../../stores/layout";
    import SidebarToggleButton from "./SidebarToggleButton.vue";


    const props = withDefaults(defineProps<{
        menu: MenuItem[],
        showLink?: boolean
    }>(), {
        showLink: true
    })

    const $emit = defineEmits(["menu-collapse"])

    const $route = useRoute()
    const {t} = useI18n({useScope: "global"});

    const layoutStore = useLayoutStore();

    function onToggleCollapse(folded: boolean) {
        collapsed.value = folded;
        layoutStore.setSideMenuCollapsed(folded);
        $emit("menu-collapse", folded);

        return folded;
    }

    function disabledCurrentRoute(items: MenuItem[]) {
        return items
            .map(r => {
                if (typeof r.href === "object" && r.href?.path === $route.path) {
                    r.disabled = true;
                }

                // route hack is still needed for blueprints
                if (typeof r.href === "string" && r.href !== "/" && ($route.path.startsWith(r.href) || r.routes?.includes($route.name))) {
                    r.class = "vsm--link_active";
                }

                if ((!r.href || typeof r.href === "string") && r.child && r.child.some(c => typeof c.href === "string" && $route.path.startsWith(c.href) || c.routes?.includes($route.name))) {
                    r.class = "vsm--link_active";
                    r.child = disabledCurrentRoute(r.child);
                }

                return r;
            })
    }


    function expandParentIfNeeded() {
        document.querySelectorAll(".vsm--link.vsm--link_level-1.vsm--link_active:not(.vsm--link_open)[aria-haspopup]").forEach(e => {
            (e as HTMLElement).click()
        });
    }

    onUpdated(() => {
        // Required here because in mounted() the menu is not yet rendered
        expandParentIfNeeded();
    })

    const bookmarksStore = useBookmarksStore();

    const menu = computed(() => {
        return [
            ...(bookmarksStore.pages?.length ? [{
                title: t("bookmark"),
                icon: {
                    element: StarOutline,
                    class: "menu-icon",
                },
                child: [{
                    // here we use only one component for all bookmarks
                    // so when one edits the bookmark, it will be updated without closing the section
                    component: () => h(BookmarkLinkList, {pages: bookmarksStore.pages}),
                }]
            }] : []),
            ...(props.menu ? disabledCurrentRoute(props.menu) : [])
        ];
    });

    const collapsed = computed({
        get: () => layoutStore.sideMenuCollapsed,
        set: (v: boolean) => layoutStore.setSideMenuCollapsed(v),
    })

    const isSmallScreen = useMediaQuery("(max-width: 768px)")

    watch(() => $route.name, (newRoute, oldRoute) => {
        if (newRoute !== oldRoute && isSmallScreen.value && !collapsed.value) {
            onToggleCollapse(true)
        }
    })
</script>

<style scoped lang="scss">
.collapseButton {
    position: absolute;
    top: .75rem;
    right: .5rem;
    z-index: 1;

    #side-menu & {
        border: none;
    }
}

#side-menu {
    position: static;
    z-index: 1039;
    border-right: 1px solid var(--ks-border-primary);
    --ks-background-left-menu: #edf8f6;
    background-color: var(--ks-background-left-menu);

    html.dark & {
        --ks-background-left-menu: #102422;
    }

    .studio-link {
        color: light-dark(#0f766e, #5eead4);
        display: block;
        padding: .5rem 1rem;
    }

    .logo {
        overflow: hidden;
        padding: 35px 0;
        height: 112px;
        position: relative;

        > * {
            transition: 0.2s all;
            position: absolute;
            left: 37px;
            display: block;
            height: 55px;
            width: 100%;
            overflow: hidden;

            span.img {
                height: 100%;
                background: url(../../assets/flowai-logo.svg) 0 0 no-repeat;
                background-size: 179px 55px;
                display: block;
                transition: 0.2s all;

                html.dark & {
                    background-image: url(../../assets/flowai-logo-white.svg);
                }
            }
        }
    }
}
</style>
