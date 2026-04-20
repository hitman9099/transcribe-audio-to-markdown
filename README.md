# transcribe-audio-to-markdown

这是一个给 Codex 使用的 skill，用来把本地音频转写成 Markdown，并进一步整理出原文、润色稿/翻译稿、关键信息和代办事项。

## 功能

- 支持处理本地音频文件，例如 `.m4a`、`.mp3`、`.wav`
- 优先使用本地离线转写链路，例如 `faster-whisper`
- 输出带时间戳的原始转写文本
- 生成适合阅读的整理稿或翻译稿
- 提取时间、地点、证件、下载入口等关键信息
- 从录音内容中提炼待办事项
- 支持保留“原文（不做修改）”章节
- 支持把“下周二下午 1 点”这类相对时间转换成明确日期

## 适用场景

- 微信语音或电话录音整理
- 招生电话、面试通知、回访电话整理
- 会议录音转纪要
- 采访、访谈、语音备忘录整理
- 需要同时保留原文和整理稿的音频处理任务

## 仓库结构

```text
.
├── SKILL.md
└── agents/
    └── openai.yaml
```

## Skill 说明

`SKILL.md` 里定义了这套流程的核心规则，包括：

- 如何确认输入音频路径和输出 Markdown 路径
- 如何优先走本地离线转写
- 如何处理转写文件乱码
- 如何组织 Markdown 结构
- 如何保留原始转写内容不做修改
- 如何提取代办事项
- 如何把相对时间转换为绝对日期

## 推荐输出结构

这个 skill 默认建议生成以下几个章节：

1. 说明
2. 关键信息
3. 整理后的内容或翻译后的内容
4. 原文（不做修改）
5. 代办事项

## 示例请求

```text
把这个 .m4a 转成 Markdown，并提炼代办事项
```

```text
转写这段通话，保留原文，不要修改
```

```text
把这段录音翻译成英文，并附上原文和行动项
```

## 使用方式

在支持 skill 的 Codex 环境中引用：

```text
Use $transcribe-audio-to-markdown to turn this local audio file into Markdown with a raw transcript, a cleaned version, and action items.
```

如果你希望把这个 skill 安装到本地 Codex 技能目录，通常可以放到：

```text
%USERPROFILE%\.codex\skills\transcribe-audio-to-markdown
```

## 备注

- 这个仓库主要提供 skill 定义，不直接捆绑具体模型权重。
- 实际转写时，优先复用本机已有的 `ffmpeg`、`python` 和缓存模型。
- 对于学校名、人名、机构名等专有名词，仍建议人工复核一次。
