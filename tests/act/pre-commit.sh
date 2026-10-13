#!/bin/sh
set -eu

if make test; then
  exit 0
else
  status=$?
  printf '\n%s\n' 'Commit bloqueado: la suite de tests con act falló.' >&2
  printf '%s\n' 'Revisá el error anterior, corregí el problema y volvé a intentar el commit.' >&2
  printf '%s\n' 'Para reproducirlo: make test (requiere act instalado y Docker iniciado).' >&2
  exit "$status"
fi
