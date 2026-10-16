# 查询与条件式修复

以下示例在 PowerShell 中执行。先将变量替换为本次已核实目标，不把案例值作为默认删除目标。

## 1. 读取对应日志

```powershell
Get-AppxLog | Format-List TimeCreated, Id, Message
```

若不是目标部署，查询近期错误；根据实际显示名、包名或 ActivityId 筛选，不能只搜显示名：

```powershell
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-AppXDeploymentServer/Operational'
    StartTime = (Get-Date).AddHours(-1)
    Level = 2
} | Select-Object -First 30 TimeCreated, Id, ActivityId, Message | Format-List
```

## 2. 核对包和清单

管理员终端查询所有用户。将 `实际包名` 换成日志中的 Name（不包含版本和架构）。

```powershell
$packageName = '实际包名'
$packages = @(Get-AppxPackage -AllUsers -Name $packageName)
$packages | Format-List Name, PackageFullName, Version, Status, InstallLocation, PackageUserInformation
```

出现多个版本时逐一解释，不能默认为第一个就是故障包。选择与失败日志一致的精确包：

```powershell
$fullName = '日志中确认的完整包名'
$pkg = $packages | Where-Object PackageFullName -eq $fullName
if (@($pkg).Count -ne 1 -or -not $pkg.InstallLocation) {
    throw '无法唯一定位目标包及安装路径，停止'
}
[xml]$manifest = Get-Content -LiteralPath (Join-Path $pkg.InstallLocation 'AppxManifest.xml') -Raw -ErrorAction Stop
$extensions = $manifest.SelectNodes("//*[local-name()='Extension' and @Category='windows.service']")
foreach ($extension in $extensions) {
    $extension.OuterXml
    foreach ($service in $extension.SelectNodes(".//*[local-name()='Service']")) {
        $serviceName = $service.GetAttribute('Name')
        sc.exe qc $serviceName
        sc.exe sdshow $serviceName
    }
}
```

记录所有声明的服务，检查旧路径是否属于另一账户仍使用的包。停止状态及退出码 1077 本身不证明服务损坏。

## 3. 普通卸载优先

先保存未同步内容并说明本地应用数据影响。使用设置中的卸载，或对已确认的精确包执行：

```powershell
Remove-AppxPackage -Package $fullName -ErrorAction Stop
```

确需系统范围且已授权时，才使用 `-AllUsers`；不是针对 Staged 状态的保证清理手段。卸载后重新查询包和服务。若尚未重启且有待删除迹象，可重启一次；重启后仍相同就不要循环。

## 4. 高级定向服务清理

仅在入口的证据、范围和备份条件满足时使用。这里的 `$serviceName` 必须选自刚核对的清单，并与旧版本服务路径一致。不要复用循环结束后未经检查的变量值。

保存注册表值备份，并额外保留 `sc.exe qc`、`sc.exe sdshow` 输出。`.reg` 导出不保存完整 ACL，也不是完整 AppX 回滚快照；需完整安全描述符备份或系统恢复时另行制定计划。

```powershell
$serviceName = '本次确认的服务名'
$workspaceRoot = '本次会话初始工作区的绝对路径'
$backupDir = Join-Path $workspaceRoot 'tmp'
New-Item -ItemType Directory -Path $backupDir -Force -ErrorAction Stop | Out-Null
$backupFile = Join-Path $backupDir ('service-' + [guid]::NewGuid().ToString() + '.reg')
$serviceKey = 'HKLM\SYSTEM\CurrentControlSet\Services\' + $serviceName
reg.exe export $serviceKey $backupFile
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $backupFile)) {
    throw '备份失败，停止清理'
}
Get-Item -LiteralPath $backupFile | Select-Object FullName, Length
sc.exe delete $serviceName
```

管理员 `sc.exe delete` 若报 5 拒绝访问，先解释保护/权限，并再次核对目标。根据当前授权与风险，可提出精确 `reg.exe delete $serviceKey /f` 候选；**不是自动下一步**，也不能把此命令当作已验证修复。不要删除父键或邻近服务；若仍拒绝访问就停止，不自动改变所有者或提升到 SYSTEM。

## 5. 验证与恢复

- 服务清理成功后重启，再查询，预期旧服务不存在（1060）。
- 商城重装后，检查新的部署日志、应用启动与服务路径；包 `Servicing` 和旧版本路径是否消失。
- 新安装可重新创建同名服务，因此“服务存在”不能作为重装失败的唯一标准。
- 若需要回滚，先确认当前没有新版服务，避免导入备份覆盖新版。导入旧 `.reg` 不等于恢复应用包、账户注册或 ACL；必要时交给系统恢复方案，不能保证靠 reg import 完整还原。
