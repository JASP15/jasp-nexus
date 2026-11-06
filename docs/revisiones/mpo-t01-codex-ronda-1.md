# T01 multi-provider-orchestrator: revisión Codex, ronda 1

- Revisor: Codex CLI 0.163.0 (proveedor efectivo OpenAI), `codex exec --sandbox read-only`, 6 de noviembre de 2026.
- Implementador: Claude Code (proveedor efectivo Anthropic).
- Alcance: árbol de trabajo sin commit sobre `main` `b6de266` (22 archivos `.md`).
- Texto íntegro del dictamen; solo se convirtieron las rutas absolutas del revisor en rutas relativas al repositorio.

---

Dictamen: CAMBIOS REQUERIDOS

## Hallazgos

1. **Bloqueante — `.kiro/specs/multi-provider-orchestrator/design.md:124`, `.kiro/specs/multi-provider-orchestrator/requirements.md:72`.** La protección del repositorio exige pasar automáticamente a `changes_requested` sin llamar al revisor, pero el control ocurre tras implementar, cuando la tarea está en `running`. `TaskStore` solo permite esa transición desde `in_review` y exige que el actor sea el revisor designado. Además, R6.1 prohíbe modificar `store.py`. La contradicción ya existe en el plan aprobado; impide implementar T12 tal como está escrita. **Corrección propuesta:** reportar la contradicción y acordar una transición compatible con la máquina de estados o un cambio revisado de esta; reflejar la decisión en requisitos, diseño y tareas.

2. **Bloqueante — `.kiro/specs/multi-provider-orchestrator/tasks.md:45`.** El plan exige que T03 resuelva o documente los riesgos originales R1–R4, equivalentes a S1–S4. La spec amplía la aceptación a S1–S7 y S9. Esto añade condiciones de cierre: por ejemplo, S9 incluye demostrar que no existe una API de cuota restante, algo que una ejecución mínima por CLI no establece necesariamente. **Corrección propuesta:** conservar S1–S4 como criterio de aceptación del plan y mantener las comprobaciones adicionales como verificaciones o supuestos pendientes con su evidencia, sin ampliar unilateralmente la aceptación.

3. **Bloqueante — `.kiro/specs/multi-provider-orchestrator/tasks.md:141`.** La verificación de T20 exige que `grep -ri "cao" --exclude-dir=archivo .` solo encuentre menciones históricas en `docs/`. El propio `AGENTS.md`, el steering y la spec activa contienen referencias vigentes a la retirada de CAO; además, la búsqueda abarca `.git` y otros archivos ajenos a ese criterio. El comando no puede cumplir la aceptación descrita. **Corrección propuesta:** definir una comprobación acotada a documentos pertinentes y evaluar si las coincidencias presentan CAO como plan vigente, en lugar de exigir ausencia de la palabra.

4. **Menor — `.kiro/specs/multi-provider-orchestrator/tasks.md:119`.** Varias tareas, entre ellas T16, T17 y T19, tienen verificación pero carecen de un apartado explícito de aceptación, pese al entregable solicitado para las 21 tareas. **Corrección propuesta:** añadir un criterio observable de aceptación a cada tarea que carezca de él.

5. **Menor — `.kiro/specs/multi-provider-orchestrator/design.md:168`.** Los riesgos R1–R13 del plan se renumeran como S1–S13 para distinguirlos de los requisitos; la correspondencia mantiene el orden. La renumeración está explicada y es razonable, pero debe actualizarse la referencia de T03 conforme al hallazgo 2.

## Verificación realizada

- Revisé el estado, el diff y los archivos nuevos, el plan aprobado, los documentos de dirección y la spec. `HEAD` es `b6de266`; los cambios identificados son Markdown y T01 permanece sin marcar.
- Contrasté las asignaciones previstas con la regla de proveedor efectivo: Claude/Anthropic y Kiro con modelo Anthropic se asignan a revisión de Codex/OpenAI; las tareas de Codex se asignan a Claude. La spec exige reelegir revisor si cambia el implementador efectivo.
- Contrasté `TRANSITIONS`, `assign` y `advance` con el flujo propuesto, así como `core.route`, `load_agents`, el catálogo y `pyproject.toml`. Las guías CAO revisadas llevan cabeceras que las identifican como históricas.
- Ejecuté `git status --short --branch`, `git diff --stat`, `git diff --name-only`, `git ls-files --others --exclude-standard`, `git diff` sobre los documentos, `git diff --check`, `git rev-parse --short HEAD`, búsquedas con `rg` y lecturas con `cat`, `sed` y `nl`. `git diff --check` terminó sin errores de espacios en los archivos rastreados; no cubre los archivos nuevos sin seguimiento.
- **No pude completar la comprobación automática de enlaces:** el intérprete `python3` no arrancó en el entorno de solo lectura por errores de caché de Xcode. Tampoco ejecuté unittest ni ruff: la tarea es documental y la verificación indicada para WSL no estaba disponible.