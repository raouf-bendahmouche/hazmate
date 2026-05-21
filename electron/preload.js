/**
 * Electron Preload Script
 * Exposes a minimal, safe bridge between main process and renderer.
 */
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  getApiBase: () => ipcRenderer.invoke("get-api-base"),
  onShortcut: (callback) => ipcRenderer.on("shortcut", (_evt, cmd) => callback(cmd)),
  removeShortcutListeners: () => ipcRenderer.removeAllListeners("shortcut"),
});
