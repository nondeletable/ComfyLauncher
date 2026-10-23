<div align="center">
  <a href="https://github.com/nondeletable/ComfyLauncher">
    <img src="/README/icon/256-main.png" alt="Logo" width="100" height="100">
  </a>
<h2>ComfyLauncher</h2>
  <p>
    <a href="https://github.com/nondeletable/ComfyLauncher/blob/master/README/languages/readme-github-en.md">English </a> |  
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


## 😎 Über ComfyLauncher

ComfyLauncher ist ein Tool zum Starten portabler Versionen von ComfyUI – bequem, schnell und „leichtgewichtig“.

Die Standalone-Version von Comfy hat ihren eigenen Launcher, was sehr angenehm ist. Deshalb wollte ich ein ähnliches Start-Erlebnis auch für die portable Version schaffen – statt dass sie sich immer im Standardbrowser öffnet.

Ich nutze unterschiedliche ComfyUI-Builds für verschiedene Aufgaben: einen speziell für WAN, einen zum Testen neuer Features, einen dritten für Bildgenerierung usw. Gleichzeitig möchte ich mich nicht auf einen einzigen „universellen“ Build für alles verlassen, um mögliche Konflikte zu vermeiden. Ich denke, viele – besonders im Production-Umfeld – kennen diesen Ansatz: „universell“ ist nicht immer stabil oder zuverlässig. Deshalb pflege ich separate portable Builds für jeden Aufgabentyp.

Was mich gestört hat: ComfyUI Portable öffnet sich immer im Standardbrowser. Mein Browser ist ziemlich schwer, mit vielen Tabs, und ich wollte einen separaten, sauberen Browser nur für Comfy nutzen. Aber selbst dann startet beim Server-Start trotzdem der Standardbrowser. Klar, das ist kein riesiges Problem – aber es sind extra Schritte. Und es ist umso relevanter, wenn jedes Megabyte RAM zählt.

Also habe ich entschieden, einen dedizierten Launcher zu bauen, der im echten Alltag praktisch ist. Unten beschreibe ich die wichtigsten Features und Ideen hinter der App.
&nbsp;
&nbsp;

## 🎨 Funktionen

- **Multi-Instance-Boot-Manager.**  
  Füge mehrere portable ComfyUI-Builds hinzu und verwalte sie – Start per Klick.  
  Jede Instanz kann eigene Start-Flags, einen Anzeigenamen und ein Icon erhalten.

&nbsp;

- **Ein leichtgewichtiger, dedizierter Browser.**  
  Geringer RAM-Verbrauch – wichtig für Mittelklasse-Rechner oder ressourcenintensive Workloads.  
  Kein typischer Browser-Overhead, dadurch schneller Start.  
  30 % weniger RAM-Nutzung als Vanilla Chrome (Idle) – getestet unter Windows 10 und Windows 11.

&nbsp;

- **Option, das CMD-Fenster ein- oder auszublenden.**  
  Wenn dich das im Hintergrund laufende Terminal-Fenster stört, kannst du es ausblenden.

&nbsp;

- **Integrierte Konsole.**  
  Ist das CMD-Fenster deaktiviert, streamt der Launcher dieselbe Ausgabe in eine eigene UI-Konsole (der Console-Button erscheint automatisch).  
  So kannst du das Terminal ausblenden, ohne auf detailliertes Monitoring zu verzichten.

&nbsp;
 
- **Schnellzugriff und häufig genutzte Server-Aktionen.**
    - Öffne den **Output**-Ordner und den **ComfyUI**-Ordner
    - **Refresh UI**
    - **Restart** – Server starten und neu starten
    - **Stop** – Server vollständig stoppen  
&nbsp;
 
- **Support für ComfyUIs Standard-Themes**, damit die Oberfläche konsistent bleibt.
- **Server-Statusanzeige** – Online, Offline, Restarting.
- **Und mehr.**
&nbsp;
&nbsp;

## ⚒ Installation

- Gehe zum Bereich **Releases** und lade das neueste Release herunter.
- Installieren Sie die Anwendung in einem Ordner Ihrer Wahl.
- Starte die ".exe" und viel Spaß!
- Stellen Sie sicher, dass Microsoft WebView2 Runtime installiert ist. Falls nicht, laden Sie bitte den [Evergreen Bootstrapper](https://developer.microsoft.com/en-us/microsoft-edge/webview2) herunter und installieren Sie ihn.
&nbsp;
&nbsp;

## 🏓 Verwendung

Du kannst die Funktionen, die Benutzeroberfläche und die Anleitung über diesen  
[Link](https://github.com/nondeletable/ComfyLauncher/blob/master/README/user_manual/user_manual_de.md) erkunden.
&nbsp;
&nbsp;

## 🎯 Fahrplan

- [x] Startmenü zur Build-Auswahl (einen bestimmten ComfyUI-Build aus einer Liste starten)
- [x] Unterstützung von Start-Flags für jeden Build
- [ ] Portierung auf Linux
- [ ] Portierung auf macOS
- [ ] Automatische Updates für ComfyLauncher
- [ ] Hotkeys für Launcher-Aktionen
- [ ] Mehrsprachige Unterstützung
- [ ] Einstellung für den `python-embedded`-Pfad hinzufügen, um unterschiedliche Python-Versionen für denselben ComfyUI-Build auszuwählen
- [ ] Eventuell: Unterstützung für den Start der Standalone-Version
- [ ] ComfyUI-Update-Checks und Möglichkeit zur Aktualisierung von ComfyUI
- [ ] Benutzerdefiniertes Theme – UI-Farben manuell festlegen
- [ ] Kosmetische Verbesserungen

&nbsp;
&nbsp;

## 💾 Technologien

- **Python 3.11+**
- **PyQt6** - für Desktop-UI
- **Subprocess** - zum Starten/Steuern von ComfyUI
- **JSON** - zum Speichern der Nutzereinstellungen
- **PyInstaller** - zum Bauen der ".exe"-Releases
&nbsp;
&nbsp;

## ☎ Kontakt

Wenn du zusammenarbeiten oder über eine Jobmöglichkeit sprechen möchtest, nutze gerne einen der Kontakte unten.
Für Support/Bugs bitte Discord oder GitHub Issues verwenden. Ich antworte in der Regel innerhalb von 24 Stunden.

- 🐙 **GitHub** - Seite (Dokumentation, Releases, Quellcode)  
  https://github.com/nondeletable

- 💬 **Discord** - News, Support, Fragen und Bug-Reports  
  https://discord.com/invite/6nvXwXp78u

- ✈️ **Telegram** - Direktnachrichten  
  https://t.me/nondeletable

- 📧 **Email** - für formelle oder geschäftliche Anfragen   
  nondeletable@gmail.com

- 💼 **LinkedIn** - professionelles Profil  
  https://www.linkedin.com/in/aleksandra-gicheva-3b0264341/

- ☕ **Boosty** - unterstütze meine Arbeit und Projekte mit Spenden  
  https://boosty.to/codebird/donate
&nbsp;
&nbsp;

Danke, dass du ComfyLauncher nutzt! Ich habe sehr viel Arbeit hineingesteckt, und ich hoffe, es macht deinen Workflow einfacher und schneller 🙂
