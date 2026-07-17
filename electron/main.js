/**
 * OrgMind Desktop — AFFiNE-inspired architecture
 *
 * Bundles the PyInstaller-compiled Python backend (OrgMindBackend.exe)
 * as an Electron extraResource. On startup, spawns the backend, waits
 * for it to be ready, then opens the Electron BrowserWindow.
 *
 * No external Python, no browser dependency — self-contained desktop app.
 */
const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const http = require('http');

let mainWindow = null;
let backendProcess = null;
const PORT = 8080;
const APP_NAME = 'OrgMind';
const IS_PACKAGED = app.isPackaged;

// ============ Backend ============
function getBackendExe() {
    if (IS_PACKAGED) {
        // In packaged Electron app, backend is in resources/backend/
        const basePath = process.resourcesPath;
        return path.join(basePath, 'backend', 'OrgMindBackend.exe');
    } else {
        // Development mode: use the pre-built backend
        return path.join(__dirname, 'resources', 'backend', 'OrgMindBackend.exe');
    }
}

function getBackendWorkDir() {
    if (IS_PACKAGED) {
        return path.join(process.resourcesPath, 'backend');
    } else {
        return path.join(__dirname, 'resources', 'backend');
    }
}

function startBackend() {
    const exePath = getBackendExe();
    const workDir = getBackendWorkDir();

    if (!fs.existsSync(exePath)) {
        dialog.showErrorBox(
            'Backend Not Found',
            `Cannot find OrgMind backend at:\n${exePath}\n\n` +
            'Please reinstall the application.'
        );
        app.quit();
        return false;
    }

    console.log(`[OrgMind] Starting backend: ${exePath}`);
    console.log(`[OrgMind] Working dir: ${workDir}`);

    const env = {
        ...process.env,
        ORGMIND_DB_PATH: path.join(app.getPath('userData'), 'orgmind.db'),
        ORGMIND_CONFIG_DIR: path.join(app.getPath('userData'), 'config'),
    };

    backendProcess = spawn(exePath, [], {
        cwd: workDir,
        env,
        stdio: ['pipe', 'pipe', 'pipe'],
        windowsHide: true,
    });

    backendProcess.stdout.on('data', (data) => {
        console.log(`[Backend] ${data.toString().trim()}`);
    });

    backendProcess.stderr.on('data', (data) => {
        console.error(`[Backend] ${data.toString().trim()}`);
    });

    backendProcess.on('error', (err) => {
        dialog.showErrorBox('Backend Error', `Failed to start backend:\n\n${err.message}`);
        app.quit();
    });

    backendProcess.on('exit', (code) => {
        console.log(`[OrgMind] Backend exited with code ${code}`);
        if (code !== 0 && mainWindow) {
            dialog.showErrorBox('Backend Stopped',
                `The OrgMind backend stopped unexpectedly (exit code ${code}).\n\nPlease restart the application.`);
            app.quit();
        }
    });

    return true;
}

function waitForBackend(maxRetries = 120) {
    return new Promise((resolve, reject) => {
        let attempts = 0;
        const check = () => {
            attempts++;
            const req = http.get(`http://127.0.0.1:${PORT}/health`, (res) => {
                if (res.statusCode === 200) {
                    resolve();
                } else if (attempts < maxRetries) {
                    setTimeout(check, 500);
                } else {
                    reject(new Error('Backend returned non-200 status'));
                }
            });
            req.on('error', () => {
                if (attempts < maxRetries) {
                    setTimeout(check, 500);
                } else {
                    reject(new Error('Backend did not start within 60 seconds'));
                }
            });
            req.setTimeout(2000, () => {
                req.destroy();
                if (attempts < maxRetries) {
                    setTimeout(check, 500);
                } else {
                    reject(new Error('Backend start timed out'));
                }
            });
        };
        setTimeout(check, 500);
    });
}

// ============ Window ============
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1280,
        height: 800,
        minWidth: 900,
        minHeight: 600,
        title: APP_NAME,
        backgroundColor: '#fafafa',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
        },
        show: false,
    });

    mainWindow.setMenuBarVisibility(false);
    mainWindow.removeMenu();

    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
        mainWindow.focus();
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    mainWindow.loadURL(`http://127.0.0.1:${PORT}`);
}

// ============ App Lifecycle ============
app.whenReady().then(async () => {
    console.log(`[OrgMind] Starting v2.1.0`);

    if (!startBackend()) return;

    try {
        await waitForBackend();
        console.log('[OrgMind] Backend is ready');
        createWindow();
    } catch (err) {
        dialog.showErrorBox('Startup Failed',
            `Could not start OrgMind:\n\n${err.message}\n\n` +
            'Please ensure no other instance is running on port 8080.');
        app.quit();
    }
});

app.on('window-all-closed', () => {
    app.quit();
});

app.on('before-quit', () => {
    if (backendProcess) {
        console.log('[OrgMind] Shutting down backend...');
        try {
            require('child_process').execSync(`taskkill /pid ${backendProcess.pid} /T /F 2>nul`, { stdio: 'ignore' });
        } catch (_) {}
        backendProcess = null;
    }
});

app.on('quit', () => {
    if (backendProcess) {
        try {
            require('child_process').execSync(`taskkill /pid ${backendProcess.pid} /T /F 2>nul`, { stdio: 'ignore' });
        } catch (_) {}
        backendProcess = null;
    }
});
