const flowField = /^(?:id|namespace|description|tasks|triggers|inputs|outputs|variables|labels|errors|finally|afterExecution|retry|concurrency|pluginDefaults|disabled|deleted|sla|kestraVersion):/;
const yamlStart = /^id:[ \t]*\S/;
const namespace = /^namespace:[ \t]*\S/;
const tasks = /^tasks:[ \t]*(?:\[|$)/;
const fenceStart = /^ {0,3}(`{3,}|~{3,})/;

export function chatMarkdown(text: string): string {
    const lines = text.split(/\r?\n/);
    let fence: string | undefined;
    for (let index = 0; index < lines.length; index++) {
        const line = lines[index];
        const marker = line.match(fenceStart)?.[1];
        if (fence) {
            if (marker?.[0] === fence[0] && marker.length >= fence.length
                && line.trim() === marker) fence = undefined;
            continue;
        }
        if (marker) {
            fence = marker;
            continue;
        }
        if (!yamlStart.test(line)) continue;

        let end = index + 1;
        while (end < lines.length && (flowField.test(lines[end]) || /^[ \t]/.test(lines[end])
            || lines[end] === "" || lines[end].startsWith("# "))) end++;
        const block = lines.slice(index, end);
        if (!block.some(line => namespace.test(line)) || !block.some(line => tasks.test(line))) continue;

        while (lines[end - 1] === "") end--;
        const code = lines.slice(index, end).join("\n");
        const delimiter = "~".repeat(Math.max(3, ...Array.from(
            code.matchAll(/~{3,}/g), match => match[0].length + 1,
        )));
        lines.splice(index, end - index, "", delimiter + "yaml", code, delimiter, "");
        index += 4;
    }
    return lines.join("\n");
}
