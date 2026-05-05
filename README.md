# llm-audit-kit

> **按 L1–L8 系统分层梳理 LLM 应用攻击面，并提供一个零依赖的查漏工具。**
>
> 核心视角：**LLM 是语义逼近器，不是规则执行器**——所有安全策略都是软边界，软边界必有缝。
> 本项目从这一原理出发，系统分层攻击面 + 给出可立即使用的自查工具。

![python](https://img.shields.io/badge/python-3.8%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![deps](https://img.shields.io/badge/dependencies-none-brightgreen)

## ✨ 这是什么

- **一份结构化的 LLM 安全知识库**：按系统层级（L1 输入 → L8 反馈回流）拆分攻击面，不按"攻击类型"平铺
- **一个可跑的查漏工具 `llm-audit`**：基于清单的自查 CLI，分层打分 + 按权重排序的整改建议
- **论文 / 工具 / 基准索引**：随时扩展

## 🚀 30 秒上手

```bash
git clone https://github.com/<your-name>/llm-audit-kit.git
cd llm-audit-kit/tools/llm-audit

# 交互式自查
python audit.py

# 或者：基于示例答案生成报告
python audit.py --answers example-answers.json --output report.md
```

无需 pip install —— 纯 Python 标准库（3.8+）。

## 🧭 阅读路径

| 想做什么 | 看哪里 |
|---------|-------|
| 快速理解 L1–L8 分层攻击面 | [`notes/attack-surface-layers.md`](./notes/attack-surface-layers.md) |
| 跑查漏工具 | [`tools/llm-audit/README.md`](./tools/llm-audit/README.md) |
| 查论文 / 工具 / 基准 | [`resources.md`](./resources.md) |
| 扩展检查清单 | 编辑 [`tools/llm-audit/checklist.yaml`](./tools/llm-audit/checklist.yaml) |

---

## 1. 背景与动机

LLM 本质是**语义逼近器**，不是**规则执行器**——它的所有"安全策略"都是在行为空间里划一条**软边界**。软边界必然存在可穿越的窄缝。

> **推论**：LLM Security 的核心不是"让 LLM 更安全"，而是"设计一个即便 LLM 不安全、整体系统依然安全"的架构。

本方向以此为主线，从原理到工程落地展开。

## 2. 核心问题 / 研究点

- [ ] 从"不精确性"原理推导出攻击面分类学（L1–L8 分层）
- [ ] Prompt Injection / 间接注入的通用防御机制（特权隔离、CaMeL、StruQ）
- [ ] Agent / Tool-use 场景下的危害放大与最小权限设计
- [ ] 长上下文 / 多轮对话中的安全不变量退化
- [ ] 后门、Sleeper Agent、Fine-tuning 去对齐等模型层攻击
- [ ] 反馈回流污染（RLHF 数据 / 长期记忆 / 日志）
- [ ] 可落地的"查漏工具"与评估基准（本目录 `tools/` 下）

## 3. 攻击面分层骨架（L1–L8）

本方向的组织骨架不按"攻击类型"拆，而按**系统分层**拆，更贴近真实部署视角：

| 层 | 名称 | 典型攻击面 | 防御落点 |
|----|------|-----------|---------|
| L1 | 输入层 | 越狱、编码绕过、低资源语言、多模态注入 | 输入分类、归一化 |
| L2 | 预处理层 | 过滤器对抗、PII 脱敏还原 | 多分类器集成 |
| L3 | **上下文组装层** ⭐ | Prompt Injection、RAG 污染、历史记忆投毒、角色伪造、多轮稀释 | **特权隔离、Spotlighting、StruQ、CaMeL** |
| L4 | 模型推理层 | 对齐失效、后门、模型窃取、成员推断、侧信道 | 对抗训练、红队、后门检测 |
| L5 | 输出层 | 输出注入（XSS）、恶意 URL、包名投毒 | 输出消毒、URL 白名单 |
| L6 | **Agent 执行层** ⭐ | 工具参数注入、Confused Deputy、多步累积误差、跨 agent 借权 | **最小权限、参数白名单、预算上限、人工确认** |
| L7 | 基础设施层 | 沙箱逃逸、凭证泄露、供应链、权重窃取 | 容器化、seccomp、SBOM、权重签名 |
| L8 | 反馈回流层 | RLHF 投毒、反馈污染、长期记忆污染、对齐退化 | 反馈审计、记忆可追溯 |

**规律**：
- 攻击面越往下（L6/L7），危害越大，但**越容易用传统确定性手段兜住**。
- 攻击面越往上（L3/L4），几乎**没有确定性防御**——防御要"挪位"到 L6/L7。

完整分层流程图见 `notes/attack-surface-layers.md`。

## 4. 目录内容导航

```
.
├── README.md                          # 本文件
├── LICENSE                            # MIT
├── notes/
│   └── attack-surface-layers.md       # L1–L8 分层攻击面详图
├── papers/                            # 论文笔记（待填充）
├── experiments/                       # 实验代码（待填充）
├── tools/
│   └── llm-audit/                     # 查漏工具：LLM 应用安全自查
│       ├── README.md
│       ├── checklist.yaml             # L1–L8 × 条目 的结构化清单
│       ├── audit.py                   # 交互式 CLI 打分工具
│       └── example-answers.json
└── resources.md                       # 外部资料索引
```

## 5. 进展与结论

- [x] 建立 L1–L8 分层攻击面骨架
- [x] 实现 v0.1 查漏工具（基于 checklist.yaml 的交互式自查 + 分层评分报告）
- [ ] 补充每一层的代表论文笔记
- [ ] 搭建可运行的注入攻击 demo 环境
- [ ] 对接公开 benchmark（JailbreakBench / HarmBench / AgentBench）

## 6. 参考资料

核心参考与链接清单见 `resources.md`。

---

_最近更新：2026-05-05_
