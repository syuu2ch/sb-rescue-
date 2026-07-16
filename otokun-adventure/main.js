const { app, BrowserWindow, Menu, globalShortcut } = require('electron');
const path = require('path');

const QUIT_ACCELERATOR = 'Control+Shift+Q';

let mainWindow;
let isQuitting = false;

Menu.setApplicationMenu(null);

function quitGame() {
  isQuitting = true;
  app.quit();
}

function createWindow() {
  mainWindow = new BrowserWindow({
    fullscreen: true,
    frame: false,
    autoHideMenuBar: true,
    webPreferences: {
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

app.whenReady().then(() => {
  createWindow();
  // Registered as a native OS-level accelerator (not tracked via renderer
  // keydown events), so it works regardless of window focus/fullscreen
  // state and isn't affected by macOS's dead-key accent composition.
  globalShortcut.register(QUIT_ACCELERATOR, quitGame);
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
});

app.on('window-all-closed', () => {
  // Intentionally a no-op: this toy app should never quit on its own,
  // only via the global quit shortcut above.
});
