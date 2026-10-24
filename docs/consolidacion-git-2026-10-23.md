# Una sola rama local para continuar

El usuario aclaró que el resultado esperado era una sola rama con los cambios fusionados. La consolidación ya terminó en `main`, merge `e120277e7930b77766f81201fa08cac6b79be1fd`, con padres `9e661af670baa2e56884cc3990ab4469d92f2eca` (conservación local) y `8683b6568ff026cb957866225115743b8b01d4f8` (foundation). No sustituye la revisión técnica de T01: Claude solicitó correcciones documentales en ronda 1 y emitió APROBADO en ronda 2.

## Estado de partida

- `main` y `feat/estructura-inicial` apuntaban a `caeb82e`, el commit inicial.
- `origin/feat/foundation-cao-mvp` apuntaba a `8683b65`, con 13 commits adicionales.
- Los archivos recuperados y conciliados, perfiles, scripts y specs estaban en la carpeta de trabajo sin commit. Cambiar de rama podía intentar sobrescribir esos archivos.
- No existe una rama `master` en este repositorio.

## Respaldo y conservación

Antes de consolidar se verificó un respaldo de 48 archivos seguros y un bundle de las referencias e historial originales en `.build/git-consolidation-2026-10-23/`:

- `working-tree/`: copia anterior a esta operación.
- `manifest-before.json`: inventario y hashes SHA-256.
- `refs-before.txt`: referencias originales.
- `history-before.bundle`: historial recuperable, verificado con Git.

No se incluyeron credenciales ni archivos de entorno. `.build/` sigue ignorado por Git.

Se conservan los perfiles, scripts, política YAML y diseño de consola porque contienen trabajo único, aunque su integración no esté validada. El archivo vacío de nombre accidental `%sn  ; done; echo ---` se conserva en el respaldo ignorado y se retira de la raíz; no forma parte del proyecto.

## Consolidación realizada

1. Se guardaron los archivos útiles en el commit de conservación `9e661af`. T01 siguió sin marcar.
2. Se hizo el merge real de foundation para conservar sus 13 commits en el historial.
3. Se preservaron los documentos conciliados y los archivos de código, pruebas, catálogo, empaquetado y CI idénticos a foundation.
4. Se adelantó `main` al resultado y se retiró `feat/estructura-inicial` tras verificar que su historial quedó incorporado.
5. Se comprobó foundation como ancestro de `main`, la conservación de archivos útiles y el árbol limpio antes de las correcciones de revisión.

La instrucción del usuario autoriza estos commits y cambios de referencias como excepción a las restricciones de preparación anteriores. No autoriza dar por revisada T01, iniciar T02 ni publicar cambios.

## Cómo continuar

Trabajar en `main`. El commit de merge contiene el historial foundation y el trabajo local guardado. Los informes anteriores de recuperación son históricos: describen la etapa en la que todavía se habían copiado archivos sin fusionar ramas.

Las referencias `origin/main` y `origin/feat/foundation-cao-mvp` pueden seguir apareciendo en GitKraken dentro de los remotos. Representan el estado de GitHub conocido por este clon; no son ramas locales pendientes de combinar. Esta consolidación no hace push, no borra ramas de GitHub y no cierra su PR.

La revisión externa de T01 terminó con APROBADO en ronda 2; véase su [registro](revisiones/local-runtime-mvp-t01.md). El commit de cierre deriva de `e120277` y contiene las correcciones documentales revisadas, la casilla y los dictámenes. Los commits de conservación no son evidencia de aprobación; T02 permanece pendiente.
