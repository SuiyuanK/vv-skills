---
name: windows-vivado-clean-uninstall
description: Safe Windows Vivado/Xilinx clean-uninstall guidance. Use when Codex needs to diagnose Vivado uninstall leftovers, prepare a cautious cleanup plan, inspect residual Xilinx/Vivado paths, registry keys, services, or environment variables, or turn a Vivado uninstall guide into executable but confirmation-gated steps without accidentally uninstalling or deleting the user's active Vivado installation.
---

# Windows Vivado Clean Uninstall

## Overview

Use this skill to help with Vivado/Xilinx removal, residue diagnosis, reinstall-blocker cleanup, and Windows environment repair. Treat all uninstall, deletion, registry, service, and environment-variable changes as destructive unless the user explicitly asks to execute them.

## Safety Rules

- Do not uninstall Vivado, delete `C:\Xilinx`, remove registry keys, delete services, or mutate environment variables unless the user explicitly asks for execution in the current turn.
- Default to read-only inspection and a staged cleanup plan.
- Before any destructive step, identify the exact target paths, registry keys, services, and variables. Ask for confirmation if the user has not already authorized that exact class of change.
- Prefer backups before changes: system restore point when practical, exported `.reg` files for registry edits, and a saved copy of user/system PATH before environment edits.
- On this user's machine, do not infer that Vivado should be removed just because this skill is invoked; the original request may be to package the workflow only.

## Workflow

1. Clarify intent:
   - If the user wants a guide, runbook, script draft, or skill/resource packaging, do not touch the installed Vivado instance.
   - If the user wants cleanup executed, confirm scope: official uninstall only, residual files only, registry only, environment variables only, or all.
2. Inspect read-only state first:
   - Running processes: `vivado.exe`, `xsct.exe`, `xsim.exe`, `xlicmgr.exe`, `uninstall.exe`.
   - Install folders and user-cache folders.
   - Xilinx/Vivado environment variables and PATH entries.
   - Xilinx registry keys and license-manager service only when elevated access is available or user asks for commands to run.
3. Produce a report before changes:
   - Existing Vivado versions found.
   - Residual files/directories found.
   - Registry keys or services that appear Xilinx-specific.
   - PATH and variables that point to Vivado/Xilinx.
   - Risk notes and backup recommendations.
4. Execute only authorized changes:
   - Run official uninstaller first when available.
   - Remove residual directories only after verifying they are Xilinx/Vivado-specific and not project workspaces.
   - Export registry keys before deleting or renaming.
   - Save environment variable snapshots before editing PATH or removing Xilinx variables.
5. Verify after cleanup:
   - New terminal cannot resolve `vivado` unless another installation remains intentionally.
   - Xilinx-specific env vars are absent or point to the retained installation.
   - Reboot is recommended after service, registry, or machine-level environment changes.

## Reference

Read `references/vivado-cleanup-checklist.md` when you need concrete paths, registry keys, service names, variable names, or a staged cleanup sequence.

## Response Pattern

When helping a user, lead with whether you are staying read-only or about to request approval for a destructive step. Give exact commands only when useful, and label commands as inspect-only, backup, or destructive.
