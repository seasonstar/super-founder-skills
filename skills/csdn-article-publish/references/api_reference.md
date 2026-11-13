# CSDN Blog API Reference

## API Endpoint

- **URL**: `https://bizapi.csdn.net/blog-console-api/v3/mdeditor/saveArticle`
- **Method**: POST
- **Content-Type**: application/json

## Request Headers

备注：可以使用浏览器开发者工具中，先尝试保存一次草稿状态的文章的操作后，从请求头中进行获取
| Header | Required | Description |
|--------|----------|-------------|
| Cookie | Yes | 用户登录Cookie |
| x-ca-nonce | Yes | UUID字符串 |
| x-ca-signature | Yes | Base64签名 |
| x-ca-signature-headers | Yes | 签名头列表，如 "x-ca-key,x-ca-nonce" |
| x-ca-key | Yes | API Key |

## Request Body Fields

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| id | Update Only | - | 文章ID，更新时必需 |
| title | Yes | - | 文章标题 |
| content | Yes | - | HTML 格式正文内容 |
| markdowncontent | Yes | - | Markdown格式文章内容 |
| pubStatus | No | draft | 发布状态: draft/publish |
| readType | No | public | 可见范围 |
| type | No | original | 文章类型 |
| tags | No | - | 标签，逗号分隔，最多5个 |
| categories | No | 自动 | 分类名，多个用英文逗号分隔。脚本按标题系列自动映射：量化指标解码→量化指标解码，量化策略开发→量化策略开发，以AI量化为生→交易系统开发 |
| Description | No | - | 摘要，最大256字,发布时需要填写 |
| creation_statement | No | 3 | 创作声明 0=无声明, 1=部分内容由AI辅助生成, 2=内容来源网络进行整合创作, 3=个人看法，仅供参考（默认值） |
| status | No | 2 | 状态 2-草稿 0-发布 |
| cover_images | No | 自动 | 首图封面 URL 数组。脚本默认取正文第一张已转存图片，即 `[第一张图片URL]` |
| cover_type | No | 1或0 | 封面类型。脚本有封面图时发送 `1`（单图封面），无封面图时发送 `0` |
| authorized_status | No | false | 授权状态 |
| source | No | pc_mdeditor | 来源 |

## Field Values

### pubStatus
- `draft` - 草稿状态
- `publish` - 发布状态

### readType
- `public` - 全部可见
- `private` - 仅我可见
- `read_need_fans` - 粉丝可见
- `read_need_vip` - VIP可见

### type
- `original` - 原创
- `repost` - 转载
- `translated` - 翻译

### creation_statement
- `0` - 无声明
- `1` - 部分内容由AI辅助生成
- `2` - 内容来源于网络，进行整合再创作
- `3` - 个人看法，仅供参考

### cover_type
- `0` - 不使用首图封面
- `1` - 单图封面；CSDN 前端在 `cover_images` 有多张时会截取第一张

CSDN 编辑器前端源码显示：`cover_type=0` 时会清空 `cover_images`；`cover_type=1` 且封面数组多于一帧时只保留第一帧。

## Response

```json
{
  "code": 200,
  "traceId": "xxx",
  "data": {
    "url": "https://blog.csdn.net/xxx/article/details/xxx",
    "id": 123456,
    "qrcode": "xxx",
    "title": "文章标题",
    "description": ""
  },
  "msg": "success"
}
```

