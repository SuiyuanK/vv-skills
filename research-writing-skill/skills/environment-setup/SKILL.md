---
name: environment-setup
description: Use when Python environment setup is needed for data visualization or conda installation is required
---

# 环境配置

本技能用于在终端完成 Python 画图环境的全流程配置。

## 适用场景

- 用户要求安装 Miniconda
- 用户要求创建虚拟环境
- 用户要求"用 Python 画图"但环境未就绪
- 绘图脚本运行报环境相关错误

## Checklist

- [ ] 系统识别（macOS/Linux/Windows）
- [ ] Miniconda 安装/修复
- [ ] conda 初始化
- [ ] 创建 `research` 环境
- [ ] 安装绘图依赖
- [ ] 环境自检
- [ ] 更新 `plan/progress.md`

## 一、系统识别

### macOS / Linux

```bash
uname -s
uname -m
echo "$SHELL"
```

### Windows PowerShell

```powershell
$PSVersionTable.PSVersion
$env:OS
```

## 二、Miniconda 安装

### macOS 全自动流程

```bash
set -euo pipefail

# 1) 选择安装包
ARCH="$(uname -m)"
if [ "$ARCH" = "arm64" ]; then
  URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"
else
  URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
fi

# 2) 下载并静默安装
INSTALLER="$HOME/Downloads/miniconda.sh"
curl -fsSL "$URL" -o "$INSTALLER"
bash "$INSTALLER" -b -p "$HOME/miniconda3"

# 3) 当前 shell 立即可用
export PATH="$HOME/miniconda3/bin:$PATH"

# 4) 初始化 shell
"$HOME/miniconda3/bin/conda" init "$(basename "$SHELL")"

# 5) 验证
conda --version
```

### Windows 全自动流程（PowerShell）

```powershell
$ErrorActionPreference = "Stop"

# 1) 下载
$installer = Join-Path $env:TEMP "Miniconda3-latest-Windows-x86_64.exe"
Invoke-WebRequest -Uri "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe" -OutFile $installer

# 2) 静默安装
$target = "$env:USERPROFILE\miniconda3"
Start-Process -FilePath $installer -ArgumentList "/InstallationType=JustMe","/RegisterPython=0","/S","/D=$target" -Wait

# 3) 初始化 powershell
& "$target\Scripts\conda.exe" init powershell

# 4) 验证
$env:Path = "$target;$target\Scripts;$target\condabin;" + $env:Path
conda --version
```

## 三、创建科研虚拟环境

**默认环境名**：`research`

### 创建与激活

```bash
conda create -n research python=3.11 -y
conda activate research
python -m pip install --upgrade pip
```

## 四、安装绘图依赖

```bash
pip install numpy pandas scipy matplotlib seaborn scikit-learn statsmodels jupyter ipykernel openpyxl
python -m ipykernel install --user --name research --display-name "Python (research)"
```

可选：

```bash
pip install plotly pingouin
```

## 五、环境自检

```bash
python - <<'PY'
import sys
import numpy, pandas, matplotlib, seaborn, sklearn, statsmodels
print('Python:', sys.version.split()[0])
print('numpy:', numpy.__version__)
print('pandas:', pandas.__version__)
print('matplotlib:', matplotlib.__version__)
print('seaborn:', seaborn.__version__)
print('sklearn:', sklearn.__version__)
print('statsmodels:', statsmodels.__version__)
print('ENV CHECK: OK')
PY
```

## 六、画图任务前检查

执行画图任务前，至少确认：
1. 已激活 `research` 环境
2. `matplotlib` 和 `seaborn` 导入正常
3. 输出目录存在（如 `figures/`）

## 七、常见问题与修复

### `conda: command not found`

macOS / Linux：
```bash
export PATH="$HOME/miniconda3/bin:$PATH"
conda init "$(basename "$SHELL")"
```

Windows PowerShell：
```powershell
$env:Path = "$env:USERPROFILE\miniconda3;$env:USERPROFILE\miniconda3\Scripts;" + $env:Path
```

### 下载慢或超时

```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### 包冲突

```bash
conda create -n research_clean python=3.11 -y
conda activate research_clean
pip install -r requirements.txt
```

## 八、执行约束

<HARD-GATE>
1. 用户提到"安装环境/画图报错"，优先执行本技能
2. 先识别系统，再给对应命令，禁止跨系统混发命令
3. 执行完成后，必须回写 `plan/progress.md`
</HARD-GATE>
