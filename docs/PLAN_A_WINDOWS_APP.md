# OrgMind 方案A 实施规划 — 打磨为「真正的Windows应用」

> 本文档给执行模型看。目标：把现有 `dist\OrgMind\OrgMind.exe`（PyInstaller onedir，FastAPI后端 + 浏览器打开localhost:8080）改造成用户感知不到"这是个网页/Python程序"的桌面应用。
> 不要重新架构，只在现有代码基础上增量修改。全程使用清华镜像源装Python包（`-i https://pypi.tuna.tsinghua.edu.cn/simple`）。

## 前置状态（已完成，勿重做）
- Python 3.10.11 已装在 `C:\Program Files\Python310`
- 源码在 `c:\Users\T14\Downloads\OrgMind-Windows-x86\OrgMind\`
- 后端入口：`orgmind\main_sqlite.py`（FastAPI app）
- 已知PyInstaller坑：sqlite3模块不会被自动打包，必须手动复制 `C:\Program Files\Python310\Lib\sqlite3\*` + `_sqlite3.pyd` + `sqlite3.dll` 到 `dist\OrgMind\_internal\sqlite3\`（`scripts\build-exe.bat` 已包含此修复步骤，照抄即可）
- 已有能跑的版本：`dist\OrgMind\OrgMind.exe`，双击后台跑uvicorn，需要手动开浏览器访问 `http://localhost:8080`

## 本次要做的6件事（按顺序，每步验证通过再进行下一步）

---

### 第1步：加桌面窗口壳（去掉"要开浏览器"的违和感）

新建 `orgmind\desktop_shell.py`：
- 用 `pywebview`（已装在 `%LOCALAPPDATA%\OrgMind\venv` 里，若打包环境没装先 `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pywebview`）
- 在后台线程跑 `uvicorn.run(app, host="127.0.0.1", port=8080)`（复用 `orgmind\desktop_launcher.py` 里已写好的逻辑，直接抄过来改造即可，不要重写）
- 主线程调 `webview.create_window(title="OrgMind", url="http://127.0.0.1:8080", width=1280, height=800)` + `webview.start()`
- 这样用户看到的是一个原生Windows窗口（Edge WebView2渲染），不是浏览器标签页

验证：`python orgmind\desktop_shell.py` 能弹出一个独立窗口，标题是"OrgMind"，不是浏览器UI（没有地址栏、前进后退按钮）。

---

### 第2步：去掉console黑框

打包命令里把 `--console` 换成 `--windowed`（或 `--noconsole`，二者等价）：

```bat
pyinstaller --name OrgMind --onedir --windowed ^
    --add-data "frontend/dist;frontend/dist" ^
    --add-data "orgmind;orgmind" ^
    --hidden-import fastapi --hidden-import uvicorn ^
    --hidden-import jieba --hidden-import bcrypt ^
    --hidden-import numpy --hidden-import openai ^
    --hidden-import pyjwt --hidden-import webview ^
    --exclude-module pkg_resources --exclude-module setuptools ^
    --exclude-module torch --exclude-module sentence_transformers ^
    --exclude-module transformers --exclude-module scipy ^
    --exclude-module redis --exclude-module sqlalchemy ^
    --clean --noconfirm orgmind\desktop_shell.py
```

注意：打包目标改成了 `orgmind\desktop_shell.py`（第1步新建的文件），不再是 `main_sqlite.py`。

`--windowed` 模式下 print/异常不会显示在任何地方，所以第4步的异常处理必须做，否则出错时用户会看到"程序无响应"却不知道为什么。

别忘了同步第1步说的sqlite3手动复制流程，还是要做一遍（换了打包目标不影响这个坑）。

验证：双击 `dist\OrgMind\OrgMind.exe`，没有黑色cmd窗口闪现，直接弹出应用窗口。

---

### 第3步：加图标 + 版本信息

**3.1 图标**
现有 `frontend\dist\icon.svg` 是SVG，PyInstaller的 `--icon` 参数只认 `.ico`。需要转换：

```bash
# 用在线工具或Pillow转换，随便找一个256x256的icon.ico放到 orgmind\assets\icon.ico
# 如果没有Pillow: pip install -i https://pypi.tuna.tsinghua.edu.cn/simple Pillow
python -c "from PIL import Image; Image.open('frontend/dist/favicon.svg')..."
```
如果SVG转ico工具链太麻烦，就找一个通用的"大脑/知识库"主题ico图标临时替代，不要卡在这一步太久。

打包命令加上：`--icon orgmind\assets\icon.ico`

**3.2 版本信息**（右键exe→属性→详细信息能看到公司名/版本号，而不是"Python"）

新建 `scripts\version_info.txt`：
```python
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(2,1,0,0),
    prodvers=(2,1,0,0),
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0,0)
  ),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', 'OrgMind Team'),
        StringStruct('FileDescription', 'OrgMind - 组织知识库'),
        StringStruct('FileVersion', '2.1.0.0'),
        StringStruct('InternalName', 'OrgMind'),
        StringStruct('OriginalFilename', 'OrgMind.exe'),
        StringStruct('ProductName', 'OrgMind'),
        StringStruct('ProductVersion', '2.1.0.0')
      ])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
```
打包命令加上：`--version-file scripts\version_info.txt`

验证：右键 `dist\OrgMind\OrgMind.exe` → 属性 → 详细信息，看到"OrgMind" "2.1.0.0" "OrgMind Team"字样，而不是Python相关信息。

---

### 第4步：单实例锁 + 友好异常提示

**4.1 单实例锁**（防止用户手抖双击两次导致两个uvicorn抢8080端口）

在 `orgmind\desktop_shell.py` 开头加：
```python
import ctypes
import sys

def check_single_instance():
    mutex_name = "OrgMind_SingleInstance_Mutex_v2.1"
    handle = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    last_error = ctypes.windll.kernel32.GetLastError()
    if last_error == 183:  # ERROR_ALREADY_EXISTS
        ctypes.windll.user32.MessageBoxW(
            0, "OrgMind 已经在运行中。", "OrgMind", 0x40
        )
        sys.exit(0)
    return handle

_mutex = check_single_instance()  # 模块级，保持handle不被GC
```

**4.2 全局异常兜底**（`--windowed`模式下崩溃不能只是静默退出）
```python
def show_error_and_exit(exc_type, exc_value, exc_tb):
    import traceback
    msg = f"OrgMind 启动失败：\n\n{exc_value}\n\n请联系技术支持。"
    ctypes.windll.user32.MessageBoxW(0, msg, "OrgMind - 错误", 0x10)
    sys.exit(1)

sys.excepthook = show_error_and_exit
```
把这段放在 `desktop_shell.py` 的 `main()` 函数最外层try/except里，或者作为模块级 `sys.excepthook`。

验证：
- 双击两次exe，第二次弹出"已经在运行中"提示框，不会开第二个窗口。
- 故意改错一个import（比如临时改 `import fastapi_typo`）重新打包测试，确认弹出的是中文错误提示框而不是静默失败或者卡死。改完测试后记得改回来。

---

### 第5步：系统托盘图标（可选但强烈建议）

装 `pystray`：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pystray`

在 `desktop_shell.py` 里，webview窗口关闭时不要真退出，而是最小化到托盘：
```python
import pystray
from PIL import Image

def create_tray_icon():
    image = Image.open("orgmind/assets/icon.ico")  # 复用第3步的图标
    menu = pystray.Menu(
        pystray.MenuItem("打开 OrgMind", lambda: webview.windows[0].show()),
        pystray.MenuItem("退出", lambda: (icon.stop(), os._exit(0)))
    )
    icon = pystray.Icon("OrgMind", image, "OrgMind", menu)
    return icon
```
需要在独立线程跑托盘图标，同时hook webview窗口的关闭事件改为hide而不是destroy。这部分pywebview的事件API细节请查阅 `pywebview` 官方文档（`window.events.closing`），不要瞎猜API。

如果这一步调试超过1小时卡住，可以先跳过，不影响核心目标（第1-4步已经能让应用"看起来像真的"）。

---

### 第6步：Inno Setup安装向导

现有 `scripts\orgmind.iss` 只是草稿，需要补全并测试。

**下载安装InnoSetup**（如果没装）：
```
从清华源没有的东西只能从官网下：https://jrsoftware.org/isdl.php
或者用winget: winget install JRSoftware.InnoSetup
```

补全 `scripts\orgmind.iss`：
```ini
[Setup]
AppName=OrgMind
AppVersion=2.1.0
AppPublisher=OrgMind Team
DefaultDirName={autopf}\OrgMind
DefaultGroupName=OrgMind
OutputDir=..\dist\installer
OutputBaseFilename=OrgMind-Setup-2.1.0
SetupIconFile=..\orgmind\assets\icon.ico
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\OrgMind.exe
PrivilegesRequired=admin

[Languages]
Name: "chinese"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Files]
Source: "..\dist\OrgMind\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\OrgMind"; Filename: "{app}\OrgMind.exe"
Name: "{commondesktop}\OrgMind"; Filename: "{app}\OrgMind.exe"
Name: "{group}\卸载 OrgMind"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\OrgMind.exe"; Description: "启动 OrgMind"; Flags: nowait postinstall skipifsilent
```

关键改动点（相对旧草稿）：
- `Source` 从单个exe改成整个 `dist\OrgMind\*` 文件夹（recursesubdirs，因为是onedir模式，有一堆依赖DLL和`_internal`文件夹要一起带走）
- 加了 `UninstallDisplayIcon`，让"卸载或更改程序"列表里图标正确显示

编译：
```
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" scripts\orgmind.iss
```

验证：
1. 生成的 `dist\installer\OrgMind-Setup-2.1.0.exe` 双击能走完安装向导（选语言→选路径→安装→完成）
2. 安装后开始菜单能找到"OrgMind"
3. 桌面有图标（如果用户勾选了）
4. 控制面板"程序和功能"里能看到"OrgMind"，卸载能正常清除文件
5. 安装完成后自动启动一次，弹出的窗口正常显示登录页

---

## 验收标准（全部做完后过一遍这个清单）

- [ ] 双击 `OrgMind-Setup-2.1.0.exe` 完整走完安装向导
- [ ] 安装后从开始菜单启动，无console黑框，直接弹出应用窗口
- [ ] 窗口标题是"OrgMind"，图标是自定义图标（不是Python默认图标）
- [ ] 右键exe属性能看到正确的产品名/版本号/公司名
- [ ] 重复启动会提示"已经在运行"而不是开两个实例
- [ ] 关闭窗口后进程正常退出（或最小化到托盘，如果做了第5步）
- [ ] 任务栏能看到"OrgMind"而不是"Python"
- [ ] 控制面板能正常卸载

## 不要做的事（超出本次范围）
- 不要改动 `orgmind\main_sqlite.py` 里的业务逻辑（登录、记忆检索等API）
- 不要碰Electron相关文件（`electron\` 目录），那是另一条已废弃的路线，不用管
- 不要尝试用 `--onefile` 模式（之前踩过sqlite3坑，onedir是唯一验证过能跑的模式）
- 遇到不确定的API行为（尤其是pywebview/pystray的事件系统），去查官方文档，不要凭感觉写代码然后指望"应该能跑"
