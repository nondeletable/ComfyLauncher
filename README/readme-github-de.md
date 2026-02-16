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


## 😎 Über ComfyLauncher

ComfyLauncher ist ein Tool zum Starten portabler Versionen von ComfyUI – bequem, schnell und „leichtgewichtig“.

Die Standalone-Version von Comfy hat ihren eigenen Launcher, was sehr angenehm ist. Deshalb wollte ich ein ähnliches Start-Erlebnis auch für die portable Version schaffen – statt dass sie sich immer im Standardbrowser öffnet.

Ich nutze unterschiedliche ComfyUI-Builds für verschiedene Aufgaben: einen speziell für WAN, einen zum Testen neuer Features, einen dritten für Bildgenerierung usw. Gleichzeitig möchte ich mich nicht auf einen einzigen „universellen“ Build für alles verlassen, um mögliche Konflikte zu vermeiden. Ich denke, viele – besonders im Production-Umfeld – kennen diesen Ansatz: „universell“ ist nicht immer stabil oder zuverlässig. Deshalb pflege ich separate portable Builds für jeden Aufgabentyp.

Was mich gestört hat: ComfyUI Portable öffnet sich immer im Standardbrowser. Mein Browser ist ziemlich schwer, mit vielen Tabs, und ich wollte einen separaten, sauberen Browser nur für Comfy nutzen. Aber selbst dann startet beim Server-Start trotzdem der Standardbrowser. Klar, das ist kein riesiges Problem – aber es sind extra Schritte. Und es ist umso relevanter, wenn jedes Megabyte RAM zählt.

Also habe ich entschieden, einen dedizierten Launcher zu bauen, der im echten Alltag praktisch ist. Unten beschreibe ich die wichtigsten Features und Ideen hinter der App.
&nbsp;
&nbsp;

## 🎨 Funktionen

- **Ein leichter, dedizierter Launcher.**  
    Nutzt wenig RAM – wichtig für Mittelklasse-Rechner oder ressourcenhungrige Workloads. Er bringt nicht den typischen Overhead eines Standardbrowsers mit und startet daher schnell.  
&nbsp;
 
- **Option, das CMD-Fenster ein- oder auszublenden.**  
    Wenn dich ein Terminal-Fenster, das im Hintergrund läuft und die Taskleiste „zumüllt“, nervt, kannst du es ausblenden.  
&nbsp;
 
- **Integrierte Konsole.**  
    Wenn das CMD-Fenster deaktiviert ist, streamt der Launcher dieselbe Ausgabe in eine eigene UI-Konsole (der Console-Button erscheint automatisch). So kannst du das Terminal verstecken, ohne auf detailliertes Monitoring zu verzichten.  
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
- Entpacke (unzip) das Archiv in einen Ordner deiner Wahl.
- Starte die ".exe" und viel Spaß!
- Stellen Sie sicher, dass Microsoft WebView2 Runtime installiert ist. Falls nicht, laden Sie bitte den [Evergreen Bootstrapper](https://developer.microsoft.com/en-us/microsoft-edge/webview2) herunter und installieren Sie ihn.
&nbsp;
&nbsp;

## 🏓 Verwendung

**1. Start with exe**  
Nach der Installation kannst du Comfy Launcher über die ".exe" starten. Du kannst auch eine Verknüpfung auf dem Desktop oder in der Taskleiste erstellen, um schneller darauf zuzugreifen.

![1](/README/screenshots/01_shortcut.png)
&nbsp;
&nbsp;

**2. Select the path - hit "Folder" button**  
Beim ersten Start bittet dich Comfy Launcher, das Verzeichnis auszuwählen, das deine portable ComfyUI enthält. Wähle den Ordner, in dem sich `main.py` befindet – also das Root-Verzeichnis von ComfyUI.

![2](/README/screenshots/02-build%20folder.png)
&nbsp;
&nbsp;

**3. Select the folder**  
Das ist der Hauptordner von ComfyUI, der "main.py", "custom_nodes" usw. enthält.

![3](/README/screenshots/03-folder.png)
&nbsp;
&nbsp;

**4. Click OK to confirm**  

![4](/README/screenshots/04-hit%20ok.png)
&nbsp;
&nbsp;

**5. Preloader**  
ComfyUI-Ladebildschirm. Standardmäßig ist das CMD-Fenster deaktiviert und erscheint beim Start nicht. Wenn du es aktivierst, wird das Terminal-Fenster вместе mit dem Preloader angezeigt.

![5](/README/screenshots/05-preloader.png)
&nbsp;
&nbsp;

**6. Main UI**  
Das Hauptfenster der Anwendung. Alle Controls befinden sich in der oberen Leiste. Das Fenster ist rahmenlos, sodass der стандартmäßige Windows-Rand den visuellen Stil nicht stört.

![6](/README/screenshots/06-main%20window%20alt.png)
&nbsp;
&nbsp;

**7. Left panel**  
- App-Icon und Name
- **Settings** – öffnet die Comfy-Launcher-Einstellungen
- **Open ComfyUI folder** – öffnet das Hauptverzeichnis von ComfyUI (wo "main.py", "custom_nodes", "models" usw. liegen)
- **Open Output folder** – öffnet den "Output"-Ordner mit generierten Inhalten
- **Refresh UI** – aktualisiert die ComfyUI-Oberfläche

![7](/README/screenshots/07-left%20corner.png)
&nbsp;
&nbsp;

**8. Right panel**  
- **Status** – Serverzustandsanzeige (Online, Offline, Restarting)
- **Console** – öffnet die integrierte Konsole mit CMD-Output (erscheint nur, wenn CMD in den Einstellungen deaktiviert ist)
- **Restart ComfyUI** – startet den Server neu. Wenn der Server gestoppt ist (Offline), funktioniert dieser Button als **Start** und запуска ihn. Ich habe bewusst keine zwei separaten Buttons gemacht und beide Verhaltensweisen in einem implementiert.
- **Stop ComfyUI** – stoppt den Server vollständig
- Fenstersteuerung

![8](/README/screenshots/08-right%20corner.png)
&nbsp;
&nbsp;

**9. Settings / Comfy Folder**  
Comfy Folder – hier legst du den Pfad zu deinem aktiven ComfyUI-Build fest. Das gleiche Setup erscheint beim ersten Start.  
Unten gibt es einen Button, der zur offiziellen Website führt, wo du verschiedene Versionen herunterladen kannst.

![9](/README/screenshots/09-comfy%20folder.png)
&nbsp;
&nbsp;

**10. Settings / CMD Window**    
CMD Window – konfiguriere, ob das Terminal-Fenster angezeigt wird, wenn ComfyUI startet.

![10](/README/screenshots/10-cmd.png)
&nbsp;
&nbsp;

**11. Settings / Exit Options**  
Exit Options – beim Schließen von Comfy Launcher fragt die App, ob du den ComfyUI-Server stoppen möchtest. In diesem Tab kannst du den Dialog deaktivieren und eine automatische Aktion wählen:
- **Always stop server** – stoppt sowohl Comfy Launcher als auch ComfyUI vollständig
- **Never stop server** – schließt Comfy Launcher, lässt den ComfyUI-Server aber im Hintergrund weiterlaufen

![11](/README/screenshots/11-exit.png)
&nbsp;
&nbsp;

**12. Settings / Color Themes**  
Color Themes – passe das Erscheinungsbild von Comfy Launcher an. Enthält 4 встроенные Themes und unterstützt ComfyUI-Themes.
- **Select** – Theme im JSON-Format auswählen
- **Download** – Themes von "www.comfyui-themes.com" herunterladen

![12](/README/screenshots/12-themes.png)
&nbsp;
&nbsp;

**13. Different theme examples**  

![13](/README/screenshots/13-themes.png)
&nbsp;
&nbsp;

**14. Settings / Launcher Logs**  
Launcher Logs – zeigt das Action-Log des Launchers, hauptsächlich fürs Debugging.

![14](/README/screenshots/14-logs.png)
&nbsp;
&nbsp;

**15. Settings / About**  
About – kurze Infos über die App, über mich und Kontaktlinks.

![15](/README/screenshots/15-about.png)
&nbsp;
&nbsp;

## 🥁 Fehlerbehebung

Unser kleines Team hat sein Bestes gegeben, die App gründlich zu testen, auftretende Probleme zu finden und zu beheben. Da jedoch alle unterschiedliche Systeme und Workflows haben, können bei manchen Nutzer*innen trotzdem noch Bugs auftreten.

Wenn etwas kaputtgeht, kannst du mich auf [Discord kontaktieren](https://discord.com/invite/6nvXwXp78u). Das ist der schnellste Weg, ein Problem zu melden. Wenn du also auf einen Bug stößt, würde ich mich sehr freuen, wenn du mir Bescheid gibst!

- In der aktuellen Version von Comfy Launcher ist die manuelle Auswahl des `python-embedded`-Verzeichnisses (wird für ComfyUI benötigt) noch nicht implementiert. Die App geht davon aus, dass `python-embedded` sich am Standardort befindet — direkt neben dem Haupt-ComfyUI-Ordner.  
&nbsp;

- Leider wird aufgrund der Besonderheiten einer rahmenlosen UI das Ändern der Fenstergröße noch nicht unterstützt, поэтому läuft die App im Vollbildmodus. Du kannst das Fenster ziehen, aber aktuell nicht skalieren. Windows „Snap“ (Andocken an Bildschirmränder) funktioniert momentan auch nicht. Ich werde in Zukunft nach einer Lösung suchen — und wenn du weißt, wie man das umsetzt, freue ich mich, wenn du es teilst!

- Wenn nach dem Start von ComfyLauncher anstelle von ComfyUI ein weißer Bildschirm angezeigt wird, ist die WebView2-Runtime höchstwahrscheinlich auf Ihrem System nicht vorhanden oder beschädigt. Laden Sie in diesem Fall den [Evergreen Bootstrapper](https://developer.microsoft.com/en-us/microsoft-edge/webview2) von der offiziellen Microsoft-Website herunter und installieren oder deinstallieren Sie ihn.

    Wir sind bei Tests unter Windows 10 22H2 auf dieses Problem gestoßen. Die WebView2-Runtime war zwar installiert, aber aus unbekannten Gründen defekt, vermutlich nach der Verwendung eines Systemoptimierungsprogramms. Das Problem ließ sich durch Entfernen der fehlerhaften Runtime und Neuinstallation beheben. 
&nbsp;
&nbsp;

## 🎯 Fahrplan

- [ ] Portierung auf Linux
- [ ] Portierung auf macOS
- [ ] Automatische Updates für Comfy Launcher
- [ ] Tastenkürzel für Launcher-Aktionen
- [ ] Mehrsprachige Unterstützung
- [ ] Startmenü zur Build-Auswahl (damit du einen bestimmten ComfyUI-Build aus einer Liste starten kannst)
- [ ] Einstellung für den `python-embedded`-Pfad hinzufügen, um unterschiedliche Python-Versionen für denselben ComfyUI-Build auswählen zu können
- [ ] Geplant: Unterstützung für den Start der Standalone-Version
- [ ] Update-Checks für ComfyUI und Möglichkeit, ComfyUI zu aktualisieren
- [ ] Custom User Theme — UI-Farben manuell setzen
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
