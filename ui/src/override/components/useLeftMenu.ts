import {computed, onMounted, ref} from "vue";

import {useRoute, useRouter} from "vue-router";
import type {
    RouteLocationRaw,
    RouteLocationNamedRaw,
    RouteRecordNameGeneric,
} from "vue-router";

import {useI18n} from "vue-i18n";

import {useMiscStore} from "override/stores/misc";

import {getDashboard} from "../../components/dashboard/composables/useDashboards";
import {shouldShowWelcome} from "../../utils/welcomeGuard";

// Main icons
import AiMenuIcon from "../../components/ai/AiMenuIcon.vue";
import ChartLineVariant from "vue-material-design-icons/ChartLineVariant.vue";
import FileTreeOutline from "vue-material-design-icons/FileTreeOutline.vue";
import ContentCopy from "vue-material-design-icons/ContentCopy.vue";
import PlayOutline from "vue-material-design-icons/PlayOutline.vue";
import FileDocumentOutline from "vue-material-design-icons/FileDocumentOutline.vue";
import FolderOpenOutline from "vue-material-design-icons/FolderOpenOutline.vue";
import PuzzleOutline from "vue-material-design-icons/PuzzleOutline.vue";
import ShapePlusOutline from "vue-material-design-icons/ShapePlusOutline.vue";
import OfficeBuildingOutline from "vue-material-design-icons/OfficeBuildingOutline.vue";

// Tenant Administration icons
import Monitor from "vue-material-design-icons/Monitor.vue";
import DatabaseOutline from "vue-material-design-icons/DatabaseOutline.vue";
import LightningBolt from "vue-material-design-icons/LightningBolt.vue";
import Battery40 from "vue-material-design-icons/Battery40.vue";

export type MenuItem = {
    id?: string; // Generated at the end of menu computation
    title: string;
    routes?: RouteRecordNameGeneric[];
    href?: RouteLocationRaw;
    icon?: {
        element?: any;
        class?: any;
    };
    child?: MenuItem[];
    attributes?: {
        locked?: boolean;
    };
    hidden?: boolean;
    disabled?: boolean;
    "class"?: string;
};

export function useLeftMenu() {
    const $route = useRoute();
    const $router = useRouter();

    const {t} = useI18n({useScope: "global"});

    const configs = useMiscStore().configs;
    const showWelcomeLink = ref(false);

    const loadWelcomeLink = async () => {
        try {
            showWelcomeLink.value = await shouldShowWelcome();
        } catch {
            showWelcomeLink.value = false;
        }
    };

    onMounted(() => {
        void loadWelcomeLink();
    });

    /**
     * Returns the names of all registered routes whose name starts with the given prefix.
     *
     * @param route - The route name prefix to match against.
     * @returns An array of route names starting with the provided prefix.
     */
    function routeStartWith(route: string) {
        return $router
            ?.getRoutes()
            .filter(
                (r) => typeof r.name === "string" && r.name.startsWith(route),
            )
            .map((r) => r.name);
    }

    /**
     * Recursively flattens a nested menu structure into a flat array.
     *
     * Each item is included in the result. If an item has `child` items,
     * they are recursively flattened and included immediately after the parent item.
     *
     * @param {MenuItem[]} items - The array of menu items to flatten. Each item may have a `child` property containing nested MenuItems.
     * @returns {MenuItem[]} A flat array of all menu items, preserving the parent-child order.
     */
    const flatten = (items: MenuItem[]): MenuItem[] => {
        return items.flatMap((item) =>
            item.child ? [item, ...flatten(item.child)] : [item],
        );
    };

    const menu = computed<MenuItem[]>(() => {
        const generated = [
            {
                title: t("ai.flow.title"),
                routes: routeStartWith("welcome"),
                href: {
                    name: "welcome",
                },
                icon: {
                    element: AiMenuIcon,
                },
            },
            {
                title: t("dashboards.labels.plural"),
                routes: routeStartWith("home"),
                href: {
                    name: "home",
                    params: {
                        dashboard: getDashboard({
                            ...$route,
                            name: "home"
                        }, "id"),
                    },
                },
                icon: {
                    element: ChartLineVariant,
                },
            },
            {
                title: t("flows"),
                routes: routeStartWith("flows"),
                href: {
                    name: "flows/list",
                },
                icon: {
                    element: FileTreeOutline,
                },
            },
            {
                title: t("executions"),
                routes: routeStartWith("executions"),
                href: {
                    name: "executions/list",
                },
                icon: {
                    element: PlayOutline,
                },
            },
            {
                title: t("logs"),
                routes: routeStartWith("logs"),
                href: {
                    name: "logs/list",
                },
                icon: {
                    element: FileDocumentOutline,
                },
            },
            {
                title: t("namespaces"),
                routes: routeStartWith("namespaces"),
                href: {
                    name: "namespaces/list",
                },
                icon: {
                    element: FolderOpenOutline,
                },
            },
            {
                title: t("templates"),
                routes: routeStartWith("templates"),
                href: {
                    name: "templates/list",
                },
                icon: {
                    element: ContentCopy,
                },
                hidden: !configs?.isTemplateEnabled,
            },
            {
                title: t("plugins.names"),
                routes: routeStartWith("plugins"),
                href: {
                    name: "plugins/list",
                },
                icon: {
                    element: PuzzleOutline,
                },
            },
            {
                title: t("blueprints.title"),
                icon: {
                    element: ShapePlusOutline,
                },
                child: [
                    {
                        title: t("blueprints.flows"),
                        routes: routeStartWith("blueprints/flow/community"),
                        href: {
                            name: "blueprints",
                            params: {
                                kind: "flow",
                                tab: "community",
                            },
                        },
                        icon: {
                            element: FileTreeOutline,
                        },
                    },
                    {
                        title: t("blueprints.dashboards"),
                        routes: routeStartWith("blueprints/dashboard"),
                        href: {
                            name: "blueprints",
                            params: {
                                kind: "dashboard",
                                tab: "community",
                            },
                        },
                        icon: {
                            element: ChartLineVariant,
                        },
                    },
                ],
            },
            {
                title: t("tenant.name"),
                routes: [
                    "admin/stats",
                    "kv",
                    "admin/triggers",
                    "admin/concurrency-limits",
                ]
                    .map(routeStartWith)
                    .find((routes) => routes.length > 0),
                icon: {
                    element: OfficeBuildingOutline,
                },
                child: [
                    {
                        title: t("system overview"),
                        routes: routeStartWith("admin/stats"),
                        href: {
                            name: "admin/stats",
                        },
                        icon: {
                            element: Monitor,
                        },
                    },
                    {
                        title: t("kv.name"),
                        routes: routeStartWith("kv"),
                        href: {
                            name: "kv/list",
                        },
                        icon: {
                            element: DatabaseOutline,
                        },
                    },
                    {
                        title: t("triggers"),
                        routes: routeStartWith("admin/triggers"),
                        href: {
                            name: "admin/triggers",
                        },
                        icon: {
                            element: LightningBolt,
                        },
                    },
                    {
                        title: t("concurrency limits"),
                        routes: routeStartWith("admin/concurrency-limits"),
                        href: {
                            name: "admin/concurrency-limits",
                        },
                        icon: {
                            element: Battery40,
                        },
                        hidden: !configs?.isConcurrencyViewEnabled,
                    },
                ],
            },
        ];

        flatten(generated).forEach((item: MenuItem) => {
            item.id = item.title.toLowerCase().replaceAll(" ", "-");

            if (item.icon?.element) item.icon.class = "menu-icon";

            if (item.href && typeof item.href !== "string") {
                const rObject = item.href as RouteLocationNamedRaw;

                // Merge query if route matches
                if (rObject.name === $route.name) {
                    rObject.query = {
                        ...$route.query,
                        ...rObject.query,
                    };
                }

                // Convert object href to string path
                item.href = $router.resolve(rObject).fullPath;
            }
        });

        return generated;
    });

    return {menu};
}
