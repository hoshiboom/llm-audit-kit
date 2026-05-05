# LLM Security 外部资源索引

## 核心论文（按层分类）

### L3 — Prompt Injection / 上下文防御
- Willison, *Prompt Injection Attacks Against GPT-3*, 2022（首次提出概念）
- Greshake et al., *Not what you've signed up for: Indirect Prompt Injection*, 2023
- *Spotlighting*：Microsoft 2024，给不可信内容打标记
- *StruQ*：结构化 prompt 隔离
- *CaMeL*：Google DeepMind 2025，规划/执行分离

### L4 — 模型层
- Anthropic, *Many-shot Jailbreaking*, 2024
- Anthropic, *Sleeper Agents*, 2024
- Qi et al., *Fine-tuning Aligned Models Can Undo Safety*, 2023
- Carlini et al., *Extracting Training Data from LLMs*, 2021

### L6 — Agent
- *AgentDojo*, 2024：Agent 安全基准
- *Confused Deputy in LLM Agents*（系列讨论）

### 综合 / Benchmark
- *JailbreakBench*, 2024
- *HarmBench*, 2024
- *AgentBench*

## 工具与框架
- `garak` — LLM 漏洞扫描器（NVIDIA）
- `PyRIT` — 微软红队框架
- `promptfoo` — prompt 测试与评估
- `llm-guard` — 输入输出防护
- OWASP **LLM Top 10** — 行业通用清单

## 博客 / 长文
- Simon Willison 的博客（prompt injection 持续跟进）
- Anthropic、OpenAI 的 safety 报告
- Karpathy 关于 "LLM OS" 的多篇讨论

## 标准与合规
- NIST AI RMF
- OWASP LLM Top 10
- MITRE ATLAS（AI 威胁建模框架）

---

_本清单持续更新。添加条目时请注明：类别、年份、核心结论一句话。_
