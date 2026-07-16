const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('otokunAPI', {
  secretQuit: () => ipcRenderer.send('secret-quit'),
});
