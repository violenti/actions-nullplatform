# Tests con act

Esta suite ejecuta la acción y los workflows locales con [nektos/act](https://github.com/nektos/act).
No modifica los workflows de producción para simular su comportamiento.

## Requisitos

- Python 3.9+, `make`, Docker iniciado y `act` v0.2.89.
- Acceso a GitHub y al registro de contenedores en la primera ejecución.
- En macOS, se puede instalar act con `brew install act`.

```sh
make test-list  # Enumerar escenarios, sin act ni Docker
make test-plan  # Validar planes de act; no ejecuta las aserciones
make test       # Ejecutar todos los escenarios
python3 tests/act/run.py --suite run-first
python3 tests/act/run.py --suite branch
```

Se utiliza `catthehacker/ubuntu:act-24.04` y arquitectura `linux/amd64`, también
en Apple Silicon. Se pueden cambiar con `ACT_RUNNER_IMAGE` y `ACT_ARCH`.
`ACT_BIN` permite seleccionar otro ejecutable de act.
La primera descarga de la imagen puede tardar varios minutos.

## Pre-commit

Instalar [pre-commit](https://pre-commit.com/) (en macOS: `brew install pre-commit`)
y activar el hook una vez por clon:

```sh
make install-hooks
```

Cada commit ejecuta la suite completa, incluso si solo cambia documentación.
Si falla un test, falta act o Docker no está disponible, el commit se bloquea.
La salida muestra el error original y el mensaje:

```text
Commit bloqueado: la suite de tests con act falló.
Revisá el error anterior, corregí el problema y volvé a intentar el commit.
Para reproducirlo: make test (requiere act instalado y Docker iniciado).
```

Para ejecutarlo manualmente: `pre-commit run act-tests --all-files`.
El hook prueba el estado preparado por pre-commit para el commit; los cambios
sin stage en archivos versionados se guardan temporalmente durante la ejecución.

## Escenarios

| Componente | Escenarios |
| --- | --- |
| `run-first` | Prioridad de candidatos, fallback, orden inverso, coincidencia exacta, candidatos inexistentes/vacíos, propagación del fallo sin ejecutar fallback, selección del package manager |
| `branch-validation` | feat/fix, excepciones Dependabot y release-please, nombre inválido, descripción vacía, tipo desconocido, patrón personalizado válido/inválido, evento sin rama de PR |

Los ocho casos de `run-first` usan un paquete sin dependencias en un directorio
con espacios. Se verifica el resultado del step y una traza que demuestra que
se ejecutó exactamente un script, o ninguno según el caso. El package manager
personalizado registra argumentos y delega a npm; no valida la instalación de pnpm.

Los diez casos de ramas llaman al workflow reutilizable real. Un caso negativo
solo pasa si act falla **y** aparece el mensaje de validación esperado; un fallo de
Docker o de descarga no cuenta como rechazo correcto de una rama.

Los archivos de eventos y configuración vacía se crean en un directorio temporal.
La suite pasa explícitamente archivos vacíos para secretos, variables, entorno e
inputs, evitando cargar los archivos locales predeterminados de act. La configuración
global/personal de act sigue aplicándose: revisar sus opciones antes de ejecutar.

## Límites y extensión

Esta es la suite inicial de comportamiento, no cobertura de todos los workflows.
No prueba AWS/OIDC, ECR, KMS/cosign, publicaciones, releases, revisiones con IA ni
los pipelines completos de Go, Node y Terraform. Esos flujos necesitan fixtures
de consumidores y, en algunos casos, servicios de prueba. La sintaxis general y
el escaneo de secretos siguen a cargo de `pr-checks-actions.yml`.

Para agregar casos de ramas, extender `CASES` en `run.py`. Para `run-first`,
extender la matriz y los scripts del paquete fixture. Los callers de prueba
están fuera de `.github/workflows` para que GitHub no los ejecute directamente.
`test-act.yml` instala act con versión fija y verifica el checksum del archivo
antes de ejecutar la misma suite en CI.

Referencia: [uso de act](https://nektosact.com/usage/index.html) y
[imágenes de runners](https://nektosact.com/usage/runners.html).
