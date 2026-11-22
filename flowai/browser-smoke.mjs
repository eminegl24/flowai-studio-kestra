import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {createRequire} from "node:module";

const require = createRequire(new URL("../ui/package.json", import.meta.url));
const {chromium} = require("playwright");
const config = JSON.parse(readFileSync(process.env.FLOWAI_CONFIG ?? new URL("./config.local.json", import.meta.url), "utf8"));
const origin = "http://127.0.0.1:18081";
const browser = await chromium.launch({
    channel: process.env.FLOWAI_BROWSER ?? "chrome",
    headless: true,
});
try {
    const page = await browser.newPage();
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto(origin + "/ui/main/flows");
    await page.getByRole("heading", {name: "FlowAI Studio"}).waitFor();
    await page.getByLabel("Username").fill("admin");
    await page.getByLabel("Password").fill(config.users.admin.password);
    await page.getByRole("button", {name: "Sign in"}).click();
    await page.goto(origin + "/ui/main/flows");
    await page.getByRole("heading", {name: "Flows", exact: true}).waitFor();
    assert.match(await page.title(), /FlowAI Studio/);
    await page.getByRole("link", {name: "Studio tools"}).click();
    await page.getByRole("heading", {name: "SAP Data Services migration"}).waitFor();
    await page.getByLabel("ATL or XML export").setInputFiles({
        name: "sample.xml",
        mimeType: "application/xml",
        buffer: Buffer.from('<export><job name="Daily"/></export>'),
    });
    await page.getByRole("button", {name: "Inventory export"}).click();
    await page.getByText(/sap_migration_draft/).waitFor();
    await page.getByRole("button", {name: "Sign out"}).click();
    await page.waitForURL(origin + "/login");
    assert.deepEqual(errors, []);
    console.log("Browser sign-in, Flows, SAP inventory and sign-out passed.");
} finally {
    await browser.close();
}
