# LLM & RAG 数据质量治理 Pipeline

## 项目简介

这是一个面向 **LLM 训练语料** 与 **RAG 数据治理** 的轻量级本地 Pipeline。

它不是分布式生产系统，也不追求大规模吞吐；它适合作为本地 LLM 数据质量治理流程的最小可复现实验。项目用于在小样例数据上验证文本清洗、去重、质量评分、LLM Judge、RAG/SFT 数据构造和报告生成流程。

项目重点是：流程完整、模块清晰、结果可解释、能在本地一键跑通。

## Pipeline 流程

```text
raw JSONL
-> cleaning / filtering
-> exact dedup
-> quality scoring
-> LLM-as-a-Judge
-> RAG chunks
-> synthetic QA
-> train mix
-> reports
```

当前默认 dedup 是 **SHA-256 exact dedup**，用于识别完全重复文本。

项目也支持可选的 **SimHash near dedup**，但默认关闭。SimHash 用于识别高度相似文本；它不是 MinHash、LSH 或分布式去重。

## 核心功能

- JSONL 读取与校验
- 文本规范化
- 规则过滤
- SHA-256 exact dedup
- optional SimHash near dedup（默认关闭）
- 多维质量评分
- LLM-as-a-Judge
- RAG chunk 构建
- template-based synthetic QA
- data mixture sampling
- report assets generation
- GitHub Actions CI
- `report.json` 和 `summary.md` 生成

## 快速运行

运行完整 demo：

```powershell
python scripts/run_demo.py
```

运行测试：

```powershell
python -m unittest discover -s tests -v
```

生成静态报告图表：

```powershell
python scripts/generate_report_assets.py
```

## Demo 结果

当前样例数据的真实运行结果：

```text
Cleaned records: 11
RAG chunks: 11
Synthetic QA pairs: 11
Training mixture records: 11
High quality by judge: 8
Low quality by judge: 3
Useful for RAG: 8
Useful for SFT: 8
Average judge score: 3.4545
```

这些数字来自仓库内置的小样例数据，用于验证流程，不代表大规模生产处理能力。

## 输出文件

运行 demo 后会在 `data/output/` 下生成：

- `data/output/cleaned.jsonl`
- `data/output/rag_chunks.jsonl`
- `data/output/synthetic_qa.jsonl`
- `data/output/train_mix.jsonl`
- `data/output/report.json`
- `data/output/summary.md`
- `data/output/report_assets/filter_reasons.csv`
- `data/output/report_assets/quality_summary.csv`
- `data/output/report_assets/record_overview.svg`
- `data/output/report_assets/filter_reasons.svg`

其中：

- `cleaned.jsonl`：清洗后的文本、质量分和 judge 结果
- `rag_chunks.jsonl`：带 source metadata 的 RAG chunks
- `synthetic_qa.jsonl`：基于模板生成的 QA 样本
- `train_mix.jsonl`：按 source/domain/language/quality_level 采样后的训练混合数据
- `report.json`：机器可读的统计报告
- `summary.md`：人工可读的 Markdown 摘要报告
- `report_assets/`：静态 CSV / SVG 报告图表，便于在 GitHub 上直接查看

## 主要模块

- `src/pipeline.py`：串联完整数据治理流程
- `src/cleaning.py`：文本规范化、规则过滤和 SHA-256 hash
- `src/near_dedup.py`：可选 SimHash near-duplicate detection
- `src/jsonl_io.py`：JSONL 读取、校验和写入
- `src/quality_scorer.py`：多维启发式质量评分
- `src/llm_judge.py`：LLM-as-a-Judge，支持 heuristic、mock 和 OpenAI-compatible API 模式
- `src/rag_chunker.py`：固定长度与 overlap 的 RAG chunk 构建
- `src/synthetic_qa.py`：template-based synthetic QA 生成
- `src/data_mixer.py`：按 source/domain/language/quality_level 做 data mixture sampling
- `src/summary.py`：生成 Markdown summary 报告
- `scripts/generate_report_assets.py`：从 `report.json` 生成静态 CSV / SVG 报告图表

## 测试

当前测试覆盖：

- cleaning
- jsonl io
- pipeline
- quality scorer
- llm judge
- rag chunker
- synthetic QA
- data mixer
- near dedup
- report assets

当前测试结果：

```text
Ran 42 tests
OK
```

## 项目边界

- 不是分布式数据处理系统
- 没有 GPU 加速
- SimHash near dedup 是可选功能，默认关闭
- 没有 MinHash / LSH / 分布式 near dedup
- SimHash 是轻量级近似去重，不是 MinHash / LSH / 分布式去重
- report assets 是静态图表，不是可视化平台
- CI 只做基础 demo 和 unit tests
- LLM Judge 默认是 heuristic，本地可跑；也支持 mock 和 OpenAI-compatible API 模式
- 当前使用小样例数据，主要用于验证 LLM 数据治理流程

## 设计取舍

该 pipeline 按数据生命周期拆分为校验、过滤、去重、评分、构造和报告几个阶段：

- 数据进入 LLM/RAG 流程前需要基础质量治理：原始语料常见空文本、重复、噪声、广告链接和结构混乱等问题。
- exact dedup 和 near dedup 负责解决不同层次的重复问题：SHA-256 exact dedup 只能去掉完全重复文本；SimHash near dedup 可以在开启后识别高度相似文本，但当前不做 MinHash、LSH 或分布式去重。
- 多维质量评分比单一规则更容易定位问题：长度、可读性、信息量、噪声和重复度可以分别观察。
- LLM-as-a-Judge 层把底层质量信号转换成更接近任务目标的判断，例如是否适合 pretraining、RAG 或 SFT。
- RAG chunk 和 synthetic QA 为后续数据构造提供入口：chunk 可进入检索语料，QA demo 可以扩展为指令数据或评测数据准备流程。
- `report.json`、`summary.md` 和 report assets 分别服务于程序读取、人工浏览和静态图表查看。
- CI 在每次 push 或 pull request 时运行 demo 和 unit tests，用来检查主流程是否仍然稳定。

整体上，这个项目不追求堆叠复杂技术，而是把 LLM 数据治理 Pipeline 拆成可运行、可测试、可解释的本地模块。
