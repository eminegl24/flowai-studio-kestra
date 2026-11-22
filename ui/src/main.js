// Modified for FlowAI Studio. See FLOWAI-NOTICE.txt.
import {createApp} from "vue"

import App from "./App.vue"
import initApp from "./utils/init"
import configureAxios from "./utils/axios"
import routes from "./routes/routes";
import en from "./translations/en.json";
import {setupTenantRouter} from "./composables/useTenant";
import * as BasicAuth from "./utils/basicAuth";
import {useMiscStore} from "override/stores/misc";


const unavailablePages = new Set([
    "apps/list", "tests/list", "assets/list", "secrets/list",
    "admin/auditlogs/list", "admin/iam", "admin/instance",
]);
const unavailableTabs = {
    "flows/update": ["auditlogs"],
    "executions/update": ["auditlogs", "assets"],
    "namespaces/update": ["edit", "secrets", "assets", "variables", "plugin-defaults", "history", "audit-logs"],
};

const app = createApp(App)

const handleAuthError = (error, to) => {
    if (error.message?.includes("401")) {
        BasicAuth.logout()
        const fromPath = to.fullPath !== "/ui/login" ? to.fullPath : undefined
        return {name: "login", query: fromPath ? {from: fromPath} : {}}
    }
    return {name: "setup"}
}

initApp(app, routes, null, en).then(({router, piniaStore}) => {
    router.beforeEach(async (to, from, next) => {
        if(to.path === from.path && to.query === from.query) {
            return next(); // Prevent navigation if the path and query are the same
        }

        try {
            const miscStore = useMiscStore();
            const configs = await miscStore.loadConfigs();

            if (window.FLOWAI_MANAGED_AUTH) {
                if (to.name === "login" || to.name === "setup") {
                    return next({name: "welcome"});
                }
                if (unavailablePages.has(to.name)) {
                    return next({name: "flows/list", params: {tenant: to.params.tenant}, replace: true});
                }
                if (["blueprints", "blueprints/view"].includes(to.name)
                    && (to.params.kind === "app" || to.params.tab === "custom")) {
                    return next({name: "blueprints", params: {tenant: to.params.tenant, kind: "flow", tab: "community"}, replace: true});
                }
                if (unavailableTabs[to.name]?.includes(to.params.tab)) {
                    return next({name: to.name, params: {...to.params, tab: "overview"}, replace: true});
                }
                return next();
            }

            if(!configs.isBasicAuthInitialized) {
                // Since, Configs takes preference
                // we need to check if any regex validation error in BE.
                const validationErrors = await miscStore.loadBasicAuthValidationErrors()

                if (validationErrors?.length > 0) {
                    // Creds exist in config but failed validation
                    // Route to login to show errors
                    if (to.name === "login") {
                        return next();
                    }

                    return next({name: "login"})
                } else {
                    // No creds in config - redirect to set it up
                    if (to.name === "setup") {
                        return next();
                    }

                    return next({name: "setup"})
                }
            }

            if (to.meta?.anonymous === true) {
                if (to.name === "setup") {
                    return next({name: "login"});
                }
                return next();
            }

            const hasCredentials = BasicAuth.isLoggedIn()

            if (!hasCredentials) {
                const fromPath = to.fullPath !== "/ui/login" ? to.fullPath : undefined
                return next({name: "login", query: fromPath ? {from: fromPath} : {}})
            }

            // Check if basic auth setup is still in progress
            const isSetupInProgress = localStorage.getItem("basicAuthSetupInProgress")
            if (isSetupInProgress === "true") {
                return next({name: "setup"})
            }

            return next();
        } catch (error) {
            console.error("Error during authentication check:", error);
            if (window.FLOWAI_MANAGED_AUTH) return next(false);
            return next(handleAuthError(error, to))
        }
    });

    // Setup tenant router
    setupTenantRouter(router, app);

    // axios
    configureAxios((instance) => {
        piniaStore.use(({store: piniaStoreLocal}) => {
            piniaStoreLocal.$http = instance;
        });
    }, null, router, true);

    // mount
    router.isReady().then(() => app.mount("#app"))
});
