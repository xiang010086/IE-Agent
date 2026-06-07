# 网页端部署说明

当前项目已经是 Streamlit 网页应用，本机可用 Chrome 打开：

```powershell
streamlit run app/streamlit_project_app.py --server.port 8501
```

打开：

```text
http://localhost:8501
```

## 局域网访问

如果同一 Wi-Fi/内网里的其他电脑要访问，用启动日志里的 Network URL，例如：

```text
http://你的电脑IP:8501
```

Windows 防火墙如果拦截，需要允许 Python/Streamlit 访问专用网络。

## 公网网页端

推荐三种方式：

1. Streamlit Community Cloud：适合演示，上传到 GitHub 后选择 `app/streamlit_project_app.py`。
2. 云服务器 + Docker：适合客户试用或内部部署。
3. 企业内网服务器：适合工业场景，视频数据不出公司网络。

## Docker 部署

```powershell
docker build -t industrial-ie-agent .
docker run -p 8501:8501 -v ${PWD}/data:/app/data industrial-ie-agent
```

然后打开：

```text
http://localhost:8501
```

## 中英文

网页左侧可以切换 `中文` / `English`。切换后，主要标题、操作入口、参数说明、验证页都会切换语言。
