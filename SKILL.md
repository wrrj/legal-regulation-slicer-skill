---
name: legal-regulation-slicer-skill
description: 适用于需要将中文法律法规或政策类文本切分为法条级 JSONL 记录的场景，可用于 RAG、向量数据库或关系型数据库入库准备。支持 docx、pdf、txt、md 输入，默认从标准法律法规分类目录推断 `legal_category`、`legal_subcategory`、`legal_topic`。
---

# legal-regulation-slicer-skill

## 何时使用

当任务目标是把中文法律法规文本切成法条级结构化记录，而不是做 OCR 增强或直接写数据库时，使用这个 skill。

- 输入可以是单文件，也可以是目录
- 支持输入：`.docx`、`.pdf`、`.txt`、`.md`
- 不支持的 legacy 格式：`.doc`
- 主要输出：`articles.jsonl`、`manifest.json`、`failed_files.jsonl`

如果任务主要是扫描版 PDF OCR、按章节而非法条重构，或直接写 MySQL/PostgreSQL/Milvus/Qdrant，则不要使用这个 skill。

## 默认流程

1. 先确认输入是单文件还是目录。只有在需要递归扫描目录时才加 `--recursive`。
2. 默认让切片器根据文件名和标准法律法规分类目录推断元数据。只有推断结果不对，或输入是单文件时，才传覆盖参数。
3. 先执行默认命令：

```bash
python scripts/slice_regulations.py --input <文件或目录> --output <输出目录> [--recursive]
```

4. 只有必要时再补覆盖参数：

```bash
python scripts/slice_regulations.py --input <文件或目录> --output <输出目录> [--recursive] [--legal-category <值>] [--legal-subcategory <值>] [--legal-topic <值>] [--authority-default <值>]
```

5. 检查生成结果：
- `manifest.json`：候选文件数、成功数、失败数、法条总数
- `failed_files.jsonl`：失败文件与失败原因，例如 `doc_requires_preconversion`、`empty_extracted_text`、`no_article_detected`
- `articles.jsonl`：每行一条法条记录

## 切片与分类规则

- 识别 `第X条`、`第X条之Y` 这类法条标题
- 忽略 `目录`、`第X章`、`第X节` 这类结构标题
- 如果法条正文跨行，持续拼接到下一条法条出现为止
- 默认按以下方式推断分类字段：
  - 文件名 -> `law_name`、`effective_from`
  - 一级目录 -> `legal_category`
  - 二级目录 -> `legal_subcategory`
  - 三级目录 -> `legal_topic`
- 只有二级目录时，`legal_topic` 为 `null`
- 少于两级分类目录时，返回 `invalid_classification_path`

legacy `.doc` 文件不会被解析，而是写入 `failed_files.jsonl` 并使用 `doc_requires_preconversion`。先转成 `.docx`，再重新执行切片。

## 按需加载

只有在任务需要更细节时，再打开下面这些文件：

- [scripts/slice_regulations.py](scripts/slice_regulations.py)：查看 CLI 参数和执行流程
- [references/output-schema.md](references/output-schema.md)：查看字段级 schema、`embedding_text`、`metadata_tags`
- [references/db-integration.md](references/db-integration.md)：查看关系库、向量库与 RAG 的对接映射

## 验证

先运行项目测试：

```bash
python -m pytest tests -q
```

在 Windows 下运行外部 skill 校验器前，先显式打开 UTF-8 模式：

```powershell
$env:PYTHONUTF8 = "1"
python C:/Users/sxyt0/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

如果任务只是确认 CLI 用法，`python scripts/slice_regulations.py --help` 是最快的接口检查方式。
