import { createHash, randomUUID } from "node:crypto";
import { promises as fs } from "node:fs";
import { createServer as createHttpServer } from "node:http";
import { dirname, extname, isAbsolute, relative, resolve, sep } from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import "dotenv/config";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { isInitializeRequest } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
const execFileAsync = promisify(execFile);
const host = process.env.MCP_HOST ?? "127.0.0.1";
const port = Number.parseInt(process.env.MCP_PORT ?? "8787", 10);
const configuredRoot = process.env.WORKSPACE_ROOT;
if (!configuredRoot) {
    throw new Error("WORKSPACE_ROOT must be set. Refusing to expose the current directory implicitly.");
}
const workspaceRoot = resolve(configuredRoot);
const authToken = process.env.MCP_AUTH_TOKEN;
const sessions = new Map();
const ignoredDirectories = new Set([".git", "node_modules", "target", "dist", ".mcp-backups"]);
const protectedNames = new Set([
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    ".ssh",
    "id_rsa",
    "id_ed25519",
    "kubeconfig",
    "config",
    "credentials",
    "secrets",
]);
const protectedExtensions = new Set([".pem", ".key", ".p12", ".pfx", ".jks"]);
function textResult(value) {
    return { content: [{ type: "text", text: typeof value === "string" ? value : JSON.stringify(value, null, 2) }] };
}
function errorResult(message) {
    return { isError: true, content: [{ type: "text", text: message }] };
}
function isInsideWorkspace(candidate) {
    const rel = relative(workspaceRoot, candidate);
    return rel === "" || (rel !== ".." && !rel.startsWith(`..${sep}`) && !isAbsolute(rel));
}
function assertSafeRelativePath(input) {
    const candidate = resolve(workspaceRoot, input || ".");
    if (!isInsideWorkspace(candidate)) {
        throw new Error(`Path escapes WORKSPACE_ROOT: ${input}`);
    }
    const parts = relative(workspaceRoot, candidate).split(/[\\/]/).filter(Boolean);
    for (const part of parts) {
        const lower = part.toLowerCase();
        if (protectedNames.has(lower) || protectedExtensions.has(extname(lower))) {
            throw new Error(`Access to protected path is denied: ${input}`);
        }
    }
    return candidate;
}
async function resolveExistingPath(input) {
    const candidate = assertSafeRelativePath(input);
    const real = await fs.realpath(candidate);
    if (!isInsideWorkspace(real)) {
        throw new Error(`Resolved path escapes WORKSPACE_ROOT: ${input}`);
    }
    return real;
}
async function resolveWritablePath(input) {
    const candidate = assertSafeRelativePath(input);
    try {
        return await resolveExistingPath(input);
    }
    catch (error) {
        if (error.code !== "ENOENT") {
            throw error;
        }
    }
    const parent = await fs.realpath(dirname(candidate));
    if (!isInsideWorkspace(parent)) {
        throw new Error(`Parent directory escapes WORKSPACE_ROOT: ${input}`);
    }
    return candidate;
}
function relativePath(path) {
    return relative(workspaceRoot, path) || ".";
}
async function readRequestBody(request) {
    const chunks = [];
    for await (const chunk of request) {
        chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
        if (Buffer.concat(chunks).length > 2 * 1024 * 1024) {
            throw new Error("Request body exceeds 2 MiB limit");
        }
    }
    const raw = Buffer.concat(chunks).toString("utf8");
    return raw ? JSON.parse(raw) : undefined;
}
function headerValue(request, name) {
    const value = request.headers[name.toLowerCase()];
    return Array.isArray(value) ? value[0] : value;
}
function checkAuthorization(request) {
    if (!authToken) {
        return true;
    }
    return headerValue(request, "authorization") === `Bearer ${authToken}`;
}
async function listFiles(inputPath, recursive, maxEntries) {
    const start = await resolveExistingPath(inputPath);
    const startStat = await fs.stat(start);
    if (!startStat.isDirectory()) {
        return [relativePath(start)];
    }
    const output = [];
    const pending = [start];
    while (pending.length > 0 && output.length < maxEntries) {
        const current = pending.shift();
        const entries = await fs.readdir(current, { withFileTypes: true });
        for (const entry of entries) {
            if (ignoredDirectories.has(entry.name)) {
                continue;
            }
            const child = resolve(current, entry.name);
            output.push(relativePath(child));
            if (recursive && entry.isDirectory() && output.length < maxEntries) {
                pending.push(child);
            }
            if (output.length >= maxEntries) {
                break;
            }
        }
    }
    return output;
}
async function readFileContent(inputPath, startLine, endLine) {
    const path = await resolveExistingPath(inputPath);
    const stat = await fs.stat(path);
    if (!stat.isFile()) {
        throw new Error(`Not a file: ${inputPath}`);
    }
    if (stat.size > 2 * 1024 * 1024) {
        throw new Error("Refusing to read files larger than 2 MiB; request a narrower artifact or log slice.");
    }
    const content = await fs.readFile(path, "utf8");
    if (startLine === undefined && endLine === undefined) {
        return content;
    }
    const lines = content.split(/\r?\n/);
    const from = Math.max(1, startLine ?? 1);
    const to = Math.min(lines.length, endLine ?? lines.length);
    return lines.slice(from - 1, to).map((line, index) => `${from + index}: ${line}`).join("\n");
}
async function searchCode(query, searchPath, regex, maxResults) {
    const path = await resolveExistingPath(searchPath);
    const args = ["--no-heading", "--line-number", "--color=never", `--max-count=${Math.min(maxResults, 200)}`];
    if (!regex) {
        args.push("--fixed-strings");
    }
    args.push("--glob=!**/.git/**", "--glob=!**/node_modules/**", "--glob=!**/target/**", "--glob=!**/dist/**", "--", query, path);
    try {
        const result = await execFileAsync(process.platform === "win32" ? "rg.exe" : "rg", args, {
            cwd: workspaceRoot,
            timeout: 10_000,
            maxBuffer: 512 * 1024,
            windowsHide: true,
        });
        return result.stdout || "No matches.";
    }
    catch (error) {
        const execError = error;
        if (execError.code === "1") {
            return "No matches.";
        }
        if (execError.stdout) {
            return `${execError.stdout}\n${execError.stderr ?? ""}`.trim();
        }
        throw new Error(`Code search failed: ${execError.message}`);
    }
}
async function runGuardedCommand(command) {
    const mavenCommand = process.env.MAVEN_COMMAND ?? (process.platform === "win32" ? "mvn.cmd" : "mvn");
    const definitions = {
        git_status: { file: process.platform === "win32" ? "git.exe" : "git", args: ["status", "--short", "--branch"] },
        git_diff: { file: process.platform === "win32" ? "git.exe" : "git", args: ["diff", "--stat"] },
        maven_test: { file: mavenCommand, args: ["-q", "test"] },
        maven_compile: { file: mavenCommand, args: ["-q", "compile"] },
        npm_test: { file: process.platform === "win32" ? "npm.cmd" : "npm", args: ["test"] },
        npm_build: { file: process.platform === "win32" ? "npm.cmd" : "npm", args: ["run", "build"] },
    };
    const definition = definitions[command];
    try {
        const result = await execFileAsync(definition.file, definition.args, {
            cwd: workspaceRoot,
            timeout: 10 * 60 * 1000,
            maxBuffer: 1024 * 1024,
            windowsHide: true,
            env: { ...process.env, CI: "true" },
        });
        return `${result.stdout}${result.stderr ? `\n${result.stderr}` : ""}`.trim() || "Command completed successfully.";
    }
    catch (error) {
        const execError = error;
        const details = `${execError.stdout ?? ""}\n${execError.stderr ?? execError.message ?? "Command failed."}`.trim();
        throw new Error(`Guarded command ${command} failed (exit ${String(execError.code)}):\n${details}`);
    }
}
function createMcpServer() {
    const server = new McpServer({ name: "sre-agent-mcp", version: "0.1.0" });
    server.registerTool("workspace_list_files", {
        title: "List workspace files",
        description: "List files under the configured workspace root. Sensitive paths and generated directories are excluded.",
        inputSchema: {
            path: z.string().default("."),
            recursive: z.boolean().default(false),
            maxEntries: z.number().int().min(1).max(500).default(200),
        },
    }, async ({ path, recursive, maxEntries }) => {
        try {
            return textResult(await listFiles(path, recursive, maxEntries));
        }
        catch (error) {
            return errorResult(error.message);
        }
    });
    server.registerTool("workspace_read_file", {
        title: "Read a workspace file",
        description: "Read a bounded text file or a selected line range from the configured workspace root.",
        inputSchema: {
            path: z.string().min(1),
            startLine: z.number().int().min(1).optional(),
            endLine: z.number().int().min(1).optional(),
        },
    }, async ({ path, startLine, endLine }) => {
        try {
            return textResult(await readFileContent(path, startLine, endLine));
        }
        catch (error) {
            return errorResult(error.message);
        }
    });
    server.registerTool("workspace_search_code", {
        title: "Search workspace code",
        description: "Search source files with ripgrep without invoking a shell. Results are capped to control context size.",
        inputSchema: {
            query: z.string().min(1).max(500),
            path: z.string().default("."),
            regex: z.boolean().default(false),
            maxResults: z.number().int().min(1).max(200).default(50),
        },
    }, async ({ query, path, regex, maxResults }) => {
        try {
            return textResult(await searchCode(query, path, regex, maxResults));
        }
        catch (error) {
            return errorResult(error.message);
        }
    });
    server.registerTool("workspace_write_file", {
        title: "Write a workspace file",
        description: "Create or replace one text file inside the workspace. Replacement requires overwrite=true and can be guarded by expectedSha256.",
        inputSchema: {
            path: z.string().min(1),
            content: z.string().max(2 * 1024 * 1024),
            overwrite: z.boolean().default(false),
            expectedSha256: z.string().regex(/^[a-f0-9]{64}$/i).optional(),
        },
    }, async ({ path, content, overwrite, expectedSha256 }) => {
        try {
            const target = await resolveWritablePath(path);
            let current;
            try {
                current = await fs.readFile(target);
            }
            catch (error) {
                if (error.code !== "ENOENT") {
                    throw error;
                }
            }
            if (current && !overwrite) {
                return errorResult(`Refusing to overwrite existing file ${path}; call again with overwrite=true after review.`);
            }
            if (expectedSha256 && (!current || createHash("sha256").update(current).digest("hex") !== expectedSha256.toLowerCase())) {
                return errorResult(`expectedSha256 does not match the current contents of ${path}; re-read before writing.`);
            }
            await fs.mkdir(dirname(target), { recursive: true });
            const temporary = `${target}.${randomUUID()}.tmp`;
            await fs.writeFile(temporary, content, "utf8");
            await fs.rename(temporary, target);
            return textResult({ path: relativePath(target), bytes: Buffer.byteLength(content, "utf8"), action: current ? "replaced" : "created" });
        }
        catch (error) {
            return errorResult(error.message);
        }
    });
    server.registerTool("workspace_run_project_command", {
        title: "Run a guarded project command",
        description: "Run one predefined, non-shell project command. Arbitrary shell commands are intentionally unavailable in V0.1.",
        inputSchema: {
            command: z.enum(["git_status", "git_diff", "maven_test", "maven_compile", "npm_test", "npm_build"]),
        },
    }, async ({ command }) => {
        try {
            return textResult(await runGuardedCommand(command));
        }
        catch (error) {
            return errorResult(error.message);
        }
    });
    return server;
}
function setCommonHeaders(response) {
    response.setHeader("Access-Control-Allow-Origin", "*");
    response.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization, MCP-Session-Id, MCP-Protocol-Version");
    response.setHeader("Access-Control-Expose-Headers", "MCP-Session-Id");
    response.setHeader("Cache-Control", "no-cache");
}
async function handleMcpRequest(request, response) {
    setCommonHeaders(response);
    if (!checkAuthorization(request)) {
        response.writeHead(401, { "Content-Type": "text/plain; charset=utf-8" });
        response.end("Unauthorized");
        return;
    }
    const sessionId = headerValue(request, "mcp-session-id");
    let body;
    if (request.method === "POST") {
        try {
            body = await readRequestBody(request);
        }
        catch (error) {
            response.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
            response.end(`Invalid JSON body: ${error.message}`);
            return;
        }
    }
    let session = sessionId ? sessions.get(sessionId) : undefined;
    if (!session) {
        if (request.method !== "POST" || !isInitializeRequest(body)) {
            response.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
            response.end("A new MCP session must start with an initialize request.");
            return;
        }
        const server = createMcpServer();
        let transport;
        transport = new StreamableHTTPServerTransport({
            sessionIdGenerator: () => randomUUID(),
            onsessioninitialized: (newSessionId) => {
                sessions.set(newSessionId, { server, transport });
            },
            onsessionclosed: (closedSessionId) => {
                sessions.delete(closedSessionId);
            },
        });
        transport.onerror = (error) => console.error("MCP transport error", error);
        transport.onclose = () => {
            if (transport.sessionId) {
                sessions.delete(transport.sessionId);
            }
        };
        await server.connect(transport);
        session = { server, transport };
    }
    await session.transport.handleRequest(request, response, body);
}
const httpServer = createHttpServer(async (request, response) => {
    try {
        if (request.method === "OPTIONS") {
            setCommonHeaders(response);
            response.writeHead(204);
            response.end();
            return;
        }
        if (request.url === "/healthz" || request.url === "/readyz") {
            response.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
            response.end(JSON.stringify({ status: "ok", workspaceRoot: relativePath(workspaceRoot), sessions: sessions.size }));
            return;
        }
        if (request.url !== "/mcp") {
            response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
            response.end("Not found");
            return;
        }
        await handleMcpRequest(request, response);
    }
    catch (error) {
        console.error("Unhandled MCP request error", error);
        if (!response.headersSent) {
            response.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
        }
        response.end("Internal MCP server error");
    }
});
httpServer.listen(port, host, () => {
    console.log(`sre-agent-mcp listening on http://${host}:${port}/mcp`);
    console.log(`workspace root: ${workspaceRoot}`);
    console.log(`authorization: ${authToken ? "Bearer token required" : "disabled (local-only development mode)"}`);
});
async function shutdown(signal) {
    console.log(`Received ${signal}; closing MCP sessions.`);
    for (const { transport } of sessions.values()) {
        await transport.close().catch(() => undefined);
    }
    httpServer.close(() => process.exit(0));
}
process.on("SIGINT", () => void shutdown("SIGINT"));
process.on("SIGTERM", () => void shutdown("SIGTERM"));
//# sourceMappingURL=server.js.map