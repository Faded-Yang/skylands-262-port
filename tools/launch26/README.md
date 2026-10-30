# launch26 —— MC 26.3 + Fabric 客户端启动器

> 目标：一个**可复用**的命令行启动器，能带**任意 mods 目录**启动 `MC 26.3 + Fabric Loader 0.19.5`，
> 并自带「到标题画面就自动杀进程」的验收哨兵。这是后续所有 26.3 移植验证的地基。
>
> 状态：**✅ 已验收通过** —— 2026-10-17 15:21，2 个 mod（`portprobe` + `fabric-api`）启动到标题画面，
> 用时 **15.7 s**，哨兵命中后自动杀进程树（无残留 GUI）。

---

## 1. 结论：是否成功启动到标题画面

**是。** 单次启动即通过，无返工。证据日志原文（`work\run26\test1\logs\latest.log`）：

```
[15:21:29] [main/INFO]: Loading Minecraft 26.3 with Fabric Loader 0.19.5
[15:21:29] [main/INFO]: Mappings not present!
[15:21:30] [main/INFO]: Loading 50 mods:
	- fabric-api 0.163.0+26.3
	   |-- fabric-advancement-api-v1 1.0.1+38c7a2d55d
	   ...
	   \-- fabric-transitive-access-wideners-v1 8.1.17+e2f63d3e5d
	- fabricloader 0.19.5
	   \-- mixinextras 0.5.5
	- java 25
	- minecraft 26.3
	- portprobe 1.0.0
[15:21:30] [main/INFO]: SpongePowered MIXIN Subsystem Version=0.8.7 Source=file:/C:/Users/95959/AppData/Roaming/.minecraft/libraries/net/fabricmc/sponge-mixin/0.17.4+mixin.0.8.7/sponge-mixin-0.17.4+mixin.0.8.7.jar Service=Knot/Fabric Env=CLIENT
[15:21:38] [Render thread/INFO]: [portprobe] initialised; Minecraft 26.3 (world version 5023, protocol 777, stable=true)
[15:21:39] [Render thread/INFO]: Backend library: LWJGL version 3.4.3-snapshot
[15:21:44] [Render thread/INFO]: OpenAL initialized on device OpenAL Soft on Headphone (Realtek(R) Audio)
[15:21:44] [Render thread/INFO]: Sound engine started
[15:21:44] [Render thread/INFO]: Created: 2048x2048x4 minecraft:textures/atlas/blocks.png-atlas
```

我们自己的哨兵输出：

```
[launch26] === 标题画面标记全部命中 ===
[launch26] 'Backend library:' <- [15:21:39] [Render thread/INFO]: Backend library: LWJGL version 3.4.3-snapshot
[launch26] 'Sound engine started' <- [15:21:44] [Render thread/INFO]: Sound engine started
[launch26] 'blocks.png-atlas' <- [15:21:44] [Render thread/INFO]: Created: 2048x2048x4 minecraft:textures/atlas/blocks.png-atlas
[launch26] 用时 15.7s，主动杀进程树 pid=33040
[launch26] RESULT: TITLE_SCREEN_OK
```

三条判据的分工（缺一条都不能算到标题画面）：

| 标记 | 含义 |
|---|---|
| `Backend library: LWJGL` | LWJGL/SDL 原生库加载成功（`--enable-native-access` 起作用了） |
| `Sound engine started` | OpenAL 起来了，客户端主循环已过初始化 |
| `Created: ...blocks.png-atlas` | 资源/图集烘完 = 主菜单资源全部就绪 |

**Fabric 侧也验到了**：`Loading 50 mods:` 里含 `portprobe 1.0.0`（我们自己编的 mod），
且 mod 代码真被执行（`[portprobe] initialised; ...` 这行是 mod 自己打的）。
`fabric-api` 被展开成 46 个子模块，说明 JiJ 嵌套也正常。

> 注：图集是 `2048x2048x4`，而 PCL 那次纯原版跑出的是 `4096x4096x4` ——
> 差别来自 `options.txt` 的 mipmap/资源包设置（PCL 带着资源包），不影响"到标题画面"这个判定。

---

## 2. 完整可复现命令

**一条命令就能跑**（`<PY>` = DSH 的 python，`--mods` 可省略）：

```powershell
& "C:\Users\95959\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" `
  "C:\Users\95959\OneDrive\Desktop\Work\skylands-262\tools\launch26\launch.py" `
  --game-dir "C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\test1" `
  --mods     "C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\mods-test1" `
  --watch-title --timeout 240
```

`mods-test1` 目录内容 = 验收指定的两个 jar：

```
portprobe-1.0.0.jar             2,209 B   (work\build26\build\libs\portprobe-1.0.0.jar)
fabric-api-0.163.0+26.3.jar 1,774,707 B   (work\aero-port\libs26\fabric-api-0.163.0+26.3.jar)
```

**只看命令不启动**（不下载、不写任何东西，最适合排查）：

```powershell
& "<PY>" "...\tools\launch26\launch.py" --game-dir <目录> [--mods <目录>] --dry-run
```

`--dry-run` 会打印 **可直接粘到 cmd 里跑的一整行**，同时列出"哪些库缺失、本轮会下什么"。
真实启动时这份命令还会落盘到 `<game-dir>\launch-command.txt`（便于复盘/贴进工单）。

### 命令行接口

| 参数 | 说明 |
|---|---|
| `--game-dir` | **必填**。测试用游戏目录，**所有写操作都在这里**（mods/natives/logs/launch-command.txt/launch-console.log） |
| `--mods` | mods 源目录，`*.jar` 复制进 `<game-dir>\mods`；**该目录是权威**，会清掉 game-dir 里本次没给的旧 jar |
| `--dry-run` | 只打印 argv，不下载、不启动 |
| `--watch-title` | 盯 `<game-dir>\logs\latest.log`，三条标记全中 → 打印证据 → `taskkill /F /T` 自杀进程树 → 退出码 0 |
| `--timeout` | 到标题画面的超时秒数（默认 300；超时同样杀进程，退出码 1） |
| `--mc-dir` | `.minecraft` 位置（默认 `%APPDATA%\.minecraft`，**只读**） |
| `--fabric-profile` | Fabric loader profile json（默认 `work\fabric-profile-26.3.json`） |
| `--no-fabric` | 去掉 Fabric，只跑 vanilla（对照实验用） |
| `--java` / `--natives-dir` / `--username` / `--uuid` / `--width` / `--height` / `--xmx` / `--xms` | 覆盖默认值 |
| `--extra-jvm-arg` / `--extra-game-arg` | 追加参数，可重复（做 A/B 实验用） |

退出码：`0` = 到标题画面（已杀进程）；`1` = 失败/超时（会自动 dump 控制台最后 40 行 +
`latest.log` 最后 40 行）；`2` = argparse 参数错误。

---

## 3. `launch.py` 的关键实现要点

### 3.1 怎么解析 json

```
26.3.json                          fabric-profile-26.3.json
├─ libraries[114]  → rules 过滤     ├─ libraries[7]  → 只有 maven 坐标，没有 downloads
├─ assetIndex.id = "34"            ├─ mainClass = ...knot.KnotClient
├─ mainClass = net.minecraft.client.main.Main
├─ arguments.jvm[]  → 含 -cp/--enable-native-access/-Djava.library.path
└─ arguments.game[] → 含 --username/--gameDir/--assetIndex...  + 带 rules 的可选块
```

* **`rules` 求值**（`rules_allow()`）：空 rules ⇒ 允许；否则**默认拒绝**，按顺序逐条匹配
  （`os.name` / `os.arch` / `os.version` 正则 / `features` 全等），最后一条命中的 `action`
  决定结果。本启动器把 `features` 全置 false ⇒ `--demo` / `--width` 的自定义分辨率块 /
  `--quickPlay*` 全部自动跳过。**`--quickPlay` 完全没有用到**，不需要它来跳过什么。
* **`arguments` 是混合数组**（`flatten_args()`）：元素可能是裸字符串，也可能是
  `{rules, value}`（value 又是 str 或 list）—— 逐条求 rules、展开、再统一做占位符替换。
* **`${placeholder}` 替换**：`auth_player_name / version_name / game_directory / assets_root /
  assets_index_name / auth_uuid / auth_access_token / clientid / auth_xuid / version_type /
  natives_directory / launcher_name / launcher_version / classpath / resolution_*`。
  `clientid` 与 `xuid` 传**空串**（离线启动，官方 launcher 也这么传），不会解析失败。
* `assetIndex.id = 34` → `--assetIndex 34`，`--assetsDir <mc>\assets`（`assets/indexes/34.json` 已存在）。
* **log4j**：从 `logging.client.file.id` 取出 `client-1.21.2.xml`，用
  `assets\log_configs\client-1.21.2.xml` 拼 `-Dlog4j.configurationFile=...`。
  （若该文件不存在，会把它下载到 `<game-dir>\log_configs\` —— 不往 `.minecraft` 写。）

### 3.2 怎么合并 Fabric

* `mainClass` 直接**覆盖**为 `net.fabricmc.loader.impl.launch.knot.KnotClient`。
* Fabric 的 7 个库**没有 `downloads.artifact`**，只有 `name` + `url`（`https://maven.fabricmc.net/`），
  所以按 maven 布局自己拼：`g:a:v` → `g/a/v/a-v.jar`，完整 URL = `url + 相对路径`
  （`maven_to_path()`）。带 classifier 的 `g:a:v:cls` 也支持。
* Fabric profile 的 `arguments.jvm` = `["-DFabricMcEmu= net.minecraft.client.main.Main "]`
  **原样保留**（注意它自带尾部空格，作为一个 argv 元素传，不要被 shell 拆开）。
* 额外补两条：`-Dfabric.gameVersion=26.3`、`-Dfabric.development=false`。

### 3.3 怎么下缺库

```
for lib in filtered_libraries:                    # vanilla 的 path 用 downloads.artifact.path
    local = <mc>\libraries\<path>                 # fabric 的 path 由 maven_to_path 算
    if local.is_file() and size>0: 用现成的
    else: download(url → local.part) → 校验 sha1/size → rename 到 local
```

* 先写 `*.part` 再原子 rename，半截文件不会被下次当成"已存在"。
* **有 sha1 就校验**（vanilla 全有；Fabric 的 7 个里 6 个有，`fabric-loader` 那个没有就只校验存在性）。
* `natives-windows-arm64` 这类**异架构包会被主动剔掉**：26.3.json 里它们的 rules 只写了
  `os.name=windows`，官方那条 rules 过滤放不过它们；而 arm64 包里 dll **同名**（`lwjgl.dll`），
  一旦排在 classpath 前面被共享库加载器抽出来就会 `0xc000007b`。⇒ rules 之后按名字再补一刀
  （`is_foreign_arch_natives()`）。
* `--dry-run` 时 `allow_download=False`：只把缺的列进 `downloaded_missing`，一个字节都不写。

### 3.4 classpath 怎么拼

```
<mc>\libraries\<path1>;<path2>;...;<pathN>;<mc>\versions\26.3\26.3.jar
```

* 顺序：**先用 vanilla 的 71 条**（rules + arch 过滤后；原始 114 条），**再接 Fabric 的 7 条**，
  **最后**才是 `26.3.jar`。`;` 分隔（Windows）。
* 用 `dict` 按 path 去重（`setdefault`）⇒ 同一个 jar 不会进两次；Fabric 侧同名库也自动合并。
* 实测 `classpath_entry_count = 72`（71 库 + 1 client jar）。

### 3.5 natives 与 `--enable-native-access`

* `26.3-natives\` 里是**已解包**的 dll（`jna\`、`lwjgl\3.4.3+4\x64\`、`netty\`）**没有** `java\`
  子目录 —— 也就是说 vanilla 那条 `-Djava.library.path=${natives_directory}/java` 指向的目录
  本来就不存在，库实际靠 LWJGL 的 `SharedLibraryExtractPath` 抽。
* 但 `-Dorg.lwjgl.system.SharedLibraryExtractPath` / `-Djna.tmpdir` /
  `-Dio.netty.native.workdir` **都指向 natives 目录内部** ⇒ 直接用 `.minecraft` 那份等于往里写。
  所以：**把 `26.3-natives` 整树复制到 `<game-dir>\natives`**（22 个文件），
  再把四个 `-D` 全部改指这份拷贝。`.minecraft` 保持只读。
* `-Djava.library.path` 额外兜底：拼上 `<natives>\java` + **所有含 `*.dll` 的目录**
  （实测就是 `natives\lwjgl\3.4.3+4\x64`）。
* `--enable-native-access=ALL-UNNAMED`（Java 25 / JEP 472）：26.3.json 里**已经带了**，
  本启动器**去重后再保底追加一次**（`any(a.startswith("--enable-native-access"))` 判断），
  保证旧 json 也能跑。**没有它 LWJGL 直接起不来**（native 访问被拒）。

### 3.6 哨兵（自动收尾）

后台读 `<game-dir>\logs\latest.log`（启动前先删掉，避免命中上一轮残留），边读边转发到 stdout，
三条标记齐了 → 打印原文证据 → `taskkill /F /T /PID <pid>` → 退出码 0。
进程自己先退（崩溃）或超时 → dump 最后 40 行然后退出码 1。**不会留下挂着的 GUI。**

> 思路参考 [`minecraft-launcher-lib`](https://codeberg.org/JakobDev/minecraft-launcher-lib)（JakobDev, MIT）
> 的 `command.py`：rules 过滤库、拼 classpath、逐条替换 `${placeholder}` 的骨架与它一致。
> 本实现在此基础上自写了：arch 级 natives 过滤、sha1 校验 + `.part` 原子下载、
> natives 目录隔离、标题画面哨兵、`--dry-run` 与失败 dump。

---

## 4. 启动过程中遇到的所有报错原文

**除了下面这 3 条"预期内"的噪声，没有任何报错。没有崩溃报告，没有 red 级 Fabric 报错。**

### 4.1 `Failed to fetch user properties` 401（离线登录，预期）

```
[15:21:39] [Download-2/ERROR]: Failed to fetch user properties
com.mojang.authlib.exceptions.InvalidCredentialsException: Status: 401
	at knot//com.mojang.authlib.exceptions.MinecraftClientHttpException.toAuthenticationException(MinecraftClientHttpException.java:70)
	at knot//com.mojang.authlib.services.MinecraftServicesUserApiService.fetchProperties(MinecraftServicesUserApiService.java:168)
	at knot//net.minecraft.client.Minecraft.lambda$new$1(Minecraft.java:451)
	...
Caused by: MinecraftClientHttpException[type=HTTP_ERROR, status=401, response=ErrorResponse[path=/player/attributes, error=null, errorMessage=null, details=null]]
```

原因：`--accessToken 0` 是假 token。**不影响进标题画面**（只是拿不到皮肤/玩家属性）。
真要正版登录再起，得换成真 token。

### 4.2 `Realms authentication error ... Failed to parse into SignedJWT: 0`（同上，预期）

```
[15:21:41] [Download-1/INFO]: Could not authorize you against Realms server: java.lang.RuntimeException: Failed to parse into SignedJWT: 0
[15:21:41] [Download-1/ERROR]: Failed to fetch Realms feature flags
com.mojang.realmsclient.exception.RealmsServiceException: Realms authentication error with message 'java.lang.RuntimeException: Failed to parse into SignedJWT: 0'
	at knot//com.mojang.realmsclient.client.RealmsClient.execute(RealmsClient.java:625)
	...
```

原因：假 token 解不出 JWT。**只影响 Realms 按钮**，不影响标题画面。

### 4.3 `Mappings not present!`（INFO 级，不是错）

```
[15:21:29] [main/INFO]: Mappings not present!
```

这条是 **INFО 不是报错**，而且**正是我们想要的**：26.3 完全未混淆（真名），
不需要 intermediary/yarn，Fabric 也就没有映射可加载。**它意味着不需要 remap。**

### 4.4 环境噪声（与本启动器无关）

* `PowerShell` 侧曾出现一次 `Copy-Item: 找不到路径 ...portprobe-1.0.0.jar` ——
  OneDrive 按需同步的瞬时不可读，**重试即成功**，与本启动器无关。
* 我们自己脚本第一版有个 Python 警告 `SyntaxWarning: invalid escape sequence '\.'`（docstring 里
  `%APPDATA%\.minecraft`），已修（docstring 改 raw string）。

---

## 5. 有没有需要额外下载的库

**有，且只有 2 个**（第一次真启动时自动下完，共 ~3.4 MiB）：

| 库 | 落盘位置 | 大小 | 来源 |
|---|---|---|---|
| `net.fabricmc:fabric-loader:0.19.5` | `<mc>\libraries\net\fabricmc\fabric-loader\0.19.5\fabric-loader-0.19.5.jar` | 1.9 MiB | `https://maven.fabricmc.net/` |
| `net.fabricmc:sponge-mixin:0.17.4+mixin.0.8.7` | `<mc>\libraries\net\fabricmc\sponge-mixin\0.17.4+mixin.0.8.7\sponge-mixin-0.17.4+mixin.0.8.7.jar` | 1.5 MiB | `https://maven.fabricmc.net/` |

* Fabric 另外 5 个库（`asm{,-analysis,-commons,-tree,-util}:9.10.1`）**本地已有**（PCL 之前拉过）。
* **vanilla 的 114 条库一条都没缺**，`26.3.jar` 也在（40 MB），素材 `assets\indexes\34.json` 齐全。
* ⚠ **诚实披露**：这 2 个 jar 是**新增文件**（不是覆盖），落在 `<mc>\libraries\` 里 ——
  这正是任务第 3 条要求的"缺库拉到正确位置"。除此之外**对 `.minecraft` 零写入**：
  26.3.json / 26.3.jar / 26.3-natives / assets / 存档 / options.txt 全部未改动。
  所有其它写入都在 `--game-dir` 内（`mods\`、`natives\`、`logs\`、`options.txt`、`saves\` 等）。

---

## 6. 复现记录（两次运行）

| # | gameDir | mods | 结果 | 备注 |
|---|---|---|---|---|
| 1 | `work\run26\test1` | portprobe + fabric-api | **TITLE_SCREEN_OK**，15.7 s | 首次即通过；本轮下载 2 个库 |
| 2 | `work\run26\test2-nomods` | 无 | **TITLE_SCREEN_OK**，15.7 s | 换目录 + 不带 mods，验幂等/可复用；`downloaded_missing: []`（**0 下载**） |

第 2 次的证据行（`Loading 4 mods` = 只剩 Fabric 自身 + java + minecraft，没有第三方 mod）：

```
[15:21:58] [main/INFO]: Mappings not present!
[15:21:58] [main/INFO]: Loading 4 mods:
[15:22:08] [Render thread/INFO]: Backend library: LWJGL version 3.4.3-snapshot
[launch26] === 标题画面标记全部命中 ===
[launch26] 用时 15.7s，主动杀进程树 pid=21980
[launch26] RESULT: TITLE_SCREEN_OK
```

⇒ 同一目录二次启动**不会重复下载**（库已就位就跳过），换 `--game-dir` 也能独立工作：
**启动器是可复用的**，不是一次性脚本。

两次运行均无残留 java 进程（`Get-Process java` 为空）。

## 7. 已知坑（给后续移植用）

1. **必须带 `--enable-native-access=ALL-UNNAMED`**（26.3.json 已自带，但自己拼命令时容易漏）——
   Java 25/JEP 472 下漏了 LWJGL 直接挂。
2. **natives 目录不能直接指 `.minecraft` 那份** —— 四个 `-D...tmpdir/extractpath` 会往里写。
   要么复制（本启动器做法），要么把 `-D` 全改到别处。
3. **`natives-windows-arm64` 这类异架构包必须在 classpath 上剔掉**（rules 拦不住，dll 同名会打架）。
4. **lwjgl 报 `3.4.3-snapshot`** 而 PCL 那次报 `3.4.3+4` —— 同一组 3.4.3 jar，只是 LWJGL 从
   jar 里读到的 build 标记不同。功能无差别（`SDL3.dll` / `shaderc` / `vma` 全部正常加载）。
5. **`-DFabricMcEmu= net.minecraft.client.main.Main `** 自带尾随空格，必须作为**单个 argv**
   传；拼成一行 cmd 字符串时会多出一个空格分词，粘到 cmd 里跑要留意。
6. Fabric 的 `Mappings not present!` 是**正常**的（26.3 未混淆）。看到它不要以为是换了 mapping 出问题。
