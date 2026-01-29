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
    <img src="/README/screenshots/render.png" alt="ComfyLauncher UI" width="96%"/>
    <br>
    <br>
  </p>
</div>


## 😎 About ComfyLauncher

ComfyLauncher is a tool for launching portable versions of ComfyUI in a convenient, fast, and “lightweight” way.

The standalone version of Comfy comes with its own launcher, which makes it very comfortable to use. That’s why I wanted to create a similar launch experience for the portable version - instead of having it open in the default browser.

I use different ComfyUI builds for different tasks: one specifically for working with WAN, another for testing new features, a third for image generation, and so on. At the same time, I don’t want to rely on a single “universal” build for everything, to avoid potential conflicts. I think many people, especially those working in production, will recognize this approach: “universal” isn’t always stable or reliable. So I chose to maintain separate portable builds for each type of task.

What I didn’t like is that ComfyUI Portable always opens in the default browser. My browser is fairly heavy, with lots of tabs, and I wanted to use a separate clean browser just for Comfy. But even then, when the Comfy server starts, it still launches the default browser. Of course, it’s not a huge problem, but it adds extra steps - and it matters even more when every megabyte of RAM counts.

So I decided to build a dedicated launcher that’s practical for real-world use. Below I describe the core features and ideas behind the app.

## 🎨 Features

- **A lightweight, dedicated launcher.**  
    Uses little RAM, which is important for mid-range machines or resource-hungry workloads. It doesn’t include the extra overhead you typically get with a standard browser, so it starts up quickly.  
&nbsp;
 
- **Option to show or hide the CMD window.**  
    If the terminal window running in the background and cluttering your taskbar is annoying, you can hide it.  
&nbsp;
 
- **Built-in console.**  
    When the CMD window is disabled, the launcher streams the same output into a dedicated UI console (the console button appears automatically). This way you can hide the terminal without losing detailed monitoring.  
&nbsp;
 
- **Quick access controls and commonly used server actions.**
    - Open the **Output** directory and the **ComfyUI** directory
    - **Refresh UI**
    - **Restart** - start and restart the server
    - **Stop** - fully stop the server  
&nbsp;
 
- **Support for ComfyUI’s default themes** to keep the interface consistent.
- **Server status indicator** - Online, Offline, Restarting.
- **And more.**
&nbsp;
&nbsp;

## ⚒ Installation

- Go to the **Releases** section and download the latest release.
- Extract (unzip) the archive to a folder of your choice.
- Run the ".exe" and enjoy!
- Make sure you have Microsoft WebView2 Runtime installed. If not, please download and install the [Evergreen Bootstrapper](https://developer.microsoft.com/en-us/microsoft-edge/webview2).
&nbsp;
&nbsp;

## 🏓 How to use

**1. Start with exe**  
After installation, you can launch Comfy Launcher using the ".exe". You can also create a desktop or taskbar shortcut for quicker access.

![1](/README/screenshots/01_shortcut.png)
&nbsp;
&nbsp;

**2. Select the path - hit "Folder" button**  
On first launch, Comfy Launcher will ask you to select the directory that contains your portable ComfyUI. Choose the folder where `main.py` is located - that is, the root ComfyUI directory.

![2](/README/screenshots/02-build%20folder.png)
&nbsp;
&nbsp;

**3. Select the folder**  
This is the main ComfyUI folder containing "main.py", "custom_nodes", and so on.

![3](/README/screenshots/03-folder.png)
&nbsp;
&nbsp;

**4. Click OK to confirm**

![4](/README/screenshots/04-hit%20ok.png)
&nbsp;
&nbsp;

**5. Preloader**  
ComfyUI loading screen. By default, the CMD window is disabled and won’t appear during startup. If you enable it, the terminal window will show up alongside the preloader.

![5](/README/screenshots/05-preloader.png)
&nbsp;
&nbsp;

**6. Main UI**  
The main application window. All controls are placed in the top bar. The window is frameless, so the standard Windows border doesn’t interfere with the overall visual style.

![6](/README/screenshots/06-main%20window%20alt.png)
&nbsp;
&nbsp;

**7. Left panel**
- App icon and name
- **Settings** - opens Comfy Launcher settings
- **Open ComfyUI folder** - opens the main ComfyUI directory (where "main.py", "custom_nodes", "models", etc. are located)
- **Open Output folder** - opens the "Output" folder containing generated content
- **Refresh UI** - refreshes the ComfyUI interface

![7](/README/screenshots/07-left%20corner.png)
&nbsp;
&nbsp;

**8. Right panel**
- **Status** - server state indicator (Online, Offline, Restarting)
- **Console** - opens the built-in console with CMD output (only appears when CMD is disabled in settings)
- **Restart ComfyUI** - restarts the server. If the server is stopped (Offline), this button acts as **Start** and launches it. I decided not to split these into two separate buttons and implemented both behaviors in one.
- **Stop ComfyUI** - fully stops the server
- Window controls

![8](/README/screenshots/08-right%20corner.png)
&nbsp;
&nbsp;

**9. Settings / Comfy Folder**  
Comfy Folder - lets you set the path to your active ComfyUI build. The same setup appears on first launch.  
At the bottom there’s a button that links to the official website where you can download different versions.

![9](/README/screenshots/09-comfy%20folder.png)
&nbsp;
&nbsp;

**10. Settings / CMD Window**  
CMD Window - configure whether the terminal window is shown when ComfyUI starts.

![10](/README/screenshots/10-cmd.png)
&nbsp;
&nbsp;

**11. Settings / Exit Options**  
Exit Options - when closing Comfy Launcher, the app asks whether you want to stop the ComfyUI server. On this tab you can disable that dialog and choose an automatic action:
- **Always stop server** - fully stops both Comfy Launcher and ComfyUI
- **Never stop server** - closes Comfy Launcher, but keeps the ComfyUI server running in the background

![11](/README/screenshots/11-exit.png)
&nbsp;
&nbsp;

**12. Settings / Color Themes**  
Color Themes - customize Comfy Launcher appearance. Includes 4 built-in themes and support for ComfyUI themes.
- **Select** - choose a theme in JSON format
- **Download** - download themes from "www.comfyui-themes.com"

![12](/README/screenshots/12-themes.png)
&nbsp;
&nbsp;

**13. Different theme examples**

![13](/README/screenshots/13-themes.png)
&nbsp;
&nbsp;

**14. Settings / Launcher Logs**  
Launcher Logs - shows the launcher action log, primarily for debugging.

![14](/README/screenshots/14-logs.png)
&nbsp;
&nbsp;

**15. Settings / About**  
About - brief info about the app, about me, and contact links.

![15](/README/screenshots/15-about.png)
&nbsp;
&nbsp;

## 🥁 Troubleshooting

Our small team did our best to test the app thoroughly, catch issues that appeared during use, and fix them. However, since everyone’s systems and workflows are different, some bugs may still show up for certain users.

If something breaks, you can contact me on [Discord](https://discord.com/invite/6nvXwXp78u). This is the fastest way to report an issue. So if you run into a bug, I’d really appreciate it if you let me know!

- In the current version of Comfy Launcher, manual selection of the "python-embedded" directory (required for ComfyUI) is not implemented yet. The app assumes that "python-embedded" is located in the default place - next to the main ComfyUI folder.

- Unfortunately, due to the specifics of a frameless UI, window resizing is not supported yet, so the app runs in fullscreen mode. You can drag the window, but you can’t resize it for now. Windows “snap” (docking to screen edges) also doesn’t work at the moment. I’ll be looking for a solution in the future - and if you know how to implement this, I’d be happy if you share it!

- If you see a white screen instead of ComfyUI after launching ComfyLauncher, there is a high chance that WebView2 Runtime is missing or corrupted on your system. In this case, try downloading the [Evergreen Bootstrapper](https://developer.microsoft.com/en-us/microsoft-edge/webview2) from the official Microsoft website and install or reinstall it.

    We encountered this situation during testing on Windows 10 22H2. WebView2 Runtime was installed on the system, but for some reason it was “broken,” likely after using one of the system optimization utilities. The issue was resolved by removing the faulty runtime and installing a fresh one.
&nbsp;
&nbsp;

## 🎯 Roadmap

- [ ] Port to Linux
- [ ] Port to macOS
- [ ] Automatic updates for Comfy Launcher
- [ ] Hotkeys for launcher actions
- [ ] Multi-language support
- [ ] Startup menu for build selection (so you can launch a specific ComfyUI build from a list)
- [ ] Add a setting for the "python-embedded" path to allow selecting different Python versions for the same ComfyUI build
- [ ] Planned: support for launching the Standalone version
- [ ] ComfyUI update checks and the ability to update ComfyUI
- [ ] Custom User Theme - set UI colors manually
- [ ] Cosmetic improvements
&nbsp;
&nbsp;

## 💾 Technologies

- **Python 3.11+**
- **PyQt6** - for desktop UI
- **Subprocess** - to handle ComfyUI execution
- **JSON** - to store user preferences
- **PyInstaller** - to build ".exe" releases
&nbsp;
&nbsp;

## ☎ Contacts

If you’d like to collaborate or discuss a job opportunity - use any of the contacts below.
For support/bugs, please use Discord or GitHub Issues. I usually reply within 24 hours.

- 🐙 **GitHub** page (docs, releases, source code)  
  https://github.com/nondeletable

- 💬 **Discord** - news, support, questions, and bug reports  
  https://discord.com/invite/6nvXwXp78u

- ✈️ **Telegram** - direct messages  
  https://t.me/nondeletable

- 📧 **Email** - for formal or business inquiries  
  nondeletable@gmail.com

- 💼 **LinkedIn** - professional profile  
  https://www.linkedin.com/in/aleksandra-gicheva-3b0264341/

- ☕ **Boosty** - support my work and projects with donations  
  https://boosty.to/codebird/donate  
&nbsp;

Thank you for using ComfyLauncher! I’ve put a lot of work into it, and I hope it makes your workflow easier and faster 🙂