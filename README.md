# LLM Data Cleaning Pipeline

一个使用 Python 实现的轻量级 LLM 预训练语料清洗流水线。项目以本地 JSONL 文本数据为输入，通过可配置、可解释的处理步骤生成清洗后的数据及统计报告，适合作为数据工程与 LLM 数据处理方向的学习和求职展示项目。

## 项目背景

LLM 的训练效果不仅取决于模型结构和数据规模，也受到训练语料质量的直接影响。未经处理的原始文本中可能包含空文本、重复内容、格式混乱、乱码、广告链接、特殊字符噪声以及低信息密度文本。

这些问题会降低有效数据占比，增加无效训练成本，也会影响语料质量的一致性。本项目实现了一个规模可控、便于理解的本地清洗流程，用于演示 LLM 训练语料从原始数据到可用数据的基础处理过程。

## 项目功能

- **JSONL 读取与校验**：逐行读取数据，识别非法 JSON、缺少 `text` 字段和字段类型错误。
- **文本规范化**：统一换行符、移除首尾空白并压缩连续空格。
- **可配置规则过滤**：过滤空文本、长度异常、URL 过多、特殊字符过多、重复字符过多和有效字符不足的文本。
- **精确去重**：对规范化文本计算 SHA-256 hash，保留首次出现的记录。
- **可解释质量评分**：根据文本长度、有效字符比例和重复字符比例计算 `0-1` 质量分。
- **清洗报告生成**：统计保留率、移除原因、无效记录、重复记录、质量分分布和处理时间。

## Pipeline 流程

```text
JSONL Loading
      -> Validation
      -> Normalization
      -> Filtering
      -> Deduplication
      -> Quality Scoring
      -> Report Generation
```

## 项目结构

```text
llm-data-cleaning-project/
├── configs/
│   └── default.yaml
├── data/
│   ├── raw/
│   │   └── sample.jsonl
│   └── output/
│       ├── cleaned.jsonl
│       ├── report.json
│       └── summary.md
├── src/
│   ├── main.py
│   ├── pipeline.py
│   ├── cleaning.py
│   ├── jsonl_io.py
│   └── config.py
└── README.md
```

- `src/main.py`：命令行入口，解析输入路径、输出目录和配置文件参数。
- `src/pipeline.py`：编排校验、规范化、过滤、去重、评分和报告生成流程。
- `src/cleaning.py`：实现文本规范化、过滤规则、hash 计算和质量评分。
- `src/jsonl_io.py`：负责 JSONL 数据读取、基础校验和结果写入。
- `src/config.py`：读取并校验项目使用的简单 YAML 配置。
- `configs/default.yaml`：定义长度、质量分及文本规则的过滤阈值。
- `data/raw/sample.jsonl`：用于演示正常、重复、无效和低质量文本的样例数据。
- `data/output/report.json`：记录清洗结果、过滤原因和质量分统计。
- `data/output/summary.md`：将核心清洗指标整理为适合人工阅读和展示的 Markdown 报告。

## 安装与运行

### 环境要求

- Python 3.10 或更高版本
- 无第三方 Python 依赖

在项目根目录使用默认路径运行：

```powershell
python -m src.main
```

显式指定输入文件、输出目录和配置文件：

```powershell
python -m src.main --input data/raw/sample.jsonl --output-dir data/output --config configs/default.yaml
```

默认输出文件：

- `data/output/cleaned.jsonl`
- `data/output/report.json`
- `data/output/summary.md`

### 运行测试

项目使用 Python 标准库 `unittest`，无需安装额外测试依赖：

```powershell
python -m unittest discover -s tests
```

## 输入格式

输入文件采用 JSONL 格式，每行必须是一个包含字符串类型 `text` 字段的 JSON 对象：

```json
{"text": "This is a document."}
```

## 清洗数据示例

`cleaned.jsonl` 保留规范化文本，并增加质量分和可解释的评分明细：

```json
{
  "text": "Large language models require clean and diverse training data.",
  "quality_score": 0.7529,
  "quality_details": {
    "length_score": 0.485,
    "valid_character_ratio": 0.9762,
    "repeated_character_ratio": 0.131
  }
}
```

## 清洗报告示例

`report.json` 汇总整个处理过程。以下为当前样例数据的部分结果：

```json
{
  "total_records": 14,
  "kept_records": 4,
  "removed_records": 10,
  "keep_ratio": 0.2857,
  "filter_reason_counts": {
    "empty_text": 1,
    "high_repeated_char_ratio": 1,
    "high_special_char_ratio": 1,
    "low_valid_char_ratio": 1,
    "too_many_urls": 1,
    "too_short": 1
  },
  "quality_score_summary": {
    "min": 0.6466,
    "max": 0.792,
    "mean": 0.7412,
    "median": 0.7631
  }
}
```

完整报告还包括输入、输出和配置路径，无效记录分类、重复记录数量、移除比例、配置快照及处理时间。

同一次运行还会生成 `summary.md`，使用表格展示运行信息、样本保留情况、无效记录、过滤原因、重复样本数量和质量分统计，便于在 GitHub 或面试中快速查看清洗效果。

## 配置文件

默认配置位于 `configs/default.yaml`：

```yaml
min_length: 20
max_length: 5000
quality_threshold: 0.0
max_url_count: 2
max_special_char_ratio: 0.3
max_repeated_char_ratio: 0.5
min_valid_char_ratio: 0.5
```

| 配置项 | 说明 |
| --- | --- |
| `min_length` | 文本允许的最小字符长度。 |
| `max_length` | 文本允许的最大字符长度。 |
| `quality_threshold` | 最低质量分，低于该分数的文本会被过滤。 |
| `max_url_count` | 单条文本允许包含的最大 URL 数量。 |
| `max_special_char_ratio` | 特殊字符数量占非空白字符的最大比例。 |
| `max_repeated_char_ratio` | 出现次数最多的单一字符所允许的最大占比。 |
| `min_valid_char_ratio` | 字母和数字等有效字符所需达到的最小比例。 |

## 项目亮点

- **面向 LLM 训练语料**：围绕预训练文本常见质量问题设计清洗步骤。
- **可解释过滤规则**：每条被过滤的记录都有明确原因，便于分析和调参。
- **配置化清洗策略**：通过配置文件调整阈值，无需修改核心处理代码。
- **可追踪统计报告**：对无效、过滤、重复和保留数据进行分类统计。
- **模块化 Pipeline 设计**：I/O、配置、清洗规则和流程编排职责清晰，便于继续扩展。

## 后续优化方向

- 扩展边界条件、异常输入和端到端测试覆盖率。
- 增加更多可解释的数据质量规则。
- 支持 MinHash 或 SimHash 等近似去重方法。
- 优化流式处理和磁盘使用，以支持更大规模数据。
- 增加图表形式的可视化清洗报告。

## 项目定位

本项目是一个用于学习和展示的 mini 数据清洗流水线，重点在于呈现完整、清晰、可运行的 LLM 文本数据处理过程。目前不包含分布式计算、GPU 加速或模型质量评分等复杂能力。
