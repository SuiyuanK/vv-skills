@echo off
setlocal enabledelayedexpansion

REM SessionStart hook for research-writing-assistant plugin (Windows)
REM Usage: run-hook.cmd session-start

set "SCRIPT_DIR=%~dp0"
set "PLUGIN_ROOT=%SCRIPT_DIR%.."

if "%1"=="session-start" (
    REM Read the skill file content
    set "SKILL_FILE=%PLUGIN_ROOT%\skills\using-research-writing\SKILL.md"
    
    if exist "!SKILL_FILE!" (
        REM For Windows, we output a simplified JSON response
        echo {"additional_context": "你已加载科研写作助手。当用户提出论文写作任务时，请调用 research-writing:using-research-writing 技能。"}
    ) else (
        echo {"additional_context": "科研写作助手已加载，但未找到入口技能文件。"}
    )
) else (
    echo {"error": "Unknown hook: %1"}
)

endlocal
