# Estructura del repositorio

## Implementado o recuperado

```text
AGENTS.md                          Reglas y spec activa
.kiro/steering/                    Producto, stack y estructura vigentes
.kiro/specs/local-runtime-mvp/     Spec activa de conciliación y flujo local
.kiro/specs/nexus-console/         Diseño de consola pospuesto
pyproject.toml                    Setuptools; entrypoint jasp_nexus.cli:main
src/jasp_nexus/
  __init__.py                     Versión 0.1.0
  cli.py                          argparse: doctor/create/list/show/route/history/advance
  core.py                         Catálogo JSON y routing simulado
  platform_support.py             Detección de host
  store.py                        TaskStore: tareas y eventos de transición SQLite
tests/                            15 pruebas unittest de la base
.github/workflows/ci.yml           CI foundation Linux/macOS
config/agents.example.json        Catálogo de la CLI; no demuestra disponibilidad real
config/routing.yaml               Política local para perfiles CAO, aún separada de la CLI
profiles/                         Perfiles CAO conservados
scripts/                          Scripts locales conservados; integración no validada
docs/                             Informe, conciliación, guías foundation y guía CAO histórica
.build/reconcile-2026-10-23/       Copias de originales y manifiesto local, ignorados por Git
```

Los archivos foundation proceden del commit `8683b6568ff026cb957866225115743b8b01d4f8`. Tras la recuperación inicial, el usuario pidió consolidar también su historial: los commits se incorporan mediante merge y se conserva `main` como única rama local de trabajo. La revisión técnica de T01 sigue pendiente.

## Datos y compatibilidad

La CLI guarda datos en `.nexus/state.sqlite3` relativo al directorio de ejecución, salvo `--db`. `.nexus/` está ignorado por Git. T01 no mueve ni abre bases existentes; las pruebas usan bases temporales. T02 añadirá tablas de ejecuciones/eventos medidos sin recrear `tasks` ni `events`.

`~/.jasp-nexus/` queda reservado para archivos auxiliares de la futura consola (por ejemplo cuota y logs); no es una segunda base canónica. Cualquier migración de ubicación o esquema necesitará diseño compatible, respaldo y revisión propios.

## Ampliaciones futuras

La spec activa podrá añadir configuración y clientes de servicios locales con módulos pequeños, CLI delgada y pruebas de red simulada. No hay `local_client`, agente OpenCode ni adaptador ComfyUI todavía.

La consola pospuesta podrá añadir `settings.py`, `routing.py`, `cao_client.py`, `quota.py`, `profiles.py`, `app.py`, `api/`, `static/`, `web/` y `launchers/windows/`. Son rutas previstas, no archivos existentes. Reutiliza `TaskStore` y la CLI; no reemplaza sus contratos.

## Convenciones de la consola futura

- Un router por recurso en `src/jasp_nexus/api/`, prefijo `/api`, sin lógica de negocio en routers.
- Modelos de respuesta pydantic junto a su router; modelos CAO en `cao_client.py` cuando exista contrato real.
- Componentes React funcionales, PascalCase, un componente por archivo, TypeScript estricto y textos en español.
- Build de Vite en `src/jasp_nexus/static/`, ignorado por Git e incluido en el paquete por setuptools cuando se implemente.
