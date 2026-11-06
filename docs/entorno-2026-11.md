# Entorno observado: noviembre de 2026

Registro de la tarea T02 de [multi-provider-orchestrator](../.kiro/specs/multi-provider-orchestrator/tasks.md). Recoge las versiones y resultados **observados** en el host principal tras seguir [setup-wsl.md](setup-wsl.md). Un valor sin observar se deja como «pendiente»; nunca se rellena por suposición.

**Reglas de redacción:** sin tokens, claves, códigos de dispositivo, correos, nombres de organización ni rutas de credenciales (`~/.claude`, `~/.codex`, `~/.kiro`…). El estado de login se registra solo como «sesión iniciada» o «sin sesión», con el método (suscripción, dispositivo, clave de API por nombre).

**Estado: pendiente de observación en WSL.**

## Host

| Elemento | Valor observado |
|---|---|
| Fecha de la observación | pendiente |
| Windows / WSL (`wsl -l -v`) | pendiente |
| Distribución (`lsb_release -ds`) | pendiente |
| Ubicación del repositorio | pendiente (bajo `~/` o `/mnt/c`) |
| Commit (`git log --oneline -1`) | pendiente |

## Herramientas de desarrollo

| Herramienta | Comando | Versión observada |
|---|---|---|
| Python | `python3 --version` | pendiente |
| uv | `uv --version` | pendiente |
| ruff | `ruff --version` | pendiente (esperada 0.17.3) |
| Node | `node --version` | pendiente |
| npm | `npm --version` | pendiente |

## CLIs de agentes

| CLI | Versión (`--version`) | Estado de login | Método |
|---|---|---|---|
| Claude Code (`claude`) | pendiente | pendiente (`claude auth status --text`) | pendiente |
| Codex (`codex`) | pendiente | pendiente (`codex login status`) | pendiente |
| Kiro CLI (`kiro-cli`) | pendiente | pendiente (`kiro-cli whoami`) | pendiente |

Referencia: en macOS (host secundario) se observaron el 6 de noviembre de 2026 `claude` 2.1.303 y `codex` 0.163.0; Kiro CLI no estaba instalado.

## Verificación

| Comando | Resultado observado |
|---|---|
| `PYTHONPATH=src python3 -m jasp_nexus.cli doctor` | pendiente |
| `PYTHONPATH=src python3 -m unittest discover -s tests -v` | pendiente (número de pruebas y `OK`/fallos) |
| `PYTHONPATH=src python3 -m jasp_nexus.cli --help` | pendiente |
| `uv run ruff check .` | pendiente |
| `uv run ruff format --check .` | pendiente |
| `git diff --check` y `git status --short` | pendiente |

## Observaciones

Pendiente: incidencias de instalación, avisos relevantes o pasos que difirieron de la guía.
