# Roadmap

## 0 — Fundamentos (este PR)
- Catálogo de agentes y enrutamiento determinista.
- Registro SQLite de tareas y eventos, revisión lógica, límites de intentos.
- CLI doctor, create, list, route, show, history, advance.
- Tests unitarios y pipeline CI (resultado de ejecución por verificar).
- Instrucciones Windows/WSL2 y macOS con CI Linux/macOS.

## 1 — Primer piloto con CAO
- Instalar CLIs y CAO en WSL2 y macOS, con autenticación independiente por host.
- Verificar perfiles restrictivos, aislamiento y políticas antes de ejecutar.
- Adaptador CAO real: salud, sesiones, terminales y ejecución autorizada.
- 3 tareas descartables: visual, backend y revisión con rechazo.

## 2 — Calidad y continuidad
- Verificar evidencia real (tests, captura, CI y git diffs).
- Worktrees y control de merges.
- Checkpoints y recuperación idempotente.
- Handoff Claude/Codex con única autoridad y estado versionado.
- Definir modelo multi-host seguro (Mac + WSL2), sin sincronizar SQLite mediante Git.

## 3 — Recursos modulares
- Adaptador Command Code y OpenRouter.
- Rutas por modelo/esfuerzo, costo, latencia y cuotas detectables.
- Métricas históricas para comparar calidad y productividad.

## 4 — UI propia (solo si aporta valor)
- Aprovechar primero Web UI integrada en CAO.
- Añadir Nexus Console si la experiencia existente es insuficiente.

Criterio go/no-go: menos supervisión, misma o mejor calidad, presupuesto controlado.
