import logMessage from "./log-message.yaml?raw";
import readPublicApi from "./read-public-api.yaml?raw";
import dailyLog from "./daily-log.yaml?raw";

export const flowExamples = {
    logMessage: {
        flow: logMessage,
        labelKey: "welcome_copilot.flows.logMessage.label",
        promptKey: "welcome_copilot.flows.logMessage.prompt",
    },
    readPublicApi: {
        flow: readPublicApi,
        labelKey: "welcome_copilot.flows.readPublicApi.label",
        promptKey: "welcome_copilot.flows.readPublicApi.prompt",
    },
    dailyLog: {
        flow: dailyLog,
        labelKey: "welcome_copilot.flows.dailyLog.label",
        promptKey: "welcome_copilot.flows.dailyLog.prompt",
    },
} as const;

export const labels = ["logMessage", "readPublicApi", "dailyLog"] as const;
