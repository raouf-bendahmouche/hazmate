/**
 * Electron Main Process
 * Starts Python FastAPI backend, then opens the BrowserWindow.
 */

const { app, BrowserWindow, ipcMain, globalShortcut } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const http = require("http");
const fs = require("fs");

app.disableHardwareAcceleration();
app.commandLine.appendSwitch("disable-gpu");

const API_PORT = 5757;
const API_BASE = `http://127.0.0.1:${API_PORT}`;

let mainWindow = null;
let pyProcess = null;

// ─────────────────────────────────────────────
// 🐍 Python Resolver (OS-Aware & Fallback)
// ─────────────────────────────────────────────

function findPython() {
  // This resolver intentionally prioritizes the project-local virtual environment.
  // Why: backend dependency versions are pinned and tested against that environment.
  // If we skip this and rely on a random system interpreter, startup can fail due to
  // missing packages or incompatible versions, and those failures are hard for users
  // to diagnose because the UI may open before backend readiness is guaranteed.
  const isWindows = process.platform === "win32";
  const venvPython = isWindows
    ? path.join(__dirname, "..", ".venv", "Scripts", "python.exe")
    : path.join(__dirname, "..", ".venv", "bin", "python3");

  const parentVenvPython = isWindows
    ? path.join(__dirname, "..", "..", ".venv", "Scripts", "python.exe")
    : path.join(__dirname, "..", "..", ".venv", "bin", "python3");

  if (fs.existsSync(venvPython)) {
    console.log("✅ Using venv python:", venvPython);
    return venvPython;
  }

  if (fs.existsSync(parentVenvPython)) {
    console.log("✅ Using parent venv python:", parentVenvPython);
    return parentVenvPython;
  }

  console.warn("⚠️ Virtual environment not found at:", venvPython, "or", parentVenvPython);
  console.warn("⚠️ Falling back to system Python...");

  // Fallback to system Python if venv is missing
  return isWindows ? "python" : "python3";
}

// ─────────────────────────────────────────────
// 🚀 Start FastAPI Backend
// ─────────────────────────────────────────────

function startPythonServer() {
  // The backend is spawned as a child process so Electron can supervise lifecycle.
  // Why this approach: a local desktop app should feel single-process to users even
  // though UI and API are separate runtimes. If this supervision is removed, users
  // would need manual backend startup and the app would become operationally fragile.
  const python = findPython();
  const serverScript = path.join(__dirname, "..", "backend", "api", "api_endpoint_manager.py");

  console.log(`🚀 Starting FastAPI backend with: ${python} ${serverScript}`);

  pyProcess = spawn(python, [serverScript], {
    cwd: path.join(__dirname, ".."),
    env: {
      ...process.env,
      PYTHONUNBUFFERED: "1",
    },
    stdio: ["ignore", "pipe", "pipe"],
  });

  pyProcess.on("error", (err) => {
    console.error("❌ Failed to start Python process. Ensure Python is installed and accessible:", err.message);
    app.quit();
  });

  pyProcess.stdout.on("data", (data) => {
    console.log("[PY]", data.toString().trim());
  });

  pyProcess.stderr.on("data", (data) => {
    console.error("[PY ERR]", data.toString().trim());
  });

  pyProcess.on("exit", (code) => {
    console.log("[PY] exited with code", code);
  });
}

// ─────────────────────────────────────────────
// 🔍 Check if backend is running
// ─────────────────────────────────────────────

function isServerReachable(timeout = 800) {
  // Quick probe is used to avoid launching duplicate backend processes.
  // This is critical because running two API instances against one SQLite file can
  // increase lock contention and produce confusing behavior for operators.
  return new Promise((resolve) => {
    const req = http.get(`${API_BASE}/api/ping`, (res) => {
      resolve(res.statusCode === 200);
    });

    req.setTimeout(timeout, () => {
      req.destroy();
      resolve(false);
    });

    req.on("error", () => resolve(false));
  });
}

// ─────────────────────────────────────────────
// ⏳ Wait for FastAPI server
// ─────────────────────────────────────────────

function waitForServer(retries = 30, delay = 500) {
  // Readiness polling gates UI startup until /api/ping is healthy.
  // Why: opening the UI before API readiness causes immediate user-facing errors,
  // broken first impressions, and avoidable support load.
  return new Promise((resolve, reject) => {
    const attempt = () => {
      http
        .get(`${API_BASE}/api/ping`, (res) => {
          if (res.statusCode === 200) resolve();
          else retry();
        })
        .on("error", retry);
    };

    const retry = () => {
      retries--;
      if (retries <= 0) {
        reject(new Error("Python server did not start in time"));
      } else {
        setTimeout(attempt, delay);
      }
    };

    attempt();
  });
}

// ─────────────────────────────────────────────
// 🖥️ Electron Window
// ─────────────────────────────────────────────

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: "License Management System",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
    show: false,
  });

  mainWindow.loadFile(
    path.join(__dirname, "..", "frontend", "pages", "login.html")
  );

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// ─────────────────────────────────────────────
// IPC
// ─────────────────────────────────────────────

ipcMain.handle("get-api-base", () => API_BASE);

// ─────────────────────────────────────────────
// 🚀 App lifecycle
// ─────────────────────────────────────────────

app.whenReady().then(async () => {
  try {
    const running = await isServerReachable();

    if (!running) {
      startPythonServer();
    }

    // This await is a hard synchronization point between renderer and backend.
    // If removed, the renderer can begin issuing API calls before FastAPI has bound
    // its port, resulting in race-condition failures during startup.
    await waitForServer();
  } catch (err) {
    console.error("❌ Backend error:", err.message);
  }

  createWindow();

  // Shortcuts
  globalShortcut.register("CommandOrControl+N", () => {
    mainWindow?.webContents.send("shortcut", "new");
  });

  globalShortcut.register("CommandOrControl+F", () => {
    mainWindow?.webContents.send("shortcut", "search");
  });
});

// ─────────────────────────────────────────────
// 🧹 Cleanup
// ─────────────────────────────────────────────

app.on("window-all-closed", () => {
  globalShortcut.unregisterAll();

  if (pyProcess) {
    pyProcess.kill();
    pyProcess = null;
  }

  app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});