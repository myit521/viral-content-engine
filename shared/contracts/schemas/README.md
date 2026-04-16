# Schema Contracts

本目录存放跨工作区共享的数据结构约定。

## 使用方式

1. 前端表单校验可参考这里的字段约束
2. 后端改动请求体或响应体时要同步更新这里
3. Prompt 输出结构也应尽量对齐这些 Schema

## 当前文件

1. [analysis-create.request.json](/F:/viral-content-engine/shared/contracts/schemas/analysis-create.request.json)
2. [template-create.request.json](/F:/viral-content-engine/shared/contracts/schemas/template-create.request.json)
3. [generation-create.request.json](/F:/viral-content-engine/shared/contracts/schemas/generation-create.request.json)
4. [generated-content.response.json](/F:/viral-content-engine/shared/contracts/schemas/generated-content.response.json)

## 说明

这些 Schema 是根据当前 `Pydantic` 模型整理出来的第一版契约，不保证已经覆盖每个响应对象的所有组合态。

