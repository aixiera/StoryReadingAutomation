# 序蓝酱读书内容生成器

一个稳定优先的本地 MVP：输入书名和一段书本文字正文，自动生成标题、简介、配音文案、分段音频、字幕、封面图和 `manifest.json`。项目默认使用 mock LLM 与 mock TTS，所以没有任何外部 API key 也可以跑完整流程。

核心原则：不做读书解读，不大幅改写正文主体。模型或 mock 只负责标题、简介、固定开头/结尾、封面文案等包装内容。

## 功能清单

- 轻量清洗正文：去空行、统一常见标点、清理乱码、合并不自然断行
- 生成自媒体发布用 `title`、`subtitle`、`description`、`cover_text`
- 构造配音用 `narration_text`：短开头 + 用户正文 + 短结尾
- 按句子边界切分 TTS chunk，目标约 40-55 秒
- 支持 ElevenLabs 真实 TTS，也支持本地 mock TTS
- 每段音频落盘到 `output/audio_segments/{job_id}/`
- 拼接生成 `output/audio_final/{job_id}/final_audio.mp3`
- 自动生成 `subtitles.srt`
- 用 Pillow 合成竖版封面 `final_cover.png`
- 生成结构化 `output/jobs/{job_id}/manifest.json`
- 提供 CLI 和 FastAPI HTTP API，方便后续接 n8n

## 目录结构

```text
project_root/
├─ app/
│  ├─ api/main.py
│  ├─ core/config.py
│  ├─ core/logging.py
│  ├─ core/utils.py
│  ├─ services/
│  │  ├─ text_cleaner.py
│  │  ├─ copy_generator.py
│  │  ├─ narration_builder.py
│  │  ├─ tts_splitter.py
│  │  ├─ elevenlabs_client.py
│  │  ├─ audio_concat.py
│  │  ├─ subtitle_builder.py
│  │  ├─ cover_composer.py
│  │  ├─ manifest_builder.py
│  │  └─ pipeline.py
│  ├─ models/
│  │  ├─ schemas.py
│  │  └─ manifest.py
│  └─ cli/main.py
├─ assets/
│  ├─ xulan/xulan_main.png
│  ├─ backgrounds/
│  ├─ fonts/
│  └─ placeholders/
├─ output/
├─ tests/
├─ .env.example
├─ requirements.txt
├─ README.md
└─ run_demo.py
```

## 环境依赖

- Python 3.11+
- pip
- ffmpeg：真实 MP3 拼接/转码需要
- Windows/macOS/Linux 都可以；路径处理使用 `pathlib`

安装 Python 依赖：

```powershell
cd F:\coding\StoryReadingAutomation
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

如果你的 Windows 终端里 `python` 不可用，先安装 Python 3.11+，并勾选 “Add Python to PATH”。

## ffmpeg 安装说明

真实 ElevenLabs 会返回 MP3 分段，最终统一采样率、声道、音量并导出 MP3 时需要 ffmpeg。

Windows 推荐：

```powershell
winget install Gyan.FFmpeg
```

安装后重新打开终端，确认：

```powershell
ffmpeg -version
```

说明：mock TTS 会生成 WAV 占位音频。若本机没有 ffmpeg，项目会使用标准库把 WAV 片段拼起来，并仍按验收路径生成 `final_audio.mp3`，同时生成一个 `final_audio.wav` 兄弟文件方便播放器直接识别。生产环境建议安装 ffmpeg。

## 本地运行 Demo

默认就是 mock 模式：

```powershell
python run_demo.py
```

成功后会打印：

- `job_id`
- 标题和简介
- `final_audio_path`
- `cover_image_path`
- `subtitle_path`
- `manifest_path`

## CLI 使用

```powershell
python -m app.cli.main `
  --book-title "如何停止胡思乱想" `
  --text-file sample.txt `
  --style "治愈安静" `
  --cover-theme "绿色治愈" `
  --mock-llm `
  --mock-tts
```

也可以直接传正文：

```powershell
python -m app.cli.main --text "这里是一段书本文字正文。" --mock-llm --mock-tts
```

## API 使用

启动服务：

```powershell
uvicorn app.api.main:app --reload
```

健康检查：

```powershell
curl http://127.0.0.1:8000/health
```

生成内容：

```powershell
curl -X POST "http://127.0.0.1:8000/generate" `
  -H "Content-Type: application/json" `
  -d "{\"book_title\":\"如何停止胡思乱想\",\"text\":\"这里是一段书本文字正文。\",\"style\":\"治愈安静\",\"cover_theme\":\"绿色治愈\",\"use_mock_tts\":true,\"use_mock_llm\":true}"
```

查询任务：

```powershell
curl http://127.0.0.1:8000/jobs/{job_id}
```

API 返回 JSON，适合直接被 n8n 的 HTTP Request 节点调用。

## 配置

复制配置文件：

```powershell
copy .env.example .env
```

常用配置：

```env
USE_MOCK_LLM=true
USE_MOCK_TTS=true
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
ELEVENLABS_OUTPUT_FORMAT=mp3_44100_128
TTS_TARGET_MIN_SECONDS=40
TTS_TARGET_MAX_SECONDS=55
TTS_CHARS_PER_MINUTE=240
COVER_WIDTH=1080
COVER_HEIGHT=1440
XULAN_ASSET_PATH=assets/xulan/xulan_main.png
MEDIA_EXPORT_DIR=F:/alex computer transfer/读书栏目/愿你可以自在张扬
```

如果设置了 `MEDIA_EXPORT_DIR`，每次任务完成后，程序会把 `final_audio.mp3` 和 `final_cover.png` 额外复制到：

```text
{MEDIA_EXPORT_DIR}/{job_id}/
```

这样本地 `output/` 仍保留完整任务产物，同时你指定的栏目文件夹里也会自动得到音频和封面。

## 如何替换序蓝酱素材

固定虚拟人素材路径：

```text
assets/xulan/xulan_main.png
```

如果该文件不存在，程序会自动生成一个明显的占位人物图。后续只需要把真实的透明背景 PNG 替换为同名文件即可。建议素材是半身或全身透明 PNG，长边 900px 以上。

## 中文字体

封面合成会优先查找：

1. `assets/fonts/` 下的 `.ttf`、`.otf`、`.ttc`
2. Windows 常见中文字体，例如微软雅黑、黑体、宋体
3. macOS/Linux 常见中文字体
4. Pillow 默认字体

如果封面中文字显示不理想，把中文字体文件放入 `assets/fonts/` 即可。

## 接入真实 ElevenLabs

在 `.env` 中设置：

```env
USE_MOCK_TTS=false
ELEVENLABS_API_KEY=你的_api_key
ELEVENLABS_VOICE_ID=你的_voice_id
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
ELEVENLABS_OUTPUT_FORMAT=mp3_44100_128
```

然后运行：

```powershell
python run_demo.py
```

或在 API 请求中传：

```json
{
  "use_mock_tts": false
}
```

项目使用 ElevenLabs 官方 Text to Speech HTTP 接口：

```text
POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128
```

参考官方文档：https://elevenlabs.io/docs/api-reference/text-to-speech

## mock 模式切换到真实模式

- mock LLM：`USE_MOCK_LLM=true`
- mock TTS：`USE_MOCK_TTS=true`
- 真实 TTS：`USE_MOCK_TTS=false`，并填写 ElevenLabs key 与 voice id
- 外部 LLM：设置 `USE_MOCK_LLM=false`，并提供 `LLM_API_URL`

当前 LLM 真实调用是可替换的通用 JSON HTTP provider，不绑定某个厂商。你的 endpoint 返回 `CopyResult` 结构即可：

```json
{
  "title": "今晚读《某本书》",
  "subtitle": "治愈安静的一段文字",
  "description": "发布简介",
  "cover_text": "封面短句",
  "cover_keywords": ["治愈安静", "夜读"],
  "intro_line": "晚上好，这里是序蓝酱。",
  "outro_line": "读到这里就好。"
}
```

## n8n 接入建议

1. 使用 HTTP Request 节点调用 `POST /generate`
2. Body 使用 JSON，传入 `book_title`、`text`、`style`、`cover_theme`
3. 从响应里读取 `job_id`、`manifest_path`、`final_audio_path`、`cover_image_path`
4. 如需后续查询，调用 `GET /jobs/{job_id}`
5. 后续可继续接 Telegram、Notion、网盘上传或视频合成节点

## 测试

```powershell
pytest
```

测试覆盖：

- 文本清洗
- TTS 分段
- mock 模式最小 smoke test，确认 manifest、cover、audio、srt 都能产出
