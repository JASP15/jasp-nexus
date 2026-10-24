# T01: registro de revisión y cierre

Fecha: 23 de octubre de 2026. Spec: `local-runtime-mvp`. Implementador: Codex, como respaldo por indisponibilidad de Kiro. Revisor de otro proveedor: Claude/Anthropic; modelo mostrado en la interfaz: **Sonnet 5.5 Bajo**.

## Alcance y dictámenes

La revisión parte de `main`, merge `e120277e7930b77766f81201fa08cac6b79be1fd`, con padres `9e661af670baa2e56884cc3990ab4469d92f2eca` y `8683b6568ff026cb957866225115743b8b01d4f8`. La ronda 2 aprobó T01 y los 12 documentos corregidos identificados en el [manifiesto de hashes](local-runtime-mvp-t01-manifest-aprobado.json), conservado sin cambios. SHA-256 del paquete revisado: `59da3ddf926b5223d17f1f280071790030cc3f4d69f69c9234ef4b668df31823`.

- [Ronda 1: CAMBIOS REQUERIDOS](local-runtime-mvp-t01-claude-ronda-1.md), dictamen íntegro. SHA-256: `b2ecb3cfe8a0f984d9784db841c9a45691f0948592d59e040ea773f1d94a2f19`.
- [Ronda 2: APROBADO](local-runtime-mvp-t01-claude-ronda-2.md), dictamen íntegro. SHA-256: `1f0fb37f7e871fdd88ad777b5f6c8a8c67c97c1d174fb4a23016bf9ea2359e37`.
- [Conversación original de Claude](https://claude.ai/chat/56702403-3333-4294-b75d-620d3ead8448).

Los archivos de los dictámenes se copiaron íntegros desde la evidencia local de entrega; no se incluyen conversaciones ajenas, paquetes completos ni capturas en Git. Paquetes y evidencia visual permanecen en `.build/review-t01-main-e120277/`, ignorado por Git.

## Comprobaciones del implementador

Codex verificó después del APROBADO las 15/15 pruebas unittest y el smoke CLI create → route → show/history/list en WSL, con SQLite temporal. No se ejecutaron proveedores ni se abrieron bases de usuario. Se confirmó que los 12 documentos coincidían con los hashes del paquete aprobado antes del cierre administrativo, que los 11 archivos heredados enumerados en T01 siguen idénticos a foundation y que foundation es ancestro de `main`.

Claude revisó texto; no ejecutó pruebas ni verificó el repositorio por su cuenta. Los resultados anteriores corresponden al implementador y su evidencia local `close-verification.json`. También se exige `git diff --check` antes del commit y árbol limpio al terminar. Ruff, pytest, frontend y CI remoto no se presentan como ejecutados.

## Cierre administrativo

El commit `T01: Foundation reconciliation and compatibility` deriva de `e120277` e incluye las correcciones documentales aprobadas, el registro del dictamen y la casilla de T01 marcada. Las actualizaciones posteriores al APROBADO solo reflejan la aprobación y conservan evidencia: no cambian requisitos, implementación ni criterios de aceptación. El manifiesto identifica las versiones exactas aprobadas antes de esas actualizaciones; las copias originales están en `.build/review-t01-main-e120277/approved-originals/`.

El merge de conservación no se reinterpreta como aprobación técnica. T02 queda pendiente, sin implementar ni aprobar. Se conserva `main` como única rama local y no se hace push.
