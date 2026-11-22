import {useRoute} from "vue-router";
import {useI18n} from "vue-i18n";

import {
    Tab,
    ORDER,
    useHelpers,
} from "../../../components/namespaces/utils/useHelpers";

import KVTable from "../../../components/kv/KVTable.vue";

export function useTabs() {
    const route = useRoute();
    const {t} = useI18n({useScope: "global"});

    const namespace = route.params?.id as string;

    const tabs: Tab[] = [
        ...useHelpers().tabs,
        {
            name: "kv",
            title: t("kv.name"),
            component: KVTable,
            props: {namespace},
        },
    ];

    // Ensure the order of tabs is following the ORDER array
    tabs.sort((a, b) => ORDER.indexOf(a.name) - ORDER.indexOf(b.name));

    return {tabs};
}
