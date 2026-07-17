const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('orgmind', {
    platform: process.platform,
    version: '1.0.0',
    serverUrl: 'http://localhost:8080',
});
