const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('keeper', {
  getListenerStatus: () => ipcRenderer.invoke('get-listener-status'),
  toggleListener: () => ipcRenderer.invoke('toggle-listener'),
  openFile: (p) => ipcRenderer.invoke('open-file', p)
});
