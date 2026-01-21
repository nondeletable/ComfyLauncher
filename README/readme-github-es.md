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


## 😎 Sobre ComfyLauncher

ComfyLauncher es una herramienta para ejecutar versiones portables de ComfyUI de forma cómoda, rápida y “ligera”.

La versión standalone de Comfy viene con su propio launcher, lo cual hace que sea muy cómodo de usar. Por eso quise crear una experiencia de inicio similar para la versión portable, en lugar de que se abra en el navegador predeterminado.

Yo uso diferentes builds de ComfyUI para distintas tareas: uno específico para trabajar con WAN, otro para probar funciones nuevas, un tercero para generar imágenes, etc. Al mismo tiempo, no quiero depender de un único build “universal” para todo, para evitar posibles conflictos. Creo que mucha gente, especialmente quienes trabajan en producción, reconocerá este enfoque: lo “universal” no siempre es estable o fiable. Por eso decidí mantener builds portables separados para cada tipo de tarea.

Lo que no me gustaba es que ComfyUI Portable siempre se abre en el navegador predeterminado. Mi navegador es bastante pesado, con muchas pestañas, y yo quería usar un navegador limpio separado solo para Comfy. Pero incluso así, cuando arranca el servidor de Comfy, igualmente lanza el navegador predeterminado. Claro, no es un problema enorme, pero añade pasos extra… y se nota aún más cuando cada megabyte de RAM cuenta.

Así que decidí crear un launcher dedicado que sea práctico para el uso real. A continuación describo las funciones clave y las ideas principales detrás de la app.
&nbsp;
&nbsp;

## 🎨 Funciones

- **Un launcher ligero y dedicado.**  
    Usa poca RAM, lo cual es importante para equipos de gama media o cargas de trabajo que consumen muchos recursos. No incluye el “peso” extra típico de un navegador estándar, así que arranca rápido.  
&nbsp;
 
- **Opción de mostrar u ocultar la ventana CMD.**  
    Si te molesta que una ventana de terminal corra en segundo plano y ensucie tu barra de tareas, puedes ocultarla.  
&nbsp;
 
- **Consola integrada.**  
    Cuando la ventana CMD está desactivada, el launcher envía la misma salida a una consola UI dedicada (el botón de consola aparece automáticamente). Así puedes ocultar el terminal sin perder el monitoreo detallado.  
&nbsp;
 
- **Controles de acceso rápido y acciones comunes del servidor.**  
    - Abrir el directorio **Output** y el directorio **ComfyUI**
    - **Refresh UI**
    - **Restart** - iniciar y reiniciar el servidor
    - **Stop** - detener el servidor por completo  
&nbsp;
 
- **Soporte para los temas predeterminados de ComfyUI** para mantener la interfaz consistente.
- **Indicador de estado del servidor** - Online, Offline, Restarting.
- **Y más.**
&nbsp;
&nbsp;

## ⚒ Instalación

- Ve a la sección **Releases** y descarga la última versión.
- Extrae (unzip) el archivo en una carpeta de tu elección.
- Ejecuta el ".exe" ¡y listo!
&nbsp;
&nbsp;

## 🏓 Cómo usarlo

**1. Inicia con el exe**  
Después de la instalación, puedes iniciar Comfy Launcher usando el ".exe". También puedes crear un acceso directo en el escritorio o en la barra de tareas para acceder más rápido.

![1](/README/screenshots/01_shortcut.png)
&nbsp;
&nbsp;

**2. Selecciona la ruta - pulsa el botón "Folder"**  
En el primer inicio, Comfy Launcher te pedirá que selecciones el directorio que contiene tu ComfyUI portable. Elige la carpeta donde está `main.py`, es decir, el directorio raíz de ComfyUI.

![2](/README/screenshots/02-build%20folder.png)
&nbsp;
&nbsp;

**3. Selecciona la carpeta**  
Esta es la carpeta principal de ComfyUI que contiene "main.py", "custom_nodes", etc.

![3](/README/screenshots/03-folder.png)
&nbsp;
&nbsp;

**4. Haz clic en OK para confirmar**  

![4](/README/screenshots/04-hit%20ok.png)
&nbsp;
&nbsp;

**5. Preloader**  
Pantalla de carga de ComfyUI. Por defecto, la ventana CMD está desactivada y no aparecerá durante el inicio. Si la activas, la ventana del terminal aparecerá junto con el preloader.

![5](/README/screenshots/05-preloader.png)
&nbsp;
&nbsp;

**6. Interfaz principal**  
La ventana principal de la aplicación. Todos los controles están en la barra superior. La ventana no tiene marco, así que el borde estándar de Windows no interfiere con el estilo visual general.

![6](/README/screenshots/06-main%20window%20alt.png)
&nbsp;
&nbsp;

**7. Panel izquierdo**  
- Icono y nombre de la app
- **Settings** - abre la configuración de Comfy Launcher
- **Open ComfyUI folder** - abre el directorio principal de ComfyUI (donde están "main.py", "custom_nodes", "models", etc.)
- **Open Output folder** - abre la carpeta "Output" que contiene el contenido generado
- **Refresh UI** - actualiza la interfaz de ComfyUI

![7](/README/screenshots/07-left%20corner.png)
&nbsp;
&nbsp;

**8. Panel derecho**  
- **Status** - indicador del estado del servidor (Online, Offline, Restarting)
- **Console** - abre la consola integrada con la salida de CMD (solo aparece cuando CMD está desactivado en settings)
- **Restart ComfyUI** - reinicia el servidor. Si el servidor está detenido (Offline), este botón actúa como **Start** y lo inicia. Decidí no separarlo en dos botones distintos e implementé ambos comportamientos en uno.
- **Stop ComfyUI** - detiene el servidor por completo
- Controles de ventana

![8](/README/screenshots/08-right%20corner.png)
&nbsp;
&nbsp;

**9. Settings / Comfy Folder**  
Comfy Folder - te permite establecer la ruta de tu build activo de ComfyUI. La misma configuración aparece en el primer inicio.  
Abajo hay un botón que enlaza al sitio oficial, donde puedes descargar diferentes versiones.

![9](/README/screenshots/09-comfy%20folder.png)
&nbsp;
&nbsp;

**10. Settings / CMD Window**    
CMD Window - configura si se muestra la ventana del terminal cuando inicia ComfyUI.

![10](/README/screenshots/10-cmd.png)
&nbsp;
&nbsp;

**11. Settings / Exit Options**  
Exit Options - al cerrar Comfy Launcher, la app pregunta si quieres detener el servidor de ComfyUI. En esta pestaña puedes desactivar ese diálogo y elegir una acción automática:
- **Always stop server** - detiene por completo tanto Comfy Launcher como ComfyUI
- **Never stop server** - cierra Comfy Launcher, pero mantiene el servidor de ComfyUI funcionando en segundo plano

![11](/README/screenshots/11-exit.png)
&nbsp;
&nbsp;

**12. Settings / Color Themes**  
Color Themes - personaliza la apariencia de Comfy Launcher. Incluye 4 temas integrados y soporte para temas de ComfyUI.
- **Select** - elige un tema en formato JSON
- **Download** - descarga temas desde "www.comfyui-themes.com"

![12](/README/screenshots/12-themes.png)
&nbsp;
&nbsp;

**13. Ejemplos de temas diferentes**  

![13](/README/screenshots/13-themes.png)
&nbsp;
&nbsp;

**14. Settings / Launcher Logs**  
Launcher Logs - muestra el registro de acciones del launcher, principalmente para depuración.

![14](/README/screenshots/14-logs.png)
&nbsp;
&nbsp;

**15. Settings / About**  
About - información breve sobre la app, sobre mí y enlaces de contacto.

![15](/README/screenshots/15-about.png)
&nbsp;
&nbsp;

## 🥁 Solución de problemas

Nuestro pequeño equipo hizo todo lo posible por probar la app a fondo, detectar los problemas que aparecieron durante el uso y corregirlos. Sin embargo, como los sistemas y los flujos de trabajo de cada persona son distintos, puede que todavía aparezcan algunos bugs para ciertos usuarios.

Si algo se rompe, puedes contactarme en [Discord](https://discord.com/invite/6nvXwXp78u). Es la forma más rápida de reportar un problema. Así que si te encuentras con un bug, ¡te agradecería mucho que me lo hicieras saber!

- En la versión actual de Comfy Launcher, la selección manual del directorio `python-embedded` (necesario para ComfyUI) aún no está implementada. La app asume que `python-embedded` está en la ubicación predeterminada — junto a la carpeta principal de ComfyUI.  
&nbsp;
 
- Lamentablemente, debido a las particularidades de una UI sin marco, el cambio de tamaño de la ventana todavía no está soportado, así que la app se ejecuta en modo pantalla completa. Puedes mover la ventana, pero por ahora no puedes redimensionarla. El “snap” de Windows (acoplar a los bordes de la pantalla) tampoco funciona en este momento. Buscaré una solución en el futuro — y si sabes cómo implementarlo, ¡me encantaría que lo compartieras!
&nbsp;
&nbsp;

## 🎯 Hoja de ruta

- [ ] Portar a Linux
- [ ] Portar a macOS
- [ ] Actualizaciones automáticas para Comfy Launcher
- [ ] Atajos de teclado para acciones del launcher
- [ ] Soporte multilenguaje
- [ ] Menú de inicio para selección de builds (para poder lanzar un build específico de ComfyUI desde una lista)
- [ ] Añadir un ajuste para la ruta de `python-embedded` para poder seleccionar distintas versiones de Python para el mismo build de ComfyUI
- [ ] Planificado: soporte para ejecutar la versión Standalone
- [ ] Comprobación de actualizaciones de ComfyUI y posibilidad de actualizar ComfyUI
- [ ] Custom User Theme — configurar colores de la UI manualmente
- [ ] Mejoras cosméticas
&nbsp;
&nbsp;

## 💾 Tecnologías

- **Python 3.11+**
- **PyQt6** - para UI de escritorio
- **Subprocess** - para gestionar la ejecución de ComfyUI
- **JSON** - para almacenar preferencias del usuario
- **PyInstaller** - para generar releases ".exe"
&nbsp;
&nbsp;

## ☎ Contacto

Si te gustaría colaborar o hablar sobre una oportunidad de trabajo, usa cualquiera de los contactos de abajo.
Para soporte/bugs, por favor usa Discord o GitHub Issues. Normalmente respondo en 24 horas.

- 🐙 **GitHub** - página (documentación, releases, código fuente)  
  https://github.com/nondeletable

- 💬 **Discord** - noticias, soporte, preguntas y reportes de bugs  
  https://discord.com/invite/6nvXwXp78u

- ✈️ **Telegram** - mensajes directos  
  https://t.me/nondeletable

- 📧 **Email** - para consultas formales o comerciales  
  nondeletable@gmail.com

- 💼 **LinkedIn** - perfil profesional  
  https://www.linkedin.com/in/aleksandra-gicheva-3b0264341/

- ☕ **Boosty** - apoya mi trabajo y proyectos con donaciones  
  https://boosty.to/codebird/donate
&nbsp;
&nbsp;

¡Gracias por usar ComfyLauncher! He puesto mucho trabajo en él, y espero que haga tu flujo de trabajo más fácil y rápido 🙂

