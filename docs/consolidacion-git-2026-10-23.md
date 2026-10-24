# Una sola rama local para continuar

El usuario aclaró que el resultado esperado era una sola rama con los cambios fusionados. Esta operación consolida Git; no sustituye la revisión técnica de T01, que sigue pospuesta por petición del usuario.

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

## Consolidación

1. Guardar los archivos útiles en un commit de conservación en la rama actual. T01 sigue sin marcar.
2. Hacer un merge real de foundation para conservar sus 13 commits en el historial.
3. Resolver los documentos compartidos preservando las versiones conciliadas. Los archivos de código, pruebas, catálogo, empaquetado y CI coinciden con foundation.
4. Adelantar `main` al resultado, continuar en ella y retirar `feat/estructura-inicial` solo después de verificar que su historial está incorporado.
5. Comprobar que foundation es ancestro de `main`, que los archivos útiles siguen presentes y que el árbol de trabajo está limpio.

La instrucción del usuario autoriza estos commits y cambios de referencias como excepción a las restricciones de preparación anteriores. No autoriza dar por revisada T01, iniciar T02 ni publicar cambios.

## Cómo continuar

Trabajar en `main`. El commit de merge contiene el historial foundation y el trabajo local guardado. Los informes anteriores de recuperación son históricos: describen la etapa en la que todavía se habían copiado archivos sin fusionar ramas.

Las referencias `origin/main` y `origin/feat/foundation-cao-mvp` pueden seguir apareciendo en GitKraken dentro de los remotos. Representan el estado de GitHub conocido por este clon; no son ramas locales pendientes de combinar. Esta consolidación no hace push, no borra ramas de GitHub y no cierra su PR.

La revisión externa de T01 sigue pendiente. Los commits de conservación permiten retomar esa revisión con el trabajo guardado; no son evidencia de aprobación.
