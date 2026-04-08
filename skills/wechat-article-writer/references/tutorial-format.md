# Knowledge Planet (知识星球) Tutorial Format

## When to Use

When user says "写教程", "写知识星球教程", "给会员写个配置教程", or asks for ultra-simplified instructions.

## Key Differences from Articles

| Aspect | Article | Tutorial |
|--------|---------|----------|
| Tone | Conversational, essay-like | Direct, imperative |
| Emojis | Forbidden | Numbers only (1️⃣ 2️⃣ 3️⃣) |
| Length | Detailed explanations | Minimal, action-only |
| Code | With context, minimal | Exact copy-paste snippets |
| Verification | Not needed | Required visual check |

## Tutorial Template

```markdown
# [指标名称] - 安装教程

## 下载文件
解压后得到：`[filename].py`

## 安装步骤（2步搞定）

### 1️⃣ 放文件
把`[filename].py`复制到：
你的项目/core/indicators/

### 2️⃣ 加配置
打开文件：`core/charts/enhanced_chart_widget.py`

找到`EXTENDED_INDICATORS_CONFIG`字典（约50行），添加配置：

**主图指标**：
```python
"[indicator_key]": {
    "module": "[module_name]",
    "class": "[ClassName]",
    "type": "main",
    "default_visible": False,
    "configurable": True,
},
```

**副图指标**：
```python
"[indicator_key]": {
    "module": "[module_name]",
    "class": "[ClassName]",
    "type": "sub",
    "default_visible": False,
    "min_height": 100,
    "max_height": 150,
    "configurable": True,
},
```

### 3️⃣ 重启
```bash
python main.py
```

## 验证
打开图表，在指标控制面板看到 **[indicator_key]** 复选框，就成功了！

## 遇到问题
留言或私信我。
```

## Rules

- 2 steps minimum, 3 steps maximum
- Use emoji numbers 1️⃣ 2️⃣ 3️⃣ for step markers
- Each step 1-2 lines max, no explanations
- Include visual verification at the end
- NO conversational prose - pure action instructions
- Config snippets are exact copy-paste, no placeholders
