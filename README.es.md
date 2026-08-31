<p align="center">
  <img src="assets/banner.png" alt="Synapse Agent" width="100%">
</p>

# Synapse Agent ☤
<p align="center">
  <b>Synapse Agent</b> | <b>Synapse Desktop</b>
</p>
<p align="center">
  <a href="https://github.com/johsua092-ui/synapse-ai-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/Lang-English-blue?style=for-the-badge" alt="English"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/Lang-中文-red?style=for-the-badge" alt="中文"></a>
  <a href="README.ur-pk.md"><img src="https://img.shields.io/badge/Lang-اردو-green?style=for-the-badge" alt="اردو"></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/Lang-Español-orange?style=for-the-badge" alt="Español"></a>
  <a href="README.ja.md"><img src="https://img.shields.io/badge/Lang-日本語-white?style=for-the-badge" alt="日本語"></a>
  <a href="README.ar.md"><img src="https://img.shields.io/badge/Lang-العربية-blue?style=for-the-badge" alt="العربية"></a>
  <a href="README.id.md"><img src="https://img.shields.io/badge/Lang-Bahasa%20Indonesia-black?style=for-the-badge" alt="Bahasa Indonesia"></a>
  <a href="README.jv.md"><img src="https://img.shields.io/badge/Lang-Basa%20Jawa-yellow?style=for-the-badge" alt="Basa Jawa"></a>
</p>

**El agente de IA que se auto-mejora, construido por Josh Research.** Es el único agente con un bucle de aprendizaje integrado: crea habilidades a partir de la experiencia, las mejora durante su uso, se impulsa a sí mismo a persistir el conocimiento, busca en sus propias conversaciones pasadas y construye un modelo cada vez más profundo de quién eres a lo largo de las sesiones. Ejecútalo en un VPS de $5, un clúster GPU o infraestructura serverless que cuesta casi nada en reposo. No está atado a tu portátil: háblale desde Telegram mientras trabaja en una VM en la nube.

Usa el modelo que quieras — OpenRouter, OpenAI, tu propio endpoint y muchos otros proveedores. Cambia con `synapse model` — sin cambios de código, sin bloqueo.

<table>
<tr><td><b>Una interfaz de terminal real</b></td><td>TUI completa con edición multilínea, autocompletado de comandos con barra inclinada, historial de conversaciones, interrupción y redirección, y salida de herramientas en streaming.</td></tr>
<tr><td><b>Vive donde tú</b></td><td>Telegram, Discord, Slack, WhatsApp, Signal y CLI — todo desde un único proceso de puerta de enlace. Transcripción de notas de voz, continuidad de conversaciones entre plataformas.</td></tr>
<tr><td><b>Un bucle de aprendizaje cerrado</b></td><td>Memoria curada por el agente con impulsos periódicos. Creación autónoma de habilidades después de tareas complejas. Las habilidades se auto-mejoran durante su uso. Búsqueda FTS5 en sesiones con resumen por LLM para recuerdo entre sesiones. Modelado dialéctico del usuario con <a href="https://github.com/plastic-labs/honcho">Honcho</a>. Compatible con el estándar abierto <a href="https://agentskills.io">agentskills.io</a>.</td></tr>
<tr><td><b>Automatizaciones programadas</b></td><td>Programador cron integrado con entrega en cualquier plataforma. Informes diarios, copias de seguridad nocturnas, auditorías semanales — todo en lenguaje natural, ejecutándose sin supervisión.</td></tr>
<tr><td><b>Delega y paraleliza</b></td><td>Lanza subagentes aislados para flujos de trabajo paralelos. Escribe scripts de Python que llaman herramientas vía RPC, colapsando pipelines de múltiples pasos en turnos de costo cero de contexto.</td></tr>
<tr><td><b>Se ejecuta en cualquier lugar, no solo en tu portátil</b></td><td>Siete backends de terminal — local, Docker, SSH, Singularity, Modal, Daytona y Vercel Sandbox. Daytona y Modal ofrecen persistencia serverless: el entorno de tu agente se hiberna cuando está inactivo y se activa bajo demanda, costando casi nada entre sesiones. Ejecútalo en un VPS de $5 o un clúster GPU.</td></tr>
<tr><td><b>Listo para investigación</b></td><td>Generación por lotes de trayectorias, compresión de trayectorias para entrenar la próxima generación de modelos de llamada a herramientas.</td></tr>
</table>

---

## Instalación rápida

### npm (todas las plataformas)

```bash
npx synapse-ai-agent
```

Descarga y ejecuta el instalador oficial para tu sistema operativo — no se necesita conocimiento de Node, el shim solo lo inicializa.

### Linux, macOS, WSL2, Termux

```bash
curl -fsSL https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.sh | bash
```

### Windows (nativo, PowerShell)

> **Aviso:** Windows nativo ejecuta Synapse sin WSL — la CLI, la puerta de enlace, la TUI y las herramientas funcionan nativamente. Si prefieres usar WSL2, el comando de Linux/macOS de arriba también funciona allí. ¿Encontraste un bug? Por favor [reporta issues](https://github.com/johsua092-ui/synapse-ai-agent/issues).

Ejecuta esto en PowerShell:

```powershell
iex (irm https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.ps1)
```

El instalador se encarga de todo: uv, Python 3.11, Node.js, ripgrep, ffmpeg, **y un Git Bash portable** (MinGit, desempaquetado en `%LOCALAPPDATA%\synapse\git` — sin necesidad de administrador, completamente aislado de cualquier instalación de Git del sistema). Synapse usa este Git Bash empaquetado para ejecutar comandos de shell.

Si ya tienes Git instalado, el instalador lo detecta y lo usa en su lugar. De lo contrario, solo necesitas una descarga de MinGit de ~45MB — no tocará ni interferirá con ningún Git del sistema.

> **Android / Termux:** La ruta manual documentada está en la guía de Termux. En Termux, Synapse instala un extra `.[termux]` seleccionado porque el extra completo `.[all]` actualmente incluye dependencias de voz incompatibles con Android.
>
> **Windows:** Windows nativo es completamente compatible — el comando de PowerShell de arriba instala todo. Si prefieres usar WSL2, el comando de Linux también funciona allí. La instalación nativa de Windows se ubica en `%LOCALAPPDATA%\synapse`; las instalaciones en WSL2 van en `~/.synapse` como en Linux.

Después de la instalación:

```bash
source ~/.bashrc    # recargar shell (o: source ~/.zshrc)
synapse              # ¡empieza a conversar!
```

### Solución de problemas

#### Windows Defender o antivirus marca `uv.exe` como malware

Si tu antivirus (Bitdefender, Windows Defender, etc.) pone en cuarentena `uv.exe` de la carpeta `bin` de Synapse (`%LOCALAPPDATA%\synapse\bin\uv.exe`), esto es un **falso positivo**. El archivo es `uv` de Astral — el gestor de paquetes de Python en Rust que Synapse empaqueta para gestionar su entorno Python. Los motores antivirus basados en ML frecuentemente marcan binarios sin firmar de Rust que descargan e instalan paquetes.

**Para verificar que tu copia es auténtica:**

```powershell
# Instalar GitHub CLI si es necesario
winget install --id GitHub.cli

# Iniciar sesión en GitHub
gh auth login

# Ejecutar verificación
$uv = "$env:LOCALAPPDATA\synapse\bin\uv.exe"
$ver = (& $uv --version).Split(' ')[1]
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$zip = "$env:TEMP\uv.zip"
Invoke-WebRequest "https://github.com/astral-sh/uv/releases/download/$ver/uv-x86_64-pc-windows-msvc.zip" -OutFile $zip -UseBasicParsing
gh attestation verify $zip --repo astral-sh/uv
Expand-Archive $zip "$env:TEMP\uv_x" -Force
(Get-FileHash "$env:TEMP\uv_x\uv.exe").Hash -eq (Get-FileHash $uv).Hash
```

Si la attestación dice "Verification succeeded" y la última línea imprime `True`, todo está bien.

**Para agregar Synapse a la lista blanca:**
- **Windows Defender:** Ejecuta PowerShell como Administrador → `Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\synapse\bin"`
- **Bitdefender:** Agrega una excepción en la consola de Bitdefender (Protección > Antivirus > Configuración > Gestionar excepciones)
- Agrega a la lista blanca la **carpeta**, no el hash del archivo — Synapse actualiza `uv` y el hash cambia con cada versión

Para más contexto, consulta los reportes de Astral: [astral-sh/uv#13553](https://github.com/astral-sh/uv/issues/13553), [astral-sh/uv#15011](https://github.com/astral-sh/uv/issues/15011), [astral-sh/uv#10079](https://github.com/astral-sh/uv/issues/10079).

---

## Desplegar en Railway

Despliega Synapse Agent en [Railway](https://railway.app) como un servicio de contenedor con un clic. La imagen ya viene con un punto de entrada s6-overlay y un panel web supervisado.

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/template/synapse-agent?referralCode=QXdhdr)

### Lo que obtienes

- **Panel web** en una URL pública de Railway (con autenticación, ver más abajo)
- **Volumen persistente** para el estado del agente (monta un volumen en `/opt/data` / `$SYNAPSE_HOME`)
- **Verificación de salud** conectada a `/api/health`

### Configuración

1. Haz clic en **Deploy on Railway** arriba (o crea un nuevo servicio desde este repo — Railway detecta automáticamente `railway.toml` + `Dockerfile`).
2. Adjunta un volumen montado en `/opt/data`.
3. Agrega las variables de servicio requeridas (consulta [.env.railway.example](.env.railway.example)). Como mínimo:
   - `SYNAPSE_DASHBOARD=1`
   - Un proveedor de autenticación — **Basic Auth** (`SYNAPSE_DASHBOARD_BASIC_AUTH_USERNAME` + `SYNAPSE_DASHBOARD_BASIC_AUTH_PASSWORD`) u OAuth/OIDC. Sin uno de estos, el panel **falla al cerrar** en el enlace público.
4. Agrega las claves API de tu modelo/proveedor (`OPENROUTER_API_KEY`, `OPENAI_API_KEY`, etc.).

### Docker (autoalojado)

```bash
SYNAPSE_UID=$(id -u) SYNAPSE_GID=$(id -g) docker compose up -d
```

Consulta `docker-compose.yml` y el directorio `docker/` para la configuración supervisada completa. Una variante de compose para Windows está en `docker-compose.windows.yml`.

---

## Primeros pasos

```bash
synapse              # CLI interactiva — inicia una conversación
synapse model        # Elige tu proveedor de LLM y modelo
synapse dashboard    # Abre el panel de administración en tu navegador (puerto 9119)
synapse tools        # Configura qué herramientas están habilitadas
synapse config set   # Establece valores de configuración individuales
synapse config get   # Imprime valores de configuración individuales
synapse gateway      # Inicia la puerta de enlace de mensajería (Telegram, Discord, etc.)
synapse setup        # Ejecuta el asistente de configuración completo (configura todo de una vez)
synapse claw migrate # Migra desde OpenClaw (si vienes de OpenClaw)
synapse update       # Actualiza a la última versión
synapse doctor       # Diagnosticar cualquier problema
```

### Panel de administración

El comando `synapse dashboard` inicia un panel de administración web local en `http://127.0.0.1:9119`. Proporciona una interfaz basada en navegador para configurar proveedores, gestionar canales, ver registros y monitorear tu agente.

```bash
synapse dashboard                        # Abrir en navegador, puerto 9119
synapse dashboard --port 8080            # Puerto personalizado
synapse dashboard --host 0.0.0.0         # Vincular a todas las interfaces (para acceso remoto)
synapse dashboard --no-open              # No abrir navegador automáticamente
synapse dashboard --skip-build           # Saltar compilación de React, usar HTML pre-compilado del admin
```

Características:
- **Configuración** — Configurar proveedores de LLM, claves API y canales de mensajería
- **Estado** — Monitorear el estado de la puerta de enlace, tiempo de actividad y sesiones activas
- **Registros** — Ver registros del agente en tiempo real
- **Usuarios** — Gestionar solicitudes de emparejamiento y usuarios aprobados
- **Copia de seguridad y restauración** — Descargar/cargar instantáneas de despliegue

📖 **La documentación completa se encuentra en la sección de documentación más abajo.**

---

## Gestión de sesiones

Synapse mantiene un historial de conversaciones para cada sesión. El comando `synapse session` te permite listar y eliminar sesiones desde la CLI, y `/delete` lo hace desde dentro de una conversación. Reutiliza el mismo backend SessionDB que el panel, por lo que hay una única implementación de eliminación en la CLI, el panel y las plataformas de chat.

```bash
synapse session list                    # Listar todas las sesiones persistidas
synapse session delete <session-id>     # Eliminar permanentemente una sesión
synapse session delete --all            # Eliminar todas las sesiones (advirtiendo primero)
synapse session delete <session-id> -y  # Saltar la confirmación
synapse session --help                  # Uso completo
```

`delete` siempre verifica que la sesión exista e imprime un error si no la encuentra. Las eliminaciones individuales muestran la información de la sesión y piden confirmación antes de realizar cualquier acción destructiva; `delete --all` requiere una confirmación aún más estricta (o `--yes`).

Dentro de una conversación, `/delete` (o `/delete -y`) elimina permanentemente la sesión activa actual e inicia una nueva.

La página de Sesiones del panel ofrece las mismas operaciones con un botón de eliminar, diálogo de confirmación, actualización después de la eliminación y estados de error/vacío — respaldados por el mismo SessionDB.

## Habilidades empaquetadas

Synapse incluye un conjunto de habilidades empaquetadas que se sincronizan en `~/.synapse/skills/` al instalar y actualizar (ver `tools/skills_sync.py`). También incluye las habilidades de flujo de trabajo de desarrollo [Superpowers](https://github.com/obra/superpowers) bajo `skills/superpowers/` — incluyendo `brainstorming`, `writing-plans`, `executing-plans`, `systematic-debugging` (a través del bundle existente de software-development), `test-driven-development`, y más. Comparten la misma sincronización de habilidades empaquetadas, por lo que están disponibles automáticamente en cualquier perfil nuevo.

Para las habilidades que comparten nombre con una habilidad empaquetada existente (por ejemplo `systematic-debugging`, `test-driven-development`, `requesting-code-review`), Synapse mantiene la copia empaquetada existente — esto evita una colisión de nombres duplicados en el manifiesto de sincronización.

---

## Agnóstico de proveedores por diseño

Synapse funciona con el proveedor que quieras — eso no va a cambiar. Trae cualquier endpoint de OpenRouter, OpenAI o personalizado y conéctalo una vez. Cambia con `synapse model` — sin cambios de código, sin bloqueo.

Todavía puedes traer tus propias claves por herramienta cuando quieras — la puerta de enlace es por backend, no todo o nada.

---

## Razonamiento y pensamiento

Synapse mantiene el razonamiento/pensamiento habilitado por defecto y nunca permite que un valor de configuración lo desactive. Esta es la política de **razonamiento siempre activo**: los modelos que admiten tokens de razonamiento siempre los usan; los que no lo admiten no se ven afectados (no se envían parámetros ilegales al proveedor).

### Niveles de esfuerzo

Solo existen tres niveles de esfuerzo, mapeados de la escala anterior más amplia:

| Nivel  | Compromiso                                                       |
|--------|------------------------------------------------------------------|
| Medium | Velocidad y costo equilibrados (el predeterminado)               |
| High   | Razonamiento más profundo — más lento y costoso por turno        |
| Max    | Razonamiento más fuerte — el más lento y costoso por turno       |

### Establecer el nivel

- **CLI:** `/reasoning medium | high | max`
- **Panel:** el selector de Razonamiento en la barra lateral del chat (la misma clave de configuración `agent.reasoning_effort`)
- **Configuración:** `agent.reasoning_effort: medium` en `config.yaml`
- **Sobrescrituras por modelo:** `agent.reasoning_overrides: { "model-id": "high" }`

### Migración de desactivación heredada

Anteriormente `none`, `false`, `off`, `disabled`, un valor vacío, un booleano YAML `False`, o `--reasoning_disabled` desactivaban el pensamiento. Bajo la política de siempre activo, todos estos ahora se resuelven en **medium** (`{"enabled": true, "effort": "medium"}`) para que el razonamiento nunca se deshabilite silenciosamente. Un nivel no reconocido (por ejemplo `turbo`) sigue usando el valor predeterminado del llamador; el flag obsoleto `--reasoning_disabled` del ejecutor por lotes existe solo por compatibilidad retroactiva e imprime un aviso de obsolescencia.

---

## Referencia rápida: CLI vs Mensajería

Synapse tiene dos puntos de entrada: inicia la interfaz de terminal con `synapse`, o ejecuta la puerta de enlace y háblale desde Telegram, Discord, Slack, WhatsApp, Signal o Email. Una vez que estás en una conversación, muchos comandos con barra inclinada están compartidos entre ambas interfaces.

| Acción                         | CLI                                           | Plataformas de mensajería                                                           |
| Empezar a conversar            | `synapse`                                     | Ejecuta `synapse gateway setup` + `synapse gateway start`, luego envía un mensaje al bot |
| Abrir panel de administración  | `synapse dashboard`                           | —                                                                                   |
| Iniciar conversación nueva     | `/new` o `/reset`                             | `/new` o `/reset`                                                                   |
| Cambiar modelo                 | `/model [proveedor:modelo]`                   | `/model [proveedor:modelo]`                                                         |
| Establecer una personalidad    | `/personality [nombre]`                       | `/personality [nombre]`                                                             |
| Reintentar o deshacer el último turno | `/retry`, `/undo`                    | `/retry`, `/undo`                                                                   |
| Comprimir contexto / verificar uso | `/compress`, `/usage`, `/insights [--days N]` | `/compress`, `/usage`, `/insights [days]`                                         |
| Explorar habilidades           | `/skills` o `/<nombre-habilidad>`             | `/<nombre-habilidad>`                                                               |
| Listar sesiones                | `synapse session list`                        | —                                                                                   |
| Eliminar sesión actual         | `/delete`                                     | —                                                                                   |
| Eliminar una sesión / todas    | `synapse session delete <id>` / `--all`       | —                                                                                   |
| Interrumpir trabajo actual     | `Ctrl+C` o envía un nuevo mensaje             | `/stop` o envía un nuevo mensaje                                                    |
| Estado específico de plataforma | `/platforms`                                | `/status`, `/sethome`                                                               |

Para las listas completas de comandos, consulta la guía de CLI y la guía de la Puerta de Enlace de Mensajería.

---

## Migración desde OpenClaw

Si vienes de OpenClaw, Synapse puede importar automáticamente tu configuración, memorias, habilidades y claves API.

**Durante la primera configuración:** El asistente de configuración (`synapse setup`) detecta automáticamente `~/.openclaw` y ofrece migrar antes de que comience la configuración.

**En cualquier momento después de la instalación:**

```bash
synapse claw migrate              # Migración interactiva (preset completo)
synapse claw migrate --dry-run    # Vista previa de lo que se migraría
synapse claw migrate --preset user-data   # Migrar sin secretos
synapse claw migrate --overwrite  # Sobrescribir conflictos existentes
```

Qué se importa:

- **SOUL.md** — archivo de personalidad
- **Memorias** — entradas de MEMORY.md y USER.md
- **Habilidades** — habilidades creadas por el usuario → `~/.synapse/skills/openclaw-imports/`
- **Lista blanca de comandos** — patrones de aprobación
- **Configuración de mensajería** — configuraciones de plataforma, usuarios permitidos, directorio de trabajo
- **Claves API** — secretos en lista blanca (Telegram, OpenRouter, OpenAI, Anthropic, ElevenLabs)
- **Recursos TTS** — archivos de audio del espacio de trabajo
- **Instrucciones del espacio de trabajo** — AGENTS.md (con `--workspace-target`)

Consulta `synapse claw migrate --help` para todas las opciones, o usa la habilidad `openclaw-migration` para una migración interactiva guiada por el agente con vistas previas en modo de prueba.

---


## Google Drive

Synapse puede leer y escribir en Google Drive del usuario a través de una habilidad empaquetada (`skills/google-drive`). Usa la API REST de Drive con OAuth — sin el SDK pesado de Google, solo `requests` (ya es una dependencia central).

Configúralo una vez ejecutando el asistente empaquetado:

```bash
python3 skills/google-drive/google-drive/scripts/gdrive.py setup
```

El asistente guía al usuario a través de Google Cloud Console (habilitar la API de Drive, crear un cliente OAuth de escritorio, descargar `credentials.json`), luego abre un navegador para el consentimiento y almacena el token en caché localmente. Los archivos de credenciales (`credentials.json`, `token.json`) están ignorados por git y nunca se comprometen.

Entonces el agente puede manejar Drive en nombre del usuario:

```bash
python3 skills/google-drive/google-drive/scripts/gdrive.py list
python3 skills/google-drive/google-drive/scripts/gdrive.py search "annual report"
python3 skills/google-drive/google-drive/scripts/gdrive.py upload notes.md
python3 skills/google-drive/google-drive/scripts/gdrive.py download <file_id>
```

Las mismas credenciales funcionan en Windows, Termux, un VPS o Railway — copia `credentials.json` (y `token.json`) en el checkout y ejecuta `setup` de nuevo. Consulta `skills/google-drive/google-drive/SKILL.md` para todos los detalles.

---

## Contribuir

¡Agradecemos las contribuciones! Consulta la Guía de Contribuciones para la configuración de desarrollo, el estilo de código y el proceso de PR.

Inicio rápido para contribuyentes — usa el instalador estándar, luego trabaja desde el checkout completo de git que crea en `$SYNAPSE_HOME/synapse-agent` (generalmente `~/.synapse/synapse-agent`). Esto coincide con el diseño usado por `synapse update`, el entorno virtual administrado, las dependencias lazy, la puerta de enlace y las herramientas de documentación.

```bash
curl -fsSL https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.sh | bash
cd "${SYNAPSE_HOME:-$HOME/.synapse}/synapse-agent"
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

Alternativa de clonación manual (para clones desechables/CI donde intencionadamente no deseas el diseño de instalación administrado):

Crea el entorno virtual fuera del árbol de código fuente clonado — un entorno virtual dentro del directorio desde el que opera el agente puede ser borrado por un comando de ruta relativa que el agente ejecuta contra su propio checkout, destruyendo el entorno de ejecución en medio de una sesión.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv ~/.synapse/venvs/synapse-dev --python 3.11
source ~/.synapse/venvs/synapse-dev/bin/activate
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

---

## Licencia

MIT — ver [LICENSE](LICENSE).
