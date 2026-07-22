# API_DESIGN.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 阶段：API 设计与最小实现更新
- 日期：2026-06-14
- 当前结论：已新增最小第一方 API 实现 `Backend/api/server.py`，覆盖恢复密钥账号、手机号登录接口、微信登录接口、同步恢复、照片原图上传/下载/删除、账号删除和第一方合规埋点；服务端已支持短信 webhook、阿里云短信 webhook adapter、微信 code 换 openid/unionid 和白名单行为事件，生产域名、真实阿里云短信签名/模板、微信开放平台凭证、iOS OpenSDK、云主机和对象存储区域仍需发布前私有确认

## 已确认事实

1. 第一版必须离线可本地记录。
2. 第一版需要账号。
3. 第一版需要同步恢复。
4. 服务器需要存照片原图。
5. 首发地区改为中国大陆，香港第二批。

## 合理推断

1. API 不应参与高频记录的实时保存路径。
2. API 失败不能影响本地使用。
3. 删除 API 是上线前强制项。
4. 照片上传应只处理用户主动加入 App 的照片。

## 待我确认的问题

1. API 正式域名。
2. 生产部署使用云对象存储还是当前磁盘对象目录。
3. 生产删除 SLA 是否承诺为立即删除，或增加短期恢复窗口。
4. 是否需要上传缩略图。
5. 短信服务商、签名、模板和发送区域。
6. 微信开放平台 AppID、AppSecret、Universal Link / URL Scheme 和审核材料。
7. 正式隐私政策中第一方行为埋点的用户告知文案。

## 不进入第一版的功能

1. 管理后台 API。
2. 运营推送 API。
3. 家庭协作 API。
4. 公开分享 API。

## 已实现的最小 API

| API | 用途 | 第一版状态 |
|---|---|---|
| `POST /v1/accounts` | 创建私有同步账号并返回恢复密钥 | 已实现 |
| `POST /v1/sessions/recover` | 使用恢复密钥换取会话 | 已实现 |
| `POST /v1/auth/phone/request-code` | 请求手机号登录验证码 | 已实现；生产需配置短信 webhook |
| `POST /v1/auth/phone/verify` | 校验手机号验证码并换取会话 | 已实现 |
| `POST /v1/auth/wechat/login` | 使用微信授权 code 登录 | 已实现；生产需配置微信开放平台凭证和 iOS OpenSDK |
| `GET /v1/account` | 查看账号状态 | 已实现 |
| `PUT /v1/sync` | 上传宝宝档案、记录、提醒、照片元数据 JSON 同步 | 已实现 |
| `GET /v1/sync` | 恢复最新 JSON 同步 | 已实现 |
| `PUT /v1/photos/{photoId}` | 上传用户主动加入 App 的照片原图 | 已实现 |
| `GET /v1/photos` | 列出账号下的照片对象元数据 | 已实现 |
| `GET /v1/photos/{photoId}` | 下载账号下的私有照片原图 | 已实现 |
| `DELETE /v1/photos/{photoId}` | 删除单张云端照片对象 | 已实现 |
| `DELETE /v1/account` | 删除账号、云端同步和云端照片对象 | 已实现 |
| `POST /v1/analytics/events` | 提交第一方白名单行为事件 | 已实现；只收聚合分析所需枚举属性 |

## 合规埋点 API

`POST /v1/analytics/events` 要求 Bearer token，示例：

```json
{
  "events": [
    {
      "eventId": "UUID",
      "name": "cloud_sync_completed",
      "occurredAt": "2026-06-24T00:00:00Z",
      "properties": {
        "source": "sync",
        "result": "success",
        "platform": "ios"
      }
    }
  ]
}
```

边界：

1. 只接受 `Docs/06_AnalyticsGrowth/EVENT_TAXONOMY.md` 中的事件名和属性枚举。
2. 不保存原始 `accountId`，只保存 HMAC 后的账号哈希。
3. 不接受宝宝昵称、生日、照片、对象 key、手机号、微信 openid/unionid、恢复密钥、token、定位、User-Agent 或任意自由文本。
4. 单次最多 50 条事件，请求体最多 64 KB。
5. 默认留存 180 天，最长 365 天。
6. 删除账号时同步删除该账号对应的埋点事件。

## 账号方式

第一版账号入口调整为恢复密钥、手机号和微信：

1. 创建账号时生成 `accountId`、短期 `sessionToken` 和一次性展示的 `recoveryKey`。
2. 客户端把 `sessionToken` 存入 Keychain。
3. 换机恢复时，用户输入恢复密钥换取新会话。
4. 手机号登录只保存手机号的 HMAC 标识，不保存明文手机号到账号身份表。
5. 微信登录只保存微信 openid/unionid 的 HMAC 标识，不在客户端保存微信密钥。
6. 不采集邮箱、通讯录或社交关系。

正式上线前必须配置真实短信 webhook、微信开放平台 AppID/AppSecret，以及 iOS 端 OpenSDK / 真实 `wx...` URL Scheme，并在微信开放平台后台绑定已准备好的 Universal Link。阿里云短信可通过 `Backend/sms/aliyun-webhook-adapter` 独立接入，主 API 只配置本机 webhook URL 和共享密钥。当前 debug 登录不能作为生产能力；`Backend/scripts/verify_auth_providers.py` 会生成不含密钥的 `Backend/proof/auth-providers.json`，用于证明后端服务商配置和线上 debug 拒绝状态。

## 验证命令

```bash
cd Backend
python3 -m unittest tests/test_api.py
```

## 禁止事项

1. 不允许上传未在隐私审查中列出的字段。
2. 不允许把宝宝照片、备注、生日作为日志输出。
3. 不允许未登录或未鉴权访问用户数据。
4. 不允许返回长期公开照片 URL。
5. 不允许把埋点扩展为用户画像、广告归因、内容分析或单用户后台查询。
