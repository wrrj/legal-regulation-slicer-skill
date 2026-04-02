# 输出契约说明

> 更新日期：2026-04-02

## 1. 目标

本文件说明 `articles.jsonl`、`manifest.json`、`failed_files.jsonl` 的固定字段契约，供：

- 开发者接入关系型数据库
- 开发者接入向量数据库
- 大模型读取产物继续处理
- 数据迁移脚本读取结果

## 2. `articles.jsonl`

### 2.1 文件语义

- 一行一个 JSON 对象
- 一条记录对应一个法条切片
- 编码固定为 UTF-8

### 2.2 字段定义

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `chunk_id` | `string` | 是 | 当前记录主键，默认等于 `version_id` |
| `version_id` | `string` | 是 | 稳定版本主键，由法规名、法条号、生效日期、正文哈希计算得到 |
| `law_name` | `string` | 是 | 法规名称 |
| `law_name_norm` | `string` | 是 | 去空白、小写后的法规名称 |
| `article_no` | `string` | 是 | 法条编号，例如 `第三条` |
| `article_no_norm` | `string` | 是 | 归一化法条编号 |
| `citation_text` | `string` | 是 | 完整法条正文 |
| `content_hash` | `string` | 是 | `citation_text` 的 SHA-1 哈希 |
| `authority_name` | `string` | 是 | 主管机关；未显式覆盖时默认为 `未指定主管机关` |
| `legal_category` | `string` | 是 | 一级法律分类，例如 `法律`、`行政法规` |
| `legal_subcategory` | `string` | 是 | 二级法律分类，例如 `法律`、`法律解释`、`行政法规` |
| `legal_topic` | `string \| null` | 是 | 三级专题分类，例如 `刑法`、`民法商法`；二级目录结构时为 `null` |
| `status` | `string` | 是 | 法规状态；当前固定为 `未知`，后续如引入独立状态来源再扩展 |
| `effective_from` | `string` | 是 | ISO 8601 日期时间字符串 |
| `effective_to` | `string \| null` | 是 | 失效时间，当前默认 `null` |
| `is_current` | `integer` | 是 | 当前默认 `1` |
| `source_file` | `string` | 是 | 相对输入根目录的来源路径 |
| `source_file_type` | `string` | 是 | 来源文件类型，如 `docx`、`pdf` |
| `chunk_mode` | `string` | 是 | 当前固定为 `article` |
| `chunk_rule_version` | `string` | 是 | 当前固定为 `article_regex_v2` |
| `embedding_text` | `string` | 是 | 默认向量化文本 |
| `metadata_tags` | `object` | 是 | 扩展标签字典 |

### 2.3 `embedding_text` 生成规则

固定拼接规则：

```text
law_name + " " + article_no + " " + citation_text
```

用途：

- 向量化输入文本
- 检索召回语料
- 大模型上下文拼接基础文本

### 2.4 示例

```json
{
  "chunk_id": "v_cf2807b444d6abf5cada610f2d6a30ef76db4db1",
  "version_id": "v_cf2807b444d6abf5cada610f2d6a30ef76db4db1",
  "law_name": "示例办法",
  "law_name_norm": "示例办法",
  "article_no": "第一条",
  "article_no_norm": "第一条",
  "citation_text": "第一条 为了规范示例流程。",
  "content_hash": "9f0b86d5c2440b75b6d4dcc8c70033f1c77f1511",
  "authority_name": "未指定主管机关",
  "legal_category": "法律",
  "legal_subcategory": "法律",
  "legal_topic": "刑法",
  "status": "未知",
  "effective_from": "2024-01-02T00:00:00",
  "effective_to": null,
  "is_current": 1,
  "source_file": "法律/法律/刑法/示例办法_20240102.docx",
  "source_file_type": "docx",
  "chunk_mode": "article",
  "chunk_rule_version": "article_regex_v2",
  "embedding_text": "示例办法 第一条 第一条 为了规范示例流程。",
  "metadata_tags": {
    "record_schema_version": "1.0.0",
    "source_name_rule": "filename_date_v1",
    "source_context_rule": "legal_taxonomy_v1",
    "effective_from_source": "file_name_or_mtime",
    "legal_category": "法律",
    "legal_subcategory": "法律",
    "legal_topic": "刑法",
    "chunk_mode": "article",
    "chunk_rule_version": "article_regex_v2"
  }
}
```

## 3. `manifest.json`

### 3.1 字段定义

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `input_path` | `string` | 本次执行的输入路径 |
| `output_path` | `string` | 本次执行的输出路径 |
| `generated_at` | `string` | 生成时间，UTC ISO 8601 |
| `recursive` | `boolean` | 是否递归扫描 |
| `candidate_files` | `integer` | 候选文件数 |
| `processed_files` | `integer` | 成功产出法条的文件数 |
| `failed_files` | `integer` | 失败文件数 |
| `article_count` | `integer` | 法条总数 |
| `failed_reasons` | `object` | 失败原因统计 |
| `cli_args` | `object` | CLI 元数据覆盖项 |

## 4. `failed_files.jsonl`

### 4.1 字段定义

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `source_file` | `string` | 失败文件的相对来源路径 |
| `source_file_type` | `string` | 失败文件类型 |
| `reason_code` | `string` | 稳定错误码 |
| `reason_message` | `string` | 人类可读错误信息 |

### 4.2 常见错误码

| 错误码 | 含义 |
| --- | --- |
| `doc_requires_preconversion` | `.doc` 必须先转 `.docx` |
| `invalid_classification_path` | 不在至少两级标准分类目录下 |
| `empty_extracted_text` | 提取后没有文本 |
| `no_article_detected` | 没有识别到 `第X条` |
| `unsupported_file_type` | 不支持的文件类型 |
| `text_decode_failed` | 文本文件解码失败 |
| `unexpected_error` | 未预期异常 |
