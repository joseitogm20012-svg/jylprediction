---
name: git-rebase-guide
description: Ayuda a resolver conflictos complejos de Git durante operaciones de rebase o merge. Usar cuando haya conflictos grandes o se necesite reescribir historia.
compatibility: [opencode]
---

# Git Rebase Guide

## Flujo
1. Antes: `git stash` o commitear cambios. Identificar commits a reordenar.
2. Ejecuta `git rebase -i HEAD~N`. Instrucciones: squash, fixup, reword, drop.
3. En conflictos: abre cada archivo, busca `<<<<<<<`, decide versión correcta.
4. Después: `git rebase --continue`. Verifica con `git log --oneline`.
5. Nunca rebasear ramas compartidas — solo ramas locales/feature.
