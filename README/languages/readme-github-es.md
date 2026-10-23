<div align="center">
  <a href="https://github.com/nondeletable/ComfyLauncher">
    <img src="/README/icon/256-main.png" alt="Logo" width="100" height="100">
  </a>
<h2>ComfyLauncher</h2>
Navegador inteligente, rápido y ligero para ComfyUI.
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


## 😎 Sobre ComfyLauncher

ComfyLauncher es una herramienta para ejecutar versiones portables de ComfyUI de forma cómoda, rápida y “ligera”.

La versión standalone de Comfy viene con su propio launcher, lo cual hace que sea muy cómodo de usar. Por eso quise crear una experiencia de inicio similar para la versión portable, en lugar de que se abra en el navegador predeterminado.

Yo uso diferentes builds de ComfyUI para distintas tareas: uno específico para trabajar con WAN, otro para probar funciones nuevas, un tercero para generar imágenes, etc. Al mismo tiempo, no quiero depender de un único build “universal” para todo, para evitar posibles conflictos. Creo que mucha gente, especialmente quienes trabajan en producción, reconocerá este enfoque: lo “universal” no siempre es estable o fiable. Por eso decidí mantener builds portables separados para cada tipo de tarea.

Lo que no me gustaba es que ComfyUI Portable siempre se abre en el navegador predeterminado. Mi navegador es bastante pesado, con muchas pestañas, y yo quería usar un navegador limpio separado solo para Comfy. Pero incluso así, cuando arranca el servidor de Comfy, igualmente lanza el navegador predeterminado. Claro, no es un problema enorme, pero añade pasos extra… y se nota aún más cuando cada megabyte de RAM cuenta.

Así que decidí crear un launcher dedicado que sea práctico para el uso real. A continuación describo las funciones clave y las ideas principales detrás de la app.
&nbsp;
&nbsp;

## 🎨 Funciones

- **Gestor de arranque multi-instancia.**  
  Añade y gestiona múltiples builds portables de ComfyUI para iniciarlos con un solo clic.  
  Personaliza cada instancia con sus propios flags de lanzamiento, nombre visible e icono.

&nbsp;

- **Navegador ligero dedicado.**  
  Usa poca RAM, algo importante para equipos de gama media o cargas de trabajo exigentes.  
  No incluye el sobrecoste típico de un navegador estándar, por lo que inicia rápidamente.  
  30 % menos uso de RAM que Chrome estándar (en reposo), probado en Windows 10 y Windows 11.

&nbsp;

- **Opción para mostrar u ocultar la ventana CMD.**  
  Si te molesta que la terminal se ejecute en segundo plano y ocupe espacio en la barra de tareas, puedes ocultarla.

&nbsp;

- **Consola integrada.**  
  Cuando la ventana CMD está desactivada, el launcher muestra la misma salida en una consola integrada en la interfaz (el botón aparece automáticamente).  
  Así puedes ocultar el terminal sin perder el monitoreo detallado.

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
- Instale la aplicación en la carpeta que elija.
- Ejecuta el ".exe" ¡y listo!
- Asegúrese de tener instalado Microsoft WebView2 Runtime. De lo contrario, descargue e instale [Evergreen Bootstrapper](https://developer.microsoft.com/en-us/microsoft-edge/webview2).
&nbsp;
&nbsp;

## 🏓 Cómo usarlo

Puedes explorar las funciones del programa, la interfaz y las instrucciones a través de este  
[enlace](https://github.com/nondeletable/ComfyLauncher/blob/master/README/user_manual/user_manual_es.md).

&nbsp;
&nbsp;


## 🎯 Hoja de ruta

- [x] Menú de inicio para selección de builds (lanzar un build específico de ComfyUI desde una lista)
- [x] Soporte de flags para cada build
- [ ] Portar a Linux
- [ ] Portar a macOS
- [ ] Actualizaciones automáticas para ComfyLauncher
- [ ] Atajos de teclado para acciones del launcher
- [ ] Soporte multilenguaje
- [ ] Añadir un ajuste para la ruta de `python-embedded` que permita seleccionar distintas versiones de Python para el mismo build de ComfyUI
- [ ] Posible soporte para ejecutar la versión Standalone
- [ ] Comprobación de actualizaciones de ComfyUI y posibilidad de actualizar ComfyUI
- [ ] Tema de usuario personalizado — configurar manualmente los colores de la interfaz
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

