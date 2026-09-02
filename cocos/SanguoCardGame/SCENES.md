# 场景搭建清单

这个仓库里的 `cocos/SanguoCardGame` 只有脚本文件，没有 `.scene`/`.meta`/
`project.json`——没有 Cocos Creator 编辑器环境没法生成这些资源，需要你在本地
编辑器里按下表逐个建。

## 通用做法

延续 `provinces/ThirteenProvincesController`（已移除）确立的写法：**每个场景
只需要一个空 Canvas 节点，挂上对应的根控制器脚本**，不需要手工摆任何子节点——
顶部条、底部导航、列表、弹层全部是脚本运行时用 `UIFactory` 代码构建出来的。

新建场景步骤（每个场景重复一遍）：

1. `场景` 菜单 → 新建场景，保存为下表「场景文件名」，路径建议
   `assets/scenes/<场景文件名>.scene`
2. 场景里新建一个 `Canvas` 节点（2D UI 根，会自带 Camera）
3. Canvas 的 **Design Resolution** 设为 `1280 x 720`，Fit Height（横屏），
   和 `core/UiTheme.ts` 里的 `Theme.design` 保持一致——所有布局代码都是按这个
   基准算像素坐标的，改了这个值不会报错，但比例会跑掉
4. 把下表对应脚本组件挂到这个 Canvas 节点上
5. 场景文件名必须和 `core/SceneNav.ts` 里的常量值完全一致（区分大小写），
   否则 `SceneNav.go()` 会在控制台报「找不到场景」并停在当前界面

建完所有场景后，去 `项目设置 → 场景管理器 → 构建列表`，把它们全部加进去
（原有的 Login/MainMenu/Gacha/Battle 应该已经在列表里；这次新增的九个还没有）。

## 场景清单

| 场景文件名 (SceneNav 常量) | 挂载脚本 | 组件类名 | 说明 |
|---|---|---|---|
| `Login` | `auth/AuthController.ts` | `AuthController` | 登录 + 注册合并在一个场景内切换，取代原 `ui/LoginController.ts` |
| `MainMenu` | `hub/HubController.ts` | `HubController` | 主城，取代原 `ui/MainMenuController.ts` |
| `Gacha` | `gacha/GachaController.ts` | `GachaController` | 招贤台 |
| `Roster` | `roster/RosterController.ts` | `RosterController` | 将台（武将图鉴），新增场景 |
| `Formation` | `formation/FormationController.ts` | `FormationController` | 编伍，新增场景 |
| `Campaign` | `campaign/CampaignController.ts` | `CampaignController` | 征伐，新增场景，取代早前的 `ThirteenProvinces`（十三州地理版图，已删除） |
| `Orders` | `orders/OrdersController.ts` | `OrdersController` | 军令，新增场景 |
| `Shop` | `shop/ShopController.ts` | `ShopController` | 市集，新增场景 |
| `Guild` | `guild/GuildController.ts` | `GuildController` | 盟，新增场景 |
| `Bag` | `bag/BagController.ts` | `BagController` | 行囊，新增场景 |
| `Arena` | `arena/ArenaController.ts` | `ArenaController` | 军演，新增场景 |
| `Battle` | （不在本次改动范围内） | — | 真实战斗结算场景，由征伐页「出征」和军演跳转过去；这个场景本身没有改动，按你仓库原有的状态处理 |

## 已知需要在编辑器里核对的地方

我这边没有 Cocos 编辑器可以实际打开验证，只跑了一个语法级的 tsc 检查（能抓
括号不匹配之类的硬伤，抓不到 Cocos API 用法错不错）。进编辑器后重点看这几处：

- 各场景 `ScrollView` + `Layout`（`core/UIFactory.ts` 的 `createScrollList`）
  的裁剪区域是否正确——用的是 `Mask` + 空 `Graphics`，如果编辑器版本对
  `Mask` 的要求有出入，滚动区域可能会不裁剪或裁剪范围不对
- `EditBox`（`auth/AuthController.ts`、`guild/GuildController.ts`）在没有
  指定背景 `Sprite` 的情况下，默认外观可能和设计稿不完全一致，可以后续按需
  给 `EditBox` 组件配一张九宫格背景图
- 各处用 `Graphics.roundRect` 画的面板都是纯色，没有设计稿里的渐变/材质
  纹理——这是所有场景统一的简化处理（`UIFactory.ts` 顶部注释里写明了），
  不是漏做，后续要加渐变贴图需要额外的美术资源
- 中文竖排标题（登录页「十三州」、主城「飞将·吕奉先」）用的是多行竖排文字
  近似，不是真正的 `writing-mode: vertical-rl`，Cocos Label 不支持这个属性
