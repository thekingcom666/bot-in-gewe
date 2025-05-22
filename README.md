# Bot-in-Gewe 🤖

Bot-in-Gewe 是基于 Dow 优化版本的微信机器人框架，采用 GeWeAPI（微信iPad协议）实现稳定安全的个人微信二次开发能力。

---

## 🚀 快速开始

### 1. 账号准备
1. **注册 Gewe 账号**
   📌 [前往 Gewe 注册账号](http://218.78.116.24:10885/#/register?inviteCode=buw8nPc2xx)

2. **获取 API Token**
   登录 GeWeAPI 管理后台获取您的专属 token

3. **配置回调地址**
   在管理后台为 token 配置回调服务器地址

---
## ⚙️ 基础配置

### API 接入配置
```json
{
  "base_url": "http://api.geweapi.com/gewe/v2/api",
  "token": "your_token_here",
  "app_id": "通过扫码登录获取"
}
```
> 💡 备用 API 地址可在 GeWeAPI 管理后台查询

---

## 📦 环境要求
- Python 3.11+
- 推荐使用虚拟环境

---

## 🛠️ 安装部署

### 本地运行
```bash
# 克隆项目
git clone https://github.com/thekingcom666/bot-in-gewe.git
cd bot-in-gewe

# 安装依赖
pip install -r requirements.txt

# 配置设置
cp config-template.json config.json

# 启动（Windows）
python app.py
# 或 macOS/Linux
python3 app.py
```

### 🖥️ 服务器部署
```bash
nohup python3 app.py & tail -f nohup.out
```

### 🐳 Docker 部署
**重要提醒**：
⚠️ 部署前请确保已拉取最新源码 ⚠️

---

## 📄 配置文件说明
配置文件模板位于 `config-template.json`，使用前请重命名为 `config.json`

---

## 📌 注意事项
- 请使用 iPad 协议扫码登录（非桌面端HOOK）
- 管理后台可查询实时连接状态
- 遇到问题可查看 `nohup.out` 日志文件

---
<div align="center">
✨ 欢迎贡献代码 | 📮 问题反馈请提交 Issues
</div>
```
