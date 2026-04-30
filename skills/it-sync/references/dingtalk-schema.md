# 钉钉 AI 表格 —— 项目整体进度表 Schema

## Base & Table

- Base ID: `pYLaezmVNe1Ql0r1Tkax5x1GWrMqPxX6`
- Table ID: `2vegybbg9tgmaki5ie3sh`

## 字段映射

| 字段名 | fieldId | 类型 | 说明 |
|--------|---------|------|------|
| 项目名称 | `h3ksjh8u63ia7tvkfq63r` | text | 项目标题 |
| 项目组 | `rvwsdq0luxq9kg84mt5hr` | singleSelect | `业务系统组` / `数据效能组` |
| 业务线 | `EYiSjyR` | singleSelect | `ERP` / `业财一体化` / `智能决策` |
| 当前阶段 | `XZkJYFz` | singleSelect | `已完工` / `开发中` / `未开始` / `设计中` |
| 当前进度 | `7x7571mgv8qra9q732zuo` | number | 百分比（0~1） |
| 优先级 | `wfppws6aj7ftqyu13rp9u` | text | 高/中/低 |
| 项目负责人 | `8I3CNfc` | singleSelect | 唐耀星/龚宏飞/佘溢钶/邹凯平/李铭发/林小鹏/赖武法/张嘉强 |
| 项目目标 | `uyqehlo2ap4g2439umilt` | text | 项目目标描述 |
| 计划开始日期 | `on2zyi96hqbraztc6qrfp` | date | YYYY-MM-DD |
| 计划结束日期 | `qiy2q0y93ap9i3mylxkhb` | date | YYYY-MM-DD |
| 是否延期 | `xrgcre7cnam74vitkqm0o` | singleSelect | `是` / `否` |
| 延期原因 | `loq0uvrlpks1is28teq6o` | text | 延期说明 |
| 版本 | `IKcjgIW` | text | 版本号 |
| 是否完工 | `QY4chlX` | singleSelect | `是` / `否` |

## 数据处理规则

1. **活跃项目过滤**：`当前阶段` 不是 `已完工` 的记录
2. **分组维度**：按 `项目组` 分为轨道一（业务系统组）和轨道二（数据效能组）
3. **排序**：延期项目优先 → 按计划结束日期升序
4. **进度显示**：`当前进度` 字段为小数（如 0.2），展示时转为百分比（20%）
5. **日期格式**：API 返回 `2026-05-15T00:00:00+08:00`，取日期部分 `2026-05-15`
