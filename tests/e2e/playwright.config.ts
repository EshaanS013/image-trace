import { defineConfig } from "@playwright/test";

const windows = process.platform === "win32";
const python = windows ? ".venv\\Scripts\\python.exe" : ".venv/bin/python";

export default defineConfig({
  testDir: ".",
  timeout: 90_000,
  retries: 0,
  use: { baseURL: "http://127.0.0.1:5173", trace: "retain-on-failure", screenshot: "only-on-failure", channel: process.env.CI ? undefined : "chrome" },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
  webServer: [
    { command: `${python} -m alembic upgrade head && ${python} -m uvicorn image_trace.main:app --host 127.0.0.1 --port 8000`, cwd: "../../apps/backend", url: "http://127.0.0.1:8000/api/v1/health", reuseExistingServer: true, timeout: 60_000 },
    { command: "npm run dev", cwd: "../../apps/frontend", url: "http://127.0.0.1:5173", reuseExistingServer: true, timeout: 60_000 },
  ],
});
