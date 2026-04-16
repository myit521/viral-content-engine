# Prompt Contracts

本目录用于管理分析与生成 Prompt 的版本化草案。

## 目标

1. 让 `prompt_version` 有明确落点
2. 让后续真实 LLM 接入时有可直接引用的模板
3. 让分析输出和生成输出尽量保持结构稳定

## 当前文件

1. [analysis.zhihu.history.v1.md](/F:/viral-content-engine/shared/contracts/prompts/analysis.zhihu.history.v1.md)
2. [generation.zhihu_to_video.v1.md](/F:/viral-content-engine/shared/contracts/prompts/generation.zhihu_to_video.v1.md)

## 约定

1. 文件名必须与接口里使用的 `prompt_version` 一致
2. 每次结构变化都递增版本号
3. Prompt 文档要写清输入、输出、约束和失败策略
4. 在真实 LLM 接入前，这些文件视为契约草案

