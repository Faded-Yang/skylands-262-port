# 交付件清单（mods-stable，118 jar）

> **本文件只登记清单与指纹，不含 jar 本体。** 本仓库是公开仓库，按许可证与体积要求不发布任何 mod jar、游戏资源或反编译代码。
> 生成方式：遍历 `work/run26/mods-stable/*.jar`（2026-10-30 快照），逐文件计算 SHA-256 取前 16 位。
> 要重建整合包，请按本表自行合法获取对应 mod；自研件用 `tools/pack_jar.py` 打包。

## 汇总

| 类别 | jar 数 | 合计字节 | 含义 |
|---|---:|---:|---|
| 26.3 原生构建 | 38 | 47,897,617 | 上游已发布 26.3 构建，直接安装，未改字节码 |
| 自移植核心 | 8 | 82,124,899 | 上游无 26.3 构建，由我们源码级重建或字节码补丁（Create 栈支柱件） |
| 移植成功 | 51 | 40,481,067 | 上游 mod 经改造/重打数据后在 26.3 可用（含 reduced 降级件） |
| 自建辅助 | 17 | 1,247,034 | 无上游对应物的自研件：数据包、修补件、任务/喷气背包/浮岛世界类型、兼容垫片 |
| 上游直装 | 4 | 2,056,893 | 上游件原样放入，但构建目标不是 26.3（跨版本兼容），仅 UI/结构类 |
| **合计** | **118** | **173,807,510**（165.8 MiB） | — |

## 明细

| # | 文件名 | 字节 | SHA-256（前 16 位） | 类别 |
|---:|---|---:|---|---|
| 1 | `appleskin-fabric-mc26.3-3.0.10.jar` | 177,859 | `004b19a812a272bb` | 26.3 原生构建 |
| 2 | `architectury-fabric-22.0.5.jar` | 622,542 | `c6a60979f75fdf07` | 26.3 原生构建 |
| 3 | `BadOptimizations-2.4.1-26.3-fabric.jar` | 60,760 | `b72d071777ebf832` | 26.3 原生构建 |
| 4 | `balm-fabric-26.3-26.3.0.3.jar` | 1,196,622 | `7981ef00a23dd2c6` | 26.3 原生构建 |
| 5 | `BetterF3-20.0.0-Fabric-26.3.jar` | 719,577 | `e3ae4820dbbed0cd` | 26.3 原生构建 |
| 6 | `Chunky-Fabric-1.5.3.jar` | 354,095 | `ecdfc55a0f67f3ec` | 26.3 原生构建 |
| 7 | `cloth-config-fabric-26.3.159.jar` | 1,123,162 | `7b4f1a042b920f93` | 26.3 原生构建 |
| 8 | `Clumps-fabric-26.3-26.3.2.jar` | 20,154 | `8c72b1505a11ad93` | 26.3 原生构建 |
| 9 | `Controlling-fabric-26.3-26.3.4.jar` | 87,230 | `5035cb0b29ad3b2e` | 26.3 原生构建 |
| 10 | `cristellib-fabric-26.3-3.1.13.jar` | 588,323 | `69e03ac9c1bf853f` | 26.3 原生构建 |
| 11 | `dynamic-fps-3.11.10+minecraft-26.3.0-fabric.jar` | 189,474 | `a186d7cdfa373893` | 26.3 原生构建 |
| 12 | `fabric-api-0.163.0+26.3.jar` | 1,774,707 | `4969f5197ebedaf6` | 26.3 原生构建 |
| 13 | `fabric-language-kotlin-1.14.2+kotlin.2.4.21.jar` | 8,142,878 | `fbdbf5286ab9d65f` | 26.3 原生构建 |
| 14 | `FarmersDelight-26.3-3.6.28+refabricated.jar` | 3,451,494 | `239e3cdbc3c130d3` | 26.3 原生构建 |
| 15 | `ferritecore-9.0.0-fabric.jar` | 72,677 | `213966c72ed967ac` | 26.3 原生构建 |
| 16 | `ForgeConfigAPIPort-v26.3.1-mc26.3.x-Fabric.jar` | 608,240 | `9d0ca9dc75c0a191` | 26.3 原生构建 |
| 17 | `Geophilic v3.7.mod.jar` | 1,115,993 | `9e6a98b438e078f2` | 26.3 原生构建 |
| 18 | `ImmediatelyFast-Fabric-1.17.1+26.3.jar` | 99,586 | `4b346661cd0811d9` | 26.3 原生构建 |
| 19 | `InventoryProfilesNext-fabric-26.3-2.3.8.jar` | 1,513,083 | `91a8102a9bb0e525` | 26.3 原生构建 |
| 20 | `iris-fabric-1.11.7+mc26.3.jar` | 2,832,426 | `ff32327e33fc24c2` | 26.3 原生构建 |
| 21 | `Jade-mc26.3-Fabric-26.3.5.jar` | 1,083,003 | `4d66516235b239fd` | 26.3 原生构建 |
| 22 | `jei-26.3-fabric-31.15.0.79.jar` | 2,385,971 | `1397e87f05c6c705` | 26.3 原生构建 |
| 23 | `libIPN-fabric-26.3-6.9.0.jar` | 652,221 | `a6dab8749a8931a0` | 26.3 原生构建 |
| 24 | `lithium-fabric-0.26.2+mc26.3.jar` | 914,543 | `0be5b17ef9f6e924` | 26.3 原生构建 |
| 25 | `lithostitched-2.0.6-fabric-26.3.jar` | 997,092 | `31c5fff53420a2af` | 26.3 原生构建 |
| 26 | `MoogsStructureLib-fabric-26.3-3.4.2.jar` | 1,093,979 | `d0b018013bd8abba` | 26.3 原生构建 |
| 27 | `moreculling-fabric-26.3-1.9.0.jar` | 294,320 | `4739cf1bba326d53` | 26.3 原生构建 |
| 28 | `MouseTweaks-fabric-mc26.3-2.31.jar` | 74,569 | `7fa35df568c870c4` | 26.3 原生构建 |
| 29 | `PacketFixer-fabric-3.3.6.jar` | 32,477 | `719eef9de881151e` | 26.3 原生构建 |
| 30 | `Searchables-fabric-26.3-1.0.3.jar` | 79,857 | `63747116b8903a6e` | 26.3 原生构建 |
| 31 | `shogi-fabric-26.3-26.3.0.3.jar` | 464,910 | `3af6e97408d52e9f` | 26.3 原生构建 |
| 32 | `sodium-fabric-0.9.3-beta.1+mc26.3.jar` | 1,900,046 | `d9cbb7d3d4e6e2b2` | 26.3 原生构建 |
| 33 | `spark-1.10.187-fabric.jar` | 3,838,499 | `3fc00663caa542b1` | 26.3 原生构建 |
| 34 | `Structory_26.3_v1.3.18+26.3.jar` | 1,261,901 | `27f8a13e26c24144` | 26.3 原生构建 |
| 35 | `t_and_t-fabric-neoforge-1.13.12.jar` | 3,195,626 | `a5ca864106daa500` | 26.3 原生构建 |
| 36 | `waystones-fabric-26.3-26.3.0.1.jar` | 1,205,181 | `aece9c10d09c22d7` | 26.3 原生构建 |
| 37 | `xaerominimap-fabric-26.3-26.6.0.jar` | 2,196,491 | `8ff662f8cf0e1aab` | 26.3 原生构建 |
| 38 | `xaeroworldmap-fabric-26.3-1.47.0.jar` | 1,476,049 | `a2e255db8fd5918f` | 26.3 原生构建 |
| 39 | `aeronautics-fabric-0.1.0-port.26.3.jar` | 31,612,206 | `7d877f79dcafb4d1` | 自移植核心 |
| 40 | `cei-2.5.2c-26.3-src.jar` | 816,449 | `9ccc31c33f93bc8f` | 自移植核心 |
| 41 | `create-fly-26.2-6.0.9-2-26.3-patched.jar` | 19,677,550 | `ceab8ec48d84bb53` | 自移植核心 |
| 42 | `dp-1.11.4p1-26.3-src.jar` | 533,695 | `621af2ff5c90f568` | 自移植核心 |
| 43 | `natures_spirit-fabric-2.3.0-26.3-nsB2.jar` | 18,807,697 | `d804b8a109140c1a` | 自移植核心 |
| 44 | `sable-fabric-26.3.jar` | 9,375,058 | `3f315c2649b9a7d7` | 自移植核心 |
| 45 | `sablecompanion-1.6.0-26.3.jar` | 28,732 | `0eaf551099c0d0fc` | 自移植核心 |
| 46 | `yungsapi-26.3-src.jar` | 1,273,512 | `2aff3b4198df5e06` | 自移植核心 |
| 47 | `chefsdelight-1.0.6-26.3.jar` | 119,475 | `d3f449d5b318004c` | 移植成功 |
| 48 | `constraintfix-1.6.0-26.3.jar` | 23,430 | `7362081e176e5a50` | 移植成功 |
| 49 | `corndelight-1.0.0-26.3.jar` | 121,298 | `356f49472f32888c` | 移植成功 |
| 50 | `create_sky_village-0.0.29I-26.3.jar` | 2,474,580 | `0c736602cd46510e` | 移植成功 |
| 51 | `createaddition-1.3.4-26.3.jar` | 1,438,512 | `71e01d397997e567` | 移植成功 |
| 52 | `createframed-1.7.3-26.3.jar` | 1,182,950 | `c4db59d2225ef945` | 移植成功 |
| 53 | `DungeonsArise-2.1.68-26.3.jar` | 11,845,448 | `63889f393b2e8fa8` | 移植成功 |
| 54 | `ends_delight-2.6-26.3.jar` | 235,400 | `294399423ba52d4e` | 移植成功 |
| 55 | `escalated-1.2.1-26.3.jar` | 431,971 | `62fac2bedc6cc5ed` | 移植成功 |
| 56 | `imst-2.2.1c-26.3.jar` | 426,929 | `dbf9e3e3ed9b0fa0` | 移植成功 |
| 57 | `interiors-0.6.0-26.3.jar` | 494,562 | `333af994a7e1a8a9` | 移植成功 |
| 58 | `JadeAddons-6.1.2-26.3.jar` | 21,548 | `ed3dc4942012468a` | 移植成功 |
| 59 | `MoogsSoaringStructures-2.2.0-26.3.jar` | 5,013,684 | `bb1b65ece6524213` | 移植成功 |
| 60 | `no_void_structures-2.0.1-26.3.jar` | 10,655 | `987989bcd8445634` | 移植成功 |
| 61 | `passivemobspawn-1.0.0-26.3.jar` | 13,182 | `86e1de160fb91643` | 移植成功 |
| 62 | `rabbit_pathfinding_fix-1.0.5-26.3.jar` | 17,662 | `149461f241f7585e` | 移植成功 |
| 63 | `sablejade-1.3.0-26.3.jar` | 296,234 | `a33f6b4adfc1afdc` | 移植成功 |
| 64 | `sablephysicscompat-1.3.0-26.3.jar` | 25,653 | `e14f03286ce1e426` | 移植成功 |
| 65 | `sky262-abnormalsdelight-6.0.3-26.3-reduced.jar` | 121,110 | `a7f6fbeefd213b8c` | 移植成功 |
| 66 | `sky262-aerocopycats-1.1.1.jar` | 9,587 | `eec29ac0825f6f5e` | 移植成功 |
| 67 | `sky262-aeroworks-1.5.0.jar` | 131,738 | `a5c98b2630f7d86c` | 移植成功 |
| 68 | `sky262-awakened-islands-1.0.0.jar` | 9,607 | `4e14bc6f4cf152dc` | 移植成功 |
| 69 | `sky262-central-kitchen-2.6.2-beta-port.1.jar` | 71,337 | `665d3a909f4e926e` | 移植成功 |
| 70 | `sky262-copycats-reduced-0.1.0.jar` | 53,833 | `0c1761e6b9af575b` | 移植成功 |
| 71 | `sky262-create-connected-1.3.3-b2.jar` | 320,380 | `a07e869970d61585` | 移植成功 |
| 72 | `sky262-create-hangars-1.0.0.jar` | 417,406 | `9bf2ea54a9d2a63b` | 移植成功 |
| 73 | `sky262-create-submarine-3.3.0.jar` | 414,908 | `1092c34052d7df5d` | 移植成功 |
| 74 | `sky262-createdeco-2.1.3-beta-port.21.jar` | 1,488,121 | `a190b39bfb29e520` | 移植成功 |
| 75 | `sky262-createpropulsion-1.1.5.jar` | 373,056 | `18ecbc810bc7fa4b` | 移植成功 |
| 76 | `sky262-culturaldelights-0.17.7-26.3-reduced.jar` | 164,306 | `7ebe6a64c8dbdb3b` | 移植成功 |
| 77 | `sky262-design-n-decor-2.2b-beta-port.32.jar` | 4,568,121 | `391e0ecd2a4697ba` | 移植成功 |
| 78 | `sky262-diesel-generators-1.3.15-beta-port.3.jar` | 1,225,464 | `f22a18efed49058e` | 移植成功 |
| 79 | `sky262-mechanical-extruder-2.2.2-beta-port.7.jar` | 33,707 | `889af406f57ffbb8` | 移植成功 |
| 80 | `sky262-minersdelight-1.4.5-26.3-reduced.jar` | 148,169 | `cf220ed171f0cb0b` | 移植成功 |
| 81 | `sky262-mynethersdelight-2.0.4-26.3-reduced.jar` | 329,824 | `c4a9f3fd2479e626` | 移植成功 |
| 82 | `sky262-no-void-structures-2.0.1.jar` | 184,591 | `b1712dbc4875a99a` | 移植成功 |
| 83 | `sky262-offroad-1.0.0.jar` | 54,644 | `6ee2721f6ff4be50` | 移植成功 |
| 84 | `sky262-ore-excavation-1.6.8.jar` | 91,095 | `80f8a0b1e8998b1b` | 移植成功 |
| 85 | `sky262-power-loader-2.0.5-beta-port.5.jar` | 78,058 | `9d9793e1739fbae2` | 移植成功 |
| 86 | `sky262-sliceanddice-4.3.4.jar` | 49,694 | `31176950ff2d726c` | 移植成功 |
| 87 | `sky262-sophisticated-backpacks-3.26.12-b2.jar` | 148,657 | `bf00a9ee0dd7473d` | 移植成功 |
| 88 | `sky262-sophisticated-storage-1.6.7-b8.jar` | 215,958 | `79d5fd76ae7f18e2` | 移植成功 |
| 89 | `sky262-tfmg-1.2.0-26.3-b5.jar` | 2,579,152 | `22dde8dde39e27eb` | 移植成功 |
| 90 | `sky262-throwable-rope-connector-0.4.3.jar` | 29,452 | `463859a67dbedcec` | 移植成功 |
| 91 | `sky262-toolgun-1.0.0.jar` | 152,415 | `773fcbd94626f802` | 移植成功 |
| 92 | `sky262-transmission-linkage-0.2.8.jar` | 70,384 | `737d4b87e8d5abb0` | 移植成功 |
| 93 | `sky262-waystonessable-1.0.7.jar` | 3,415 | `cfd8caba260578ac` | 移植成功 |
| 94 | `SkyVillages-1.0.6-26.3.jar` | 187,930 | `f4e1f1ac1b5007b2` | 移植成功 |
| 95 | `strayed-fates-forsaken-2.0.0.2-26.3.jar` | 2,300,908 | `4d90b4339a8d7ce5` | 移植成功 |
| 96 | `Structory_Towers-1.0.17-26.3.jar` | 252,533 | `b51c7aa4150e997c` | 移植成功 |
| 97 | `structures-1.2-26.3.jar` | 8,334 | `593539b2bd8814b7` | 移植成功 |
| 98 | `sky262-aero-recipes-1.0.8.jar` | 158,723 | `2c8fe78f5cf95bc5` | 自建辅助 |
| 99 | `sky262-aeronauticscompat-1.1.3.jar` | 2,366 | `14cf9829c5babe02` | 自建辅助 |
| 100 | `sky262-audit-items-0.1.0.jar` | 2,489 | `f01e37c41ef276c7` | 自建辅助 |
| 101 | `sky262-create-extra-recipes-1.0.1.jar` | 8,533 | `5e04690e662b77bf` | 自建辅助 |
| 102 | `sky262-create-recipes-6.0.9-2-26.3.jar` | 801,486 | `ba7eb2a32b9d4ff9` | 自建辅助 |
| 103 | `sky262-create-seqassembly-1.0.3.jar` | 2,169 | `87035537c46419a4` | 自建辅助 |
| 104 | `sky262-createfix-0.1.0-26.3.jar` | 2,557 | `07483a416e5c51e5` | 自建辅助 |
| 105 | `sky262-createliquidfuel-3.0.0-26.3-shell.jar` | 1,165 | `f2a44bd0d13f7f0f` | 自建辅助 |
| 106 | `sky262-doorfix-0.1.0.jar` | 2,773 | `8ab1f1c7960c47f9` | 自建辅助 |
| 107 | `sky262-jetpack-1.0.0.jar` | 21,343 | `11a738db6ab0135d` | 自建辅助 |
| 108 | `sky262-mechanicals-1.1.6.jar` | 77,522 | `f88a00aee39ce61e` | 自建辅助 |
| 109 | `sky262-offroad-lootfix-1.0.0.jar` | 1,837 | `41a5ded277476dbf` | 自建辅助 |
| 110 | `sky262-portable_engine_liquid_fuel-2.0.0-26.3-shell.jar` | 1,342 | `544a08177e3988c9` | 自建辅助 |
| 111 | `sky262-preset-1.0.0.jar` | 6,127 | `ecfc6034c9c5fe4a` | 自建辅助 |
| 112 | `sky262-quests-1.6.0.jar` | 126,345 | `86900d5b4d6d6507` | 自建辅助 |
| 113 | `sky262-sable-createaddition-compat-0.1.13.jar` | 21,744 | `21c75509d0716fa9` | 自建辅助 |
| 114 | `sky262crashfix-1.0.5.jar` | 8,513 | `8f8b6b08cb1500b0` | 自建辅助 |
| 115 | `Explorify v1.6.5.mod.jar` | 756,890 | `83de0f1e6319f818` | 上游直装 |
| 116 | `medieval_buildings-fabric-26.1.2-1.2.0.jar` | 217,047 | `0147f9ea171537f9` | 上游直装 |
| 117 | `modmenu-21.0.0.jar` | 853,276 | `62a9c57569d30863` | 上游直装 |
| 118 | `Paxi-26.1.2-Fabric-6.1.0.jar` | 229,680 | `3528b69844420aa5` | 上游直装 |

## 说明与口径

- **版本坐标**：MC 26.3（官方未混淆）/ Fabric Loader 0.19.5 / Java 25；交付状态见 `docs/release-1.0.7.md`。
- **118 个 jar = 118 个不同 mod id**（`docs/release-1.0.7.md` 的验收口径）；mod 项计数（含 Fabric API 子模块）与 jar 数不是同一口径。
- **分类依据**：文件名与版本号 + `docs/DELIVERY.md` §2 的来源说明 + `docs/port-*.md` 的移植记录；跨类件按**主要来源**归类（例：`sky262-toolgun` 是 aero toolgun 的重写 → 移植成功；`sky262-mechanicals` 是共享库 → 自建辅助）。
- **SHA-256 只取前 16 位**用于人工核对；要逐字节校验请对同一文件重算完整摘要。
- **不做任何 jar 分发**：本表不含下载地址，也不代表我们有权再分发这些二进制。
