---
name: windows-store-service-registration-fix
description: 诊断 Windows 微软商城/MSIX 安装或更新的 0x80073CF6，重点处理内层 0x80070005、windows.service 注册拒绝访问以及旧版打包服务残留；根据应用清单核对服务身份，按证据备份、清理并验证。适用于 ChatGPT/Codex 等打包服务应用，不用于 Linux 或一般网络下载故障。
---

# Windows 商城打包服务注册故障

用于从商城笼统错误定位到具体失败环节。优先解释已取得的证据，避免让用户循环清缓存、卸载和重启。

## 环境与依赖

- Windows 10/11、Windows PowerShell 5.1、内置 Appx 模块、sc.exe、reg.exe；读取所有用户的包需要管理员权限。
- 不自动安装依赖、修改系统权限或下载第三方安装包。缺少命令时说明限制。
- 所有主动生成的日志、备份和中间文件使用会话初始工作区的 `./tmp/`，文件名唯一；不覆盖原有文件。若用户另指定长期备份位置，按其指定。
- 本 skill 的用途是诊断与条件式修复；调用本 skill 不代表授权卸载其他账户的应用、清除本地数据或修改无关系统组件。按当前任务授权执行必要操作；范围不明时先展示具体目标和影响。

## 先定位，再选择修复

1. 记录系统版本、应用显示名、安装/更新/卸载重装历史和已经做过的操作。商城的“我们已了解此问题”是通用文案，不证明服务器故障。
2. 刚重现错误后读取部署日志。`Get-AppxLog` 默认只对应最近部署，可能取到其他应用；对照时间、包全名、操作和 ActivityId，必要时查询事件日志或按 ActivityId 取日志。
3. `0x80073CF6` 只代表包注册失败；追踪前面的具体错误。本路径要求日志明确出现 `windows.service` 扩展和 `0x80070005` 拒绝访问。没有这一证据时，不进入服务清理分支。
4. 从实际包的 AppxManifest.xml 获取服务名、可执行文件和账户，再查询服务配置与安全描述符。显示名、历史名称和包身份可能不同，不能仅凭 `OpenAI.Codex` 排除用户所指的 ChatGPT，也不能将二者名称关系推广为所有发行版事实。
5. 对比当前包版本与服务路径中的版本。旧服务路径、新包 `Servicing` 是更新未完成的线索，不单独证明服务可删除；先检查所有用户的包状态及服务实际归属。

可复制的只读查询及条件式修复见 [references/procedure.md](references/procedure.md)。不要照搬案例版本号、账户 SID 或包路径。

## 决策与停止条件

- 尚无具体日志、且未做基础检查时，可先尝试商城缓存重置与应用修复；日志已定位服务注册失败后不反复走基础步骤。
- 日志称 `ACLs repaired successfully` 只说明包目录 ACL 修复步骤完成，不证明服务权限恢复或下次安装必定成功。允许一次有依据的重试；同一错误复现后换诊断方向。
- 优先正常卸载重装；说明本地登录、设置和未同步数据可能丢失，先保存。系统范围卸载影响所有账户，必须先核对账户列表与任务授权。
- PowerShell 卸载无输出不等于成功：管道可能没有输入，或只去掉用户注册而仍有 SYSTEM 暂存包。重新查询包和服务，区分“命令成功”“用户已注销”“系统包/服务已移除”。
- `S-1-5-18: Staged` 表示 SYSTEM 暂存记录，不代表普通用户仍安装，也不证明文件或服务可以安全删除。
- 仅在实际清单、旧版服务路径、所有用户查询和卸载结果支持旧服务残留结论后，讨论定向清理。先成功备份准确的单个服务键，再尝试正常 `sc.exe delete`。
- 正常服务删除拒绝访问时，不宣称 ACL 损坏。打包服务可能有受保护的正常安全描述符；不要套用通用 SDDL、接管整个 Services/WindowsApps 或递归重置 ACL。
- 精确删除服务注册表键是高级人工修复候选，不是微软针对该问题保证有效的方案。必须解释影响、确认备份可读和范围已获授权；普通删除失败后停止并保留证据。不得自动升级到 SYSTEM/TrustedInstaller、临时计划任务或离线删除，也不直接改 AppRepository 数据库。
- 实际执行服务键删除成功后需要重启，再检查服务是否返回 1060，然后尝试安装并检查应用能否启动。新包重新创建同名服务是预期行为，最终要核对它指向当前版本。

## 交付与验证

分别报告已经确认的根错误、推测原因、实际改动、备份位置和当前验证结果。未收到安装成功反馈就写“待验证”，不能把建议当实测。尽量一次给出相互依赖的一组明确步骤及成功/失败分支。

本次经验的证据和未完成环节见 [references/case-2026-10-16.md](references/case-2026-10-16.md)，仅在需要案例比对时读取。

## 官方参考

- [部署错误码与日志](https://learn.microsoft.com/en-us/windows/win32/appxpkg/troubleshooting)
- [应用清单 Service 定义](https://learn.microsoft.com/en-us/uwp/schemas/appxpackage/uapmanifestschema/element-desktop6-service)
- [Remove-AppxPackage](https://learn.microsoft.com/en-us/powershell/module/appx/remove-appxpackage)
- [sc delete](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/sc-delete)
- [reg export](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/reg-export)、[reg delete](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/reg-delete)

命令文档支持语法和作用，不证明某个具体故障应当执行删除。需要当前版本或额外修复依据时重新核验官方来源。
