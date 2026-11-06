# Entorno de desarrollo en WSL2

Guía vigente desde el 6 de noviembre de 2026 (tarea T02 de la spec [multi-provider-orchestrator](../.kiro/specs/multi-provider-orchestrator/tasks.md)). Sustituye a [setup-windows.md](setup-windows.md) y [WINDOWS_WSL2.md](WINDOWS_WSL2.md), que describen la línea CAO retirada.

Deja listo el host principal (Windows 11 + WSL2 con Ubuntu 24.04) para desarrollar y verificar Nexus: Python 3.12, `uv`, ruff, Node LTS y las tres CLIs de agentes (Claude Code, Codex y Kiro CLI) con sesión iniciada. **Las instalaciones y los inicios de sesión los ejecutas tú**; ningún agente instala herramientas ni inicia sesión por su cuenta. Al terminar, registra las versiones observadas en [entorno-2026-11.md](entorno-2026-11.md).

Todos los comandos se ejecutan **dentro de la terminal de Ubuntu (WSL)**, no en PowerShell ni en CMD, salvo que se indique lo contrario.

## Reglas de seguridad durante la instalación

- No pegues en el chat, en issues ni en archivos del repositorio tokens, claves de API, códigos de dispositivo, URLs de inicio de sesión con parámetros ni el contenido de `~/.claude`, `~/.codex`, `~/.kiro` u otros directorios de credenciales.
- Si una salida muestra tu correo, organización o ruta personal, sustitúyelos por `<redactado>` antes de compartirla.
- `KIRO_API_KEY` (opcional) se define en tu perfil de shell, nunca en el repositorio ni en `.env` del proyecto. Nexus solo la pasa por nombre al proceso de Kiro; no lee ni guarda su valor.
- No ejecutes los scripts heredados de CAO (`scripts/*.sh`).

## 1. Comprobar WSL2 y Ubuntu

En **PowerShell** (Windows):

```powershell
wsl -l -v
```

La distribución Ubuntu debe mostrar `VERSION 2`. Si no tienes WSL, sigue la documentación oficial de Microsoft (`wsl --install -d Ubuntu-24.04`) y reinicia si lo pide.

En **Ubuntu (WSL)**:

```bash
lsb_release -ds
```

```bash
sudo apt update && sudo apt install -y git curl ca-certificates build-essential python3 python3-venv python3-pip
```

```bash
python3 --version
```

Ubuntu 24.04 trae Python 3.12; Nexus exige 3.11 o superior.

## 2. Ubicar el repositorio en el sistema de archivos de WSL

Clona o copia el repositorio bajo tu `HOME` de Linux (por ejemplo `~/proyectos/jasp-nexus`), **no** en `/mnt/c/...`: `node_modules` y SQLite son mucho más lentos sobre NTFS (supuesto S12 del diseño). Tus proyectos objetivo pueden seguir en `C:\laragon\www` (`/mnt/c/laragon/www`).

`main` contiene commits locales que **no se han publicado** en GitHub (la regla del repo es no hacer push sin que tú lo pidas). Elige una de estas vías:

- **Si decides publicar** `main` desde el equipo donde está el trabajo, en WSL basta con:

  ```bash
  mkdir -p ~/proyectos && cd ~/proyectos && git clone https://github.com/JASP15/jasp-nexus.git && cd jasp-nexus
  ```

- **Sin publicar**, con un *bundle* de Git. En el equipo donde está el trabajo (por ejemplo macOS), desde la raíz del repo:

  ```bash
  git bundle create jasp-nexus-main.bundle main
  ```

  Copia el archivo a Windows (por ejemplo a `C:\Users\<tú>\Downloads`) y en WSL:

  ```bash
  mkdir -p ~/proyectos && cd ~/proyectos && git clone -b main /mnt/c/Users/<tú>/Downloads/jasp-nexus-main.bundle jasp-nexus && cd jasp-nexus
  ```

Comprueba que tienes el último commit esperado:

```bash
git log --oneline -3
```

## 3. uv y ruff

`uv` y ruff son herramientas de desarrollo; Nexus no los necesita para ejecutarse. Instalador oficial de uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Abre una terminal nueva (o ejecuta `source ~/.local/bin/env`) y comprueba:

```bash
uv --version
```

Ruff con la misma versión fijada en el extra `dev` de `pyproject.toml`:

```bash
uv tool install ruff==0.17.3
```

```bash
ruff --version
```

Desde la raíz del repositorio, `uv run ruff ...` crea `.venv/` y `uv.lock` (ambos ignorados por Git) y usa el ruff instalado como herramienta. Si `ruff --version` no muestra `0.17.3`, ejecuta `uv tool install --force ruff==0.17.3`.

## 4. Node LTS

Solo hace falta para la consola `web/` (F4) y como alternativa de instalación de algunas CLIs. Con nvm (instalador oficial, versión fijada):

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.41.0/install.sh | bash
```

Abre una terminal nueva y:

```bash
nvm install --lts
```

```bash
node --version && npm --version
```

## 5. Claude Code

Instalador nativo oficial para Linux y WSL:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

```bash
claude --version
```

Inicio de sesión con tu suscripción (abre el navegador de Windows o muestra una URL para copiar):

```bash
claude auth login
```

```bash
claude auth status --text
```

Requiere un plan Pro, Max u otro con Claude Code. No definas `ANTHROPIC_API_KEY` si quieres usar la suscripción.

## 6. Codex CLI

Instalador oficial para Linux:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

Alternativa con Node: `npm install -g @openai/codex` (sin `sudo`).

```bash
codex --version
```

Inicio de sesión con ChatGPT. En WSL el flujo de dispositivo evita depender del navegador: muestra una URL y un código para introducir en cualquier navegador.

```bash
codex login --device-auth
```

```bash
codex login status
```

## 7. Kiro CLI

Instalador oficial (macOS, Linux y Windows):

```bash
curl -fsSL https://cli.kiro.dev/install | bash
```

Requisito de Linux: glibc 2.34 o superior (Ubuntu 24.04 lo cumple).

```bash
kiro-cli --version
```

Inicio de sesión: elige el método; en un equipo sin navegador directo, la CLI muestra una URL y un código de un solo uso.

```bash
kiro-cli login
```

```bash
kiro-cli whoami
```

**Opcional, modo headless con clave de API** (solo planes Kiro Pro, Pro+, Pro Max o Power): genera la clave en app.kiro.dev, sección *API Keys*, y añade `export KIRO_API_KEY=...` a tu `~/.bashrc` o `~/.profile`, fuera del repositorio. Si hay sesión de navegador activa, Kiro la usa antes que la clave.

## 8. Verificar

Desde la raíz del repositorio en WSL. `doctor` es el heredado: busca `claude`, `codex`, `kiro-cli` y `cmdc` y consulta `cao-server`; es normal que `commandcode` salga `missing` y `cao-server` `offline` (legado que se retira en F5).

```bash
PYTHONPATH=src python3 -m jasp_nexus.cli doctor
```

```bash
claude auth status --text; codex login status; kiro-cli whoami
```

Verificación base de toda tarea:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

```bash
PYTHONPATH=src python3 -m jasp_nexus.cli --help
```

```bash
uv run ruff check . && uv run ruff format --check .
```

```bash
git diff --check && git status --short
```

Resultado esperado: `doctor` muestra `found` para `claude`, `codex` y `kiro`; los tres comandos de estado indican sesión iniciada; unittest termina en `OK`; ruff no informa errores; `git status` no muestra archivos nuevos fuera de los ignorados.

## 9. Registrar el entorno

Copia en [entorno-2026-11.md](entorno-2026-11.md) las versiones y resultados observados, siguiendo sus reglas de redacción (sin tokens, correos ni rutas de credenciales).

## Problemas frecuentes

- **`command not found` tras instalar:** abre una terminal nueva; los instaladores añaden `~/.local/bin` al `PATH` en el perfil de shell.
- **El navegador no se abre desde WSL:** copia la URL que muestra la CLI en el navegador de Windows o usa el flujo de dispositivo (`codex login --device-auth`, método de dispositivo en `kiro-cli login`).
- **Lentitud en `npm` o `uv`:** confirma que el repositorio está bajo `~/` y no en `/mnt/c`.
- **Python inferior a 3.11 en macOS:** la suite no corre ahí; se verifica en WSL.
