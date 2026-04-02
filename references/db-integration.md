# 数据库对接建议

> 更新日期：2026-04-02

## 1. 设计原则

本 skill 只负责输出稳定的中间契约，不直接绑定数据库实现。

推荐把 `articles.jsonl` 视为“库前中间层”，优点是：

- 切片逻辑与数据库解耦
- 关系库与向量库可以独立重建
- 大模型与 ETL 脚本共用同一份标准数据
- 迁移到新存储时不必重跑全文切片

## 2. 关系型数据库映射建议

### 2.1 推荐主表字段

| JSONL 字段 | 关系表字段 | 说明 |
| --- | --- | --- |
| `chunk_id` | `chunk_id` | 主键 |
| `version_id` | `version_id` | 唯一版本键 |
| `law_name` | `law_name` | 法规名称 |
| `law_name_norm` | `law_name_norm` | 归一化法规名称 |
| `article_no` | `article_no` | 法条编号 |
| `article_no_norm` | `article_no_norm` | 归一化法条编号 |
| `citation_text` | `citation_text` | 法条正文 |
| `content_hash` | `content_hash` | 正文哈希 |
| `authority_name` | `authority_name` | 主管机关 |
| `legal_category` | `legal_category` | 一级法律分类 |
| `legal_subcategory` | `legal_subcategory` | 二级法律分类 |
| `legal_topic` | `legal_topic` | 三级专题分类 |
| `status` | `status` | 法规状态 |
| `effective_from` | `effective_from` | 生效时间 |
| `effective_to` | `effective_to` | 失效时间 |
| `is_current` | `is_current` | 当前版本标记 |
| `source_file` | `source_file` | 来源文件 |
| `source_file_type` | `source_file_type` | 来源文件类型 |
| `chunk_mode` | `chunk_mode` | 切片模式 |
| `chunk_rule_version` | `chunk_rule_version` | 切片规则版本 |
| `embedding_text` | `embedding_text` | 向量化文本 |
| `metadata_tags` | `metadata_tags` | JSON 扩展标签 |

### 2.2 推荐索引

- 唯一索引：`version_id`
- 普通索引：`law_name`
- 普通索引：`law_name_norm`
- 普通索引：`article_no`
- 普通索引：`article_no_norm`
- 普通索引：`status`
- 普通索引：`effective_from`
- 普通索引：`legal_category`
- 普通索引：`legal_subcategory`
- 普通索引：`legal_topic`

### 2.3 版本策略建议

当前 skill 输出的 `version_id` 已经由以下信息稳定计算：

- 归一化法规名
- 归一化法条号
- 生效日期
- 正文哈希

因此推荐：

- 把 `version_id` 视为“版本唯一键”
- 把 `chunk_id` 视为“当前输出主键”
- 后续若要做 SCD2，可直接基于 `version_id` 扩展

## 3. 向量数据库映射建议

### 3.1 建议写入内容

向量库写入时建议使用：

- 向量输入文本：`embedding_text`
- 主键：`chunk_id`
- 元数据：`metadata_tags` + 若干顶层关键字段

### 3.2 推荐元数据最小集

建议至少写入以下元数据：

- `version_id`
- `law_name`
- `law_name_norm`
- `article_no`
- `article_no_norm`
- `legal_category`
- `legal_subcategory`
- `legal_topic`
- `status`
- `effective_from`
- `effective_to`
- `source_file`
- `chunk_rule_version`

### 3.3 适配不同向量库的建议

#### Milvus

- 主键：`chunk_id`
- 向量字段：embedding 向量
- 过滤字段：可从 `metadata_tags` 展平为标量字段

#### Qdrant

- `id`：`chunk_id`
- `vector`：embedding 向量
- `payload`：整份 `metadata_tags` + 核心顶层字段

#### pgvector

- 主表存结构化字段
- 单独向量列存 embedding
- 查询时联合结构化过滤字段

## 4. 大模型工作流建议

如果让大模型继续消费 `articles.jsonl`，推荐流程如下：

1. 先读取 `manifest.json`
2. 检查 `failed_files.jsonl`
3. 按 `law_name + article_no` 组织法条上下文
4. 需要向量化时使用 `embedding_text`
5. 需要过滤时使用 `metadata_tags`

## 5. 不建议的做法

以下做法不建议在 v1 中直接耦合到 skill：

- 把切片脚本直接写死为某个数据库方言
- 在切片时直接生成向量并入某个固定向量库
- 把业务规则硬编码到数据库写入器里
- 把主项目内部模型类直接复制进来作为外部契约
