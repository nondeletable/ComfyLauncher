<div align="center">
  <a href="https://github.com/nondeletable/ComfyLauncher">
    <img src="/README/icon/256-main.png" alt="Logo" width="100" height="100">
  </a>
<h2>ComfyLauncher</h2>
  <p>
    <a href="https://github.com/nondeletable/ComfyLauncher/tree/master/README/readme-github-en.md">English </a> |  
    <a href="https://github.com/nondeletable/ComfyLauncher/tree/master/README/readme-github-de.md">Deutsch </a> |
    <a href="https://github.com/nondeletable/ComfyLauncher/tree/master/README/readme-github-es.md">Español </a> |
    <a href="https://github.com/nondeletable/ComfyLauncher/tree/master/README/readme-github-cn.md">简体中文 </a> |
    <a href="https://github.com/nondeletable/ComfyLauncher/tree/master/README/readme-github-ru.md">Русский </a>
    <br>
    <br>
    <img src="/README/screenshots/06-main%20window.png" alt="ComfyLauncher UI" width="46%"/>
    <img src="/README/screenshots/13-themes.png" alt="ComfyLauncher Themes" width="46%"/>
    <br>
    <br>
  </p>
</div>


## 😎 关于 ComfyLauncher

ComfyLauncher 是一个用于启动 ComfyUI 便携版（portable builds）的工具：方便、快速，而且“轻量”。

Comfy 的 Standalone 版本自带 Launcher，用起来非常舒服。所以我也想为便携版做一个类似的启动体验，而不是每次都在默认浏览器里打开。

我会为不同任务使用不同的 ComfyUI build：一个专门跑 WAN，一个用来测试新功能，另一个用于图像生成等。同时我不想把所有事情都压在一个“万能 build”上，以避免潜在冲突。我想很多人（尤其是生产环境）都熟悉这种做法：“万能”并不总是稳定或可靠。因此我为每种任务类型维护独立的 portable builds。

让我不舒服的一点是：ComfyUI Portable 总会在默认浏览器里打开。我的浏览器很“重”，开了很多标签页；我更想要一个专门给 Comfy 用的干净浏览器。但即便你这样做，在启动服务器时它还是会拉起默认浏览器。当然这不是什么大问题，但确实增加了额外步骤……而且当每一 MB 内存都很宝贵时，这就变得更明显。

所以我决定做一个真正适合日常使用的专用 Launcher。下面我会介绍这个应用的核心功能与主要想法。
&nbsp;
&nbsp;

## 🎨 功能

- **轻量、专用的 Launcher。**  
    占用更少的 RAM——对中端电脑或资源吃紧的工作负载很重要。它没有常规浏览器那种额外开销，因此启动很快。  
&nbsp;
 
- **可选择显示或隐藏 CMD 窗口。**  
    如果你讨厌后台跑着的终端窗口占着任务栏、显得很乱，你可以把它隐藏掉。  
&nbsp;
 
- **内置控制台。**  
    当 CMD 窗口被关闭时，Launcher 会把同样的输出流式显示到自己的 UI 控制台里（Console 按钮会自动出现）。这样你可以隐藏终端，但仍然保留详细监控。  
&nbsp;
 
- **快捷入口与常用服务器操作。**
    - 打开 **Output** 文件夹与 **ComfyUI** 文件夹
    - **Refresh UI**
    - **Restart** - 启动并重启服务器
    - **Stop** - 完全停止服务器  
&nbsp;
 
- **支持 ComfyUI 的默认主题**，让界面风格保持一致。
- **服务器状态指示** - Online, Offline, Restarting.
- **以及更多。**
&nbsp;
&nbsp;

## ⚒ 安装

- 前往 **Releases** 区域并下载最新版本。
- 将压缩包解压到你喜欢的文件夹。
- 运行 ".exe"，尽情使用！
- 请确保您已安装 Microsoft WebView2 运行时。如果没有，请下载并安装 [Evergreen Bootstrapper](https://developer.microsoft.com/en-us/microsoft-edge/webview2)。
&nbsp;
&nbsp;

## 🏓 使用方法

**1. 使用 exe 启动**  
安装后，你可以通过 ".exe" 启动 Comfy Launcher。你也可以创建桌面快捷方式或固定到任务栏，以便更快访问。

![1](/README/screenshots/01_shortcut.png)
&nbsp;
&nbsp;

**2. 选择路径 - 点击 "Folder" 按钮**  
首次启动时，Comfy Launcher 会让你选择包含便携版 ComfyUI 的目录。请选择包含 `main.py` 的文件夹，也就是 ComfyUI 的根目录。

![2](/README/screenshots/02-build%20folder.png)
&nbsp;
&nbsp;

**3. 选择文件夹**  
这是 ComfyUI 的主文件夹，里面包含 "main.py"、"custom_nodes" 等内容。

![3](/README/screenshots/03-folder.png)
&nbsp;
&nbsp;

**4. 点击 OK 确认**  

![4](/README/screenshots/04-hit%20ok.png)
&nbsp;
&nbsp;

**5. Preloader**  
ComfyUI 加载屏。默认情况下 CMD 窗口是关闭的，启动时不会出现。如果你启用它，终端窗口会与 Preloader 一起显示。

![5](/README/screenshots/05-preloader.png)
&nbsp;
&nbsp;

**6. 主界面**  
应用主窗口。所有控制项都在顶部栏。窗口是无边框的，因此不会被 Windows 的默认边框影响整体视觉风格。

![6](/README/screenshots/06-main%20window%20alt.png)
&nbsp;
&nbsp;

**7. 左侧面板**  
- 应用图标与名称
- **Settings** - 打开 Comfy Launcher 设置
- **Open ComfyUI folder** - 打开 ComfyUI 主目录（包含 "main.py"、"custom_nodes"、"models" 等）
- **Open Output folder** - 打开包含生成内容的 "Output" 文件夹
- **Refresh UI** - 刷新 ComfyUI 界面

![7](/README/screenshots/07-left%20corner.png)
&nbsp;
&nbsp;

**8. 右侧面板**  
- **Status** - 服务器状态指示（Online, Offline, Restarting）
- **Console** - 打开内置控制台查看 CMD 输出（仅当 Settings 中关闭 CMD 时显示）
- **Restart ComfyUI** - 重启服务器。如果服务器已停止（Offline），该按钮会作为 **Start** 使用并启动服务器。我刻意没有拆成两个按钮，而是把两个行为合并在一个按钮里。
- **Stop ComfyUI** - 完全停止服务器
- 窗口控制按钮

![8](/README/screenshots/08-right%20corner.png)
&nbsp;
&nbsp;

**9. Settings / Comfy Folder**  
Comfy Folder - 在这里设置你当前使用的 ComfyUI build 路径。首次启动时也会出现同样的设置流程。  
下面有一个按钮可以跳转到官方站点，你可以在那里下载不同版本。

![9](/README/screenshots/09-comfy%20folder.png)
&nbsp;
&nbsp;

**10. Settings / CMD Window**  
CMD Window - 配置在启动 ComfyUI 时是否显示终端窗口。

![10](/README/screenshots/10-cmd.png)
&nbsp;
&nbsp;

**11. Settings / Exit Options**  
Exit Options - 当你关闭 Comfy Launcher 时，应用会询问是否要停止 ComfyUI 服务器。在这个页面你可以关闭该对话框并选择自动行为：
- **Always stop server** - 完全停止 Comfy Launcher 与 ComfyUI
- **Never stop server** - 关闭 Comfy Launcher，但让 ComfyUI 服务器继续在后台运行

![11](/README/screenshots/11-exit.png)
&nbsp;
&nbsp;

**12. Settings / Color Themes**  
Color Themes - 自定义 Comfy Launcher 的外观。包含 4 个内置主题，并支持 ComfyUI themes。
- **Select** - 选择 JSON 格式主题
- **Download** - 从 "www.comfyui-themes.com" 下载主题

![12](/README/screenshots/12-themes.png)
&nbsp;
&nbsp;

**13. 不同主题示例**  

![13](/README/screenshots/13-themes.png)
&nbsp;
&nbsp;

**14. Settings / Launcher Logs**  
Launcher Logs - 显示 Launcher 的动作日志，主要用于调试。

![14](/README/screenshots/14-logs.png)
&nbsp;
&nbsp;

**15. Settings / About**  
About - 关于应用、关于我，以及联系链接的简要信息。

![15](/README/screenshots/15-about.png)
&nbsp;
&nbsp;

## 🥁 故障排查

我们的小团队尽可能仔细地测试了程序、捕捉并修复了使用过程中出现的 bug。但由于每个人的系统和使用场景都不同，不排除有人仍会遇到问题。

如果出现故障，你可以在 [Discord](https://discord.com/invite/6nvXwXp78u) 联系我。这是反馈问题最快的方式。所以如果你遇到 bug，我会非常感谢你告诉我！

- 当前版本的 Comfy Launcher 还没有实现手动选择 `python-embedded` 目录（ComfyUI 需要）。应用默认认为 `python-embedded` 位于标准位置——就在 ComfyUI 主目录旁边。  
&nbsp;
 
- 很遗憾，由于无边框 UI 的特性，目前还不支持窗口缩放，因此应用以全屏模式运行。你可以拖动窗口，但暂时无法调整大小。Windows 的 “Snap”（贴边吸附）目前也无法使用。我会在未来寻找解决方案——如果你知道如何实现，也欢迎分享！
&nbsp;
&nbsp;

## 🎯 路线图

- [ ] 移植到 Linux
- [ ] 移植到 macOS
- [ ] Comfy Launcher 自动更新
- [ ] Launcher 操作热键
- [ ] 多语言支持
- [ ] 启动时的 build 选择菜单（可从列表启动指定的 ComfyUI build）
- [ ] 添加 `python-embedded` 路径设置，以便为同一个 ComfyUI build 选择不同的 Python 版本
- [ ] 计划：支持启动 Standalone 版本
- [ ] ComfyUI 更新检查与更新 ComfyUI 的能力
- [ ] Custom User Theme — 手动设置 UI 颜色
- [ ] 外观与细节优化
&nbsp;
&nbsp;

## 💾 技术栈

- **Python 3.11+**
- **PyQt6** - 用于桌面 UI
- **Subprocess** - 用于处理 ComfyUI 的启动/执行
- **JSON** - 用于保存用户偏好
- **PyInstaller** - 用于构建 ".exe" Releases
&nbsp;
&nbsp;

## ☎ 联系方式

如果你想合作或讨论工作机会，可以使用下面任意联系方式。
如需支持/报 bug，请使用 Discord 或 GitHub Issues。我通常会在 24 小时内回复。

- 🐙 **GitHub** - 页面（文档、Releases、源代码）  
  https://github.com/nondeletable

- 💬 **Discord** - 新闻、支持、提问与 bug 报告  
  https://discord.com/invite/6nvXwXp78u

- ✈️ **Telegram** - 私信  
  https://t.me/nondeletable

- 📧 **Email** - 用于正式或商务咨询  
  nondeletable@gmail.com

- 💼 **LinkedIn** - 职业主页  
  https://www.linkedin.com/in/aleksandra-gicheva-3b0264341/

- ☕ **Boosty** - 通过捐赠支持我的工作与项目  
  https://boosty.to/codebird/donate
&nbsp;
&nbsp;

感谢你使用 ComfyLauncher！我投入了很多心血，希望它能让你的工作流程更轻松、更快速 🙂



