# video-lines skill v2.7.0 开发经验总结

> **日期**: 2026-03-13
> **版本**: v2.7.0
> **主题**: ASR 幻觉问题的排查与解决

---

## 一、问题背景

用户报告视频转录存在两个问题：
1. **末尾多余内容**：视频结束后出现 ASR 产生的幻觉文本（如 `</persisted-output>` 标签）
2. **分段不足**：LLM 后处理的段落太长

---

## 二、踩过的坑

### 坑1：不可靠的文本模式匹配

**错误方案**：通过检测"结束语"来截断末尾内容
```python
# 这个方案不可靠！
ending_patterns = [r'下次见', r'拜拜', r'再见', ...]
```

**问题**：
- 不是所有视频都有标准结束语
- 有些视频说完"再见"后还有真实内容
- 模式固定，无法适应不同类型视频

**教训**：视频内容千差万别，不能用简单的模式匹配一刀切

---

### 坑2：ffmpeg silenceremove 参数错误

**错误参数**：
```
silenceremove=stop_periods=1:stop_duration=1:stop_threshold=-40dB
```

**后果**：裁剪过度（121分钟 → 54分钟，少了近一半！）

**正确参数**：
```
silenceremove=stop_periods=-1:stop_duration=1:stop_threshold=-40dB:detection=peak
```

**关键点**：
- `stop_periods=-1`：负值表示从**末尾**开始移除静音
- `stop_periods=1`：表示从**开头**移除静音（与预期相反）
- `detection=peak`：使用峰值检测模式

**验证方法**：始终检查裁剪前后的音频时长
```python
# 检查音频时长
import wave
with wave.open('audio.wav', 'rb') as f:
    duration = f.getnframes() / f.getframerate()
    print(f"Duration: {duration:.2f} seconds")
```

---

### 坑3：幻觉检测逻辑错误

**错误代码**：
```python
for i in range(len(lines) - 1, len(lines) - lines_to_check - 1, -1):
    for pattern in hallucination_patterns:
        if re.match(pattern, line):
            first_hallucination_idx = i
            break
    else:
        if first_hallucination_idx is not None:
            first_hallucination_idx = None
        continue
    break  # ← 这个 break 导致只检查了一行就退出！
```

**问题**：`break` 语句导致外层循环也提前退出，只检查了一行

**教训**：写循环逻辑时，要仔细考虑 `break` 和 `continue` 的作用范围

---

## 三、正确的解决方案

### 方案架构：双层防护

```
┌─────────────────────────────────────────────────────────┐
│                    视频输入                              │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  第一层：音频级别防护                                    │
│  - 提取音频                                             │
│  - 使用 ffmpeg silenceremove 裁剪末尾静音               │
│  - 参数：stop_periods=-1:stop_duration=1:stop_threshold=-40dB │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  第二层：文本级别防护                                    │
│  - ASR 转录                                             │
│  - 检测末尾的 XML 标签模式（如 </persisted-output>）     │
│  - 仅移除连续出现在末尾的幻觉标签                        │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    干净的输出                            │
└─────────────────────────────────────────────────────────┘
```

### 关键代码

**1. 音频静音裁剪**（`video_transcriber.py`）
```python
def _trim_end_silence(self, audio_path: str) -> str:
    cmd = [
        self.ffmpeg_path,
        "-i", audio_path,
        "-af", "silenceremove=stop_periods=-1:stop_duration=1:stop_threshold=-40dB:detection=peak",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        "-y", trimmed_path
    ]
    # ...
```

**2. 文本幻觉检测**（`transcript_cleaner.py`）
```python
def _remove_trailing_asr_hallucination(self, content: str) -> Tuple[str, Dict]:
    # 检测 XML 标签模式
    hallucination_patterns = [
        r'^</[a-zA-Z0-9_-]+>$',  # Closing XML-like tags
        r'^<[a-zA-Z0-9_-]+>$',   # Opening XML-like tags
    ]
    # 只移除连续出现在末尾的幻觉标签
    # ...
```

---

## 四、避坑技巧

### 技巧1：验证每一步的效果

```bash
# 检查音频时长变化
python -c "
import wave
for name in ['temp_audio.wav', 'temp_audio_trimmed.wav']:
    with wave.open(f'transcripts/{name}', 'rb') as f:
        duration = f.getnframes() / f.getframerate()
        print(f'{name}: {duration:.2f} seconds')
"

# 检查分段数量变化
ls -la transcripts/audio_segments/ | wc -l

# 检查输出文件末尾
tail -50 output.txt
```

### 技巧2：使用 `-40dB` 阈值

| 声音类型 | 典型分贝值 |
|----------|-----------|
| 正常语音 | -20 ~ -30dB |
| 轻声说话 | -35 ~ -40dB |
| 静音/背景噪音 | -50dB 以下 |

**-40dB 是安全阈值**：不会误删轻声内容

### 技巧3：保留改进的分段提示词

即使幻觉问题解决了，也要保留 LLM 分段提示词的改进：
```
【智能分段规则】
1. 按对话轮次分段：识别不同说话人或对话转换
2. 控制段落长度：
   - 理想长度：3-5句话（约100-200字）
   - 最长不超过10句话（约400字）
```

### 技巧4：先理解再修改

在修改代码之前，先理解：
1. 数据流向（音频 → 分段 → ASR → 清洗 → LLM → 输出）
2. 每个环节的作用
3. 问题的根源在哪里

---

## 五、效果验证

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 分段数 | 333 | 289 |
| 末尾状态 | 有幻觉标签 | 干净，自然结束 |
| 有效音频 | 完整 | 完整（正确裁剪） |

---

## 六、关键教训

1. **音频级别 > 文本级别**：从根源解决问题比后处理更可靠
2. **验证参数效果**：ffmpeg 参数要实际测试，不要想当然
3. **保守策略**：宁可漏掉一些问题，也不要误删正常内容
4. **用户反馈很重要**：用户说的"不能用简单模式匹配"是正确的

---

## 七、未来改进方向

1. **分段级别的静音检测**：不仅裁剪整体音频末尾，也检测每个分段是否有静音
2. **置信度过滤**：利用 ASR 返回的置信度信息，过滤低置信度内容
3. **自适应阈值**：根据视频的整体音量动态调整静音阈值

---

*此文档基于 v2.7.0 开发过程中的实际经验整理*
