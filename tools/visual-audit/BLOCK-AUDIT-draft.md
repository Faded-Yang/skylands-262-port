# 游戏内方块渲染审计（自动判定：品红像素占比 >= 5% => missing texture）

| namespace | 已测方块 | MISSING | 占比 | 备注 |
|---|---|---|---|---|
| interiors | 53 | 0 | 0.0% | |
| createframed | 249 | 0 | 0.0% | |
| createdieselgenerators | 59 | 0 | 0.0% | |
| aeroworks | 8 | 0 | 0.0% | |
| aeronautics | 42 | 0 | 0.0% | |
| dndecor | 774 | 0 | 0.0% | |
| createdeco | 389 | 0 | 0.0% | |
| tfmg | 436 | 0 | 0.0% | |
| create_connected | 109 | 2 | 1.8% | |
| **合计** | **2119** | **2** | **0.1%** | |

## 破损清单

### create_connected
| block | 品红占比 | 格子(x,z) | 截图 |
|---|---|---|---|
| create_connected:magenta_fan_dyeing_catalyst | 25.9% | -1,0 | ..\..\work\run26\port\g300\game-vis1\shots\create_connected-b02.png |
| create_connected:brass_gearbox | 8.7% | 2,0 | ..\..\work\run26\port\g300\game-vis1\shots\create_connected-b00.png |

