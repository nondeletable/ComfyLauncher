<div align="center">
  <a href="https://github.com/nondeletable/ComfyLauncher">
    <img src="/README/icon/256-main.png" alt="Logo" width="100" height="100">
  </a>
<h2>ComfyLauncher</h2>
Smart, fast and lightweight browser for ComfyUI.
  <p>
    <a href="https://github.com/nondeletable/ComfyLauncher/blob/master/README/languages/readme-github-en.md">English </a> |  
    <a href="https://github.com/nondeletable/ComfyLauncher/blob/master/README/languages/readme-github-de.md">Deutsch </a> |
    <a href="https://github.com/nondeletable/ComfyLauncher/blob/master/README/languages/readme-github-es.md">Español </a> |
    <a href="https://github.com/nondeletable/ComfyLauncher/blob/master/README/languages/readme-github-cn.md">简体中文 </a> |
    <a href="https://github.com/nondeletable/ComfyLauncher/blob/master/README/languages/readme-github-ru.md">Русский </a>
    <br>
    <br>
    <img src="/README/screenshots/16-build-selector.png" alt="ComfyLauncher UI" width="46%"/>
    <img src="/README/screenshots/13-themes.png" alt="ComfyLauncher Themes" width="46%"/>
    <br>
    <br>
     Join <a href="https://discord.com/invite/6nvXwXp78u">Discord </a>server to stay notified about new versions, updates, and bug reports!
  </p>
</div>

## 😎 About ComfyLauncher

ComfyLauncher is a tool for launching portable versions of ComfyUI in a convenient, fast, and “lightweight” way.

The standalone version of Comfy comes with its own launcher, which makes it very comfortable to use. That’s why I wanted to create a similar launch experience for the portable version - instead of having it open in the default browser.

I use different ComfyUI builds for different tasks: one specifically for working with WAN, another for testing new features, a third for image generation, and so on. At the same time, I don’t want to rely on a single “universal” build for everything, to avoid potential conflicts. I think many people, especially those working in production, will recognize this approach: “universal” isn’t always stable or reliable. So I chose to maintain separate portable builds for each type of task.

What I didn’t like is that ComfyUI Portable always opens in the default browser. My browser is fairly heavy, with lots of tabs, and I wanted to use a separate clean browser just for Comfy. But even then, when the Comfy server starts, it still launches the default browser. Of course, it’s not a huge problem, but it adds extra steps - and it matters even more when every megabyte of RAM counts.

So I decided to build a dedicated launcher that’s practical for real-world use. Below I describe the core features and ideas behind the app.

## 🎨 Features

- **Multi-instance boot manager.**
	Add and manage multiple portable ComfyUI builds for one-click launching.
	Customize each instance with its own launch flags, display name, and icon.
&nbsp;

- **A lightweight, dedicated browser.**  
    Uses little RAM, which is important for mid-range machines or resource-hungry workloads. It doesn’t include the extra overhead you typically get with a standard browser, so it starts up quickly.
    30% lower RAM usage than vanilla Chrome (idle) - tested on Win10 and Win11.
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
- Install the application to the folder of your choice.
- Run the ".exe" and enjoy!
- Make sure you have Microsoft WebView2 Runtime installed. If not, please download and install the [Evergreen Bootstrapper](https://developer.microsoft.com/en-us/microsoft-edge/webview2).
&nbsp;
&nbsp;

## 🏓 How to use

You can explore the program's features, interface, and instructions by following this [link](https://github.com/nondeletable/ComfyLauncher/blob/master/README/user_manual/user_manual_en.md).
&nbsp;
&nbsp;

## 🎯 Roadmap

- [x] Startup menu for build selection (so you can launch a specific ComfyUI build from a list)
- [x] Flag support for every build
- [ ] Port to Linux
- [ ] Port to macOS
- [ ] Automatic updates for Comfy Launcher
- [ ] Hotkeys for launcher actions
- [ ] Multi-language support
- [ ] Add a setting for the "python-embedded" path to allow selecting different Python versions for the same ComfyUI build
- [ ] Maybe: support for launching the Standalone version
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
