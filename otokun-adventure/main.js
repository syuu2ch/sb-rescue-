const { app, BrowserWindow, Menu, ipcMain } = require('electron');
const path = require('path');

let mainWindow;
let isQuitting = false;

Menu.setApplicationMenu(null);

function createWindow() {
  mainWindow = new BrowserWindow({
    kiosk: true,
    fullscreen: true,
    frame: false,
    alwaysOnTop: true,
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  mainWindow.on('close', (e) => {
    if (!isQuitting) e.preventDefault();
  });

  mainWindow.webContents.on('before-input-event', (event, input) => {
    if (isQuitting) return;
    const key = (input.key || '').toLowerCase();
    const blockedWithMeta = ['q', 'w', 'h', 'm'];
    if (input.meta && blockedWithMeta.includes(key)) {
      event.preventDefault();
    }
  });
}

app.on('before-quit', (e) => {
  if (!isQuitting) e.preventDefault();
});

ipcMain.on('secret-quit', () => {
  isQuitting = true;
  app.quit();
});

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  // Intentionally a no-op: this toy app should never quit on its own,
  // only via the secret-quit IPC path above.
});
