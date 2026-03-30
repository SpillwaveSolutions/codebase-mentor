---
phase: 14
slug: gemini-converter-implementation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.0+ |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `pytest tests/test_gemini_installer.py -x` |
| **Full suite command** | `pytest tests/ -m 'not slow'` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_gemini_installer.py -x`
- **After each wave:** Run `pytest tests/ -m 'not slow'`
- **Phase gate:** Full suite green before `/gsd:verify-work`

---

## Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GEMINI-01 | Global install writes to `~/.gemini/codebase-wizard/` | unit | `pytest tests/test_gemini_installer.py::test_global_install -x` | No (Wave 1) |
| GEMINI-02 | Project install writes to `./.gemini/codebase-wizard/` | unit | `pytest tests/test_gemini_installer.py::test_project_install -x` | No (Wave 1) |
| GEMINI-03 | `allowed_tools:` → `tools:` YAML array | unit | `pytest tests/test_gemini_installer.py::test_agent_tools_array_format -x` | No (Wave 1) |
| GEMINI-04 | 10 tool name mappings | unit | `pytest tests/test_gemini_installer.py -k "tool_mapping" -x` | No (Wave 1) |
| GEMINI-05 | `color:` stripped | unit | `pytest tests/test_gemini_installer.py::test_color_field_stripped -x` | No (Wave 1) |
| GEMINI-06 | Task and mcp__ excluded | unit | `pytest tests/test_gemini_installer.py::test_task_and_mcp_excluded -x` | No (Wave 1) |
| GEMINI-07 | Commands → `.toml` files | unit | `pytest tests/test_gemini_installer.py::test_command_to_toml -x` | No (Wave 1) |
| GEMINI-08 | `${VAR}` → `$VAR` | unit | `pytest tests/test_gemini_installer.py::test_template_var_escape -x` | No (Wave 1) |
| GEMINI-09 | `<sub>` → `*(text)*` | unit | `pytest tests/test_gemini_installer.py::test_sub_tag_conversion -x` | No (Wave 1) |
| GEMINI-10 | Path rewriting `~/.claude` → `~/.gemini` | unit | `pytest tests/test_gemini_installer.py::test_path_rewriting -x` | No (Wave 1) |
| GEMINI-11 | Skills copied verbatim to `skill/` | unit | `pytest tests/test_gemini_installer.py::test_skills_copied -x` | No (Wave 1) |
| GEMINI-12 | Uninstall removes dir, no-op if absent | unit | `pytest tests/test_gemini_installer.py -k "uninstall" -x` | No (Wave 1) |
| GEMINI-13 | Status reporting includes Gemini | unit | `pytest tests/test_gemini_installer.py::test_status -x` | No (Wave 2) |
| GEMINI-14 | `--for all` includes Gemini | unit | `pytest tests/test_gemini_installer.py::test_for_all -x` | No (Wave 2) |
| GEMINI-15 | TDD suite covers all conversion rules | meta | `pytest tests/test_gemini_installer.py -v` | No (Wave 1) |

---

## Wave Verification

### Wave 1: 14-01 (TDD gemini.py)
**Gate:** `pytest tests/test_gemini_installer.py -x` exits 0 (25+ tests pass)

### Wave 2: 14-02 (CLI wiring)
**Gate:** `pytest tests/ -m 'not slow' -x` exits 0 (full fast suite)
