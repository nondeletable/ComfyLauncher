<div align="center">
  <a href="https://github.com/nondeletable/ComfyLauncher">
    <img src="/README/icon/256-main.png" alt="Logo" width="100" height="100">
  </a>
<h2>ComfyLauncher</h2>
智能、快速且轻量的 ComfyUI 专用浏览器。
  <p>
    <a href="https://github.com/nondeletable/ComfyLauncher/blob/master/README/languages/readme-github-de.md">Deutsch </a> |
    <a href="https://github.com/nondeletable/ComfyLauncher/blob/master/README/languages/readme-github-es.md">Español </a> |
    <a href="https://github.com/nondeletable/ComfyLauncher/blob/master/README/languages/readme-github-cn.md">简体中文 </a> |
    <a href="https://github.com/nondeletable/ComfyLauncher/blob/master/README/languages/readme-github-ru.md">Русский </a>
    <br>
    <br>
    <img src="/README/screenshots/render.png" alt="ComfyLauncher UI" width="96%"/>
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

- **多实例启动管理器（Multi-Instance Boot Manager）。**  
  添加并管理多个 ComfyUI 便携版 build，一键启动。  
  每个实例都可以设置独立的启动参数（flags）、显示名称和图标。

&nbsp;

- **轻量级专用浏览器。**  
  占用更少 RAM，适合中端电脑或资源密集型任务。  
  不包含传统浏览器的额外开销，因此启动更快。  
  在空闲状态下比原生 Chrome 少约 30% 内存占用（已在 Windows 10 和 Windows 11 测试）。

&nbsp;

- **可选择显示或隐藏 CMD 窗口。**  
  如果后台运行的终端窗口占据任务栏、影响整洁，可以将其隐藏。

&nbsp;

- **内置控制台。**  
  当 CMD 窗口被关闭时，Launcher 会将相同的输出流显示到内置 UI 控制台（Console 按钮会自动出现）。  
  这样可以隐藏终端，同时保留详细的运行监控。

&nbsp;

- **快捷入口与常用服务器操作。**
  - 打开 **Output** 文件夹与 **ComfyUI** 文件夹
  - **Refresh UI**
  - **Restart** —— 启动或重启服务器
  - **Stop** —— 完全停止服务器

&nbsp;
 
- **支持 ComfyUI 的默认主题**，让界面风格保持一致。
- **服务器状态指示** - Online, Offline, Restarting.
- **以及更多。**
&nbsp;
&nbsp;

## ⚒ 安装

- 前往 **Releases** 区域并下载最新版本。
- 将应用程序安装到您选择的文件夹中。
- 运行 ".exe"，尽情使用！
- 请确保您已安装 Microsoft WebView2 运行时。如果没有，请下载并安装 [Evergreen Bootstrapper](https://developer.microsoft.com/en-us/microsoft-edge/webview2)。
&nbsp;
&nbsp;

## 🏓 使用方法

你可以通过以下链接查看程序功能、界面介绍及使用说明：  
[使用手册](https://github.com/nondeletable/ComfyLauncher/blob/master/README/user_manual/user_manual_cn.md)
&nbsp;
&nbsp;


## 🎯 路线图

- [x] 启动菜单支持 build 选择（从列表启动指定的 ComfyUI build）
- [x] 每个 build 支持独立启动参数（flags）
- [ ] 移植到 Linux
- [ ] 移植到 macOS
- [ ] ComfyLauncher 自动更新
- [ ] Launcher 操作快捷键
- [ ] 多语言支持
- [ ] 添加 `python-embedded` 路径设置，以便为同一个 ComfyUI build 选择不同的 Python 版本
- [ ] 可能支持启动 Standalone 版本
- [ ] ComfyUI 更新检查与更新功能
- [ ] 自定义用户主题 —— 手动设置 UI 颜色
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



