# legal-regulation-slicer-skill

> 更新日期：2026-04-02

`legal-regulation-slicer-skill` 用于把中文法律法规文本稳定切成法条级 JSONL 记录，并按标准法律法规分类目录输出分类字段，作为关系型数据库、向量数据库和 RAG 法律知识库的中间产物。

如果你是给 Agent使用，请先看 [SKILL.md](SKILL.md)。如果你是手工运行 CLI，请从本文档开始。

## 适用场景

适合以下任务：

- 将法律、行政法规、部门规章、办法、规定等文本切成法条级记录
- 从单文件或目录批量生成标准化 `articles.jsonl`
- 为后续数据库入库、向量化、RAG 检索准备稳定中间层
- 希望默认从标准法律法规分类目录推断分类字段

当前不适合以下任务：

- 扫描版 PDF 的 OCR 增强
- 章/节级重构而非法条级切片
- 直接写入 MySQL、PostgreSQL、Milvus、Qdrant 或 pgvector
- 自动判断法规是否废止、修订、失效

## 输入与输出

支持输入：

- `.docx`
- `.pdf`
- `.txt`
- `.md`

不支持原生解析：

- `.doc`

标准输出：

- `articles.jsonl`
- `manifest.json`
- `failed_files.jsonl`

其中：

- `articles.jsonl`：每行一条法条记录
- `manifest.json`：本次执行的统计摘要
- `failed_files.jsonl`：失败文件与失败原因

## 安装

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

安装基础依赖：

```bash
pip install -r requirements.txt
```

如需为后续 OCR 扩展预装依赖，可额外执行：

```bash
pip install -r requirements-ocr.txt
```

注意：当前版本不会自动执行 OCR，`requirements-ocr.txt` 只是预留扩展位。

## 快速开始

单文件：

```bash
python scripts/slice_regulations.py --input ./samples/示例办法_20240102.docx --output ./output
```

目录递归：

```bash
python scripts/slice_regulations.py --input ./samples --output ./output --recursive
```

仅在默认分类推断不正确，或直接处理单文件时，才传入覆盖参数：

```bash
python scripts/slice_regulations.py --input ./samples --output ./output --recursive --legal-category 法律 --legal-subcategory 法律 --legal-topic 刑法
```

查看完整参数：

```bash
python scripts/slice_regulations.py --help
```

## 分类字段推断

默认优先从文件名和标准分类目录推断元数据：

- 文件名 -> `law_name`、`effective_from`
- 一级目录 -> `legal_category`
- 二级目录 -> `legal_subcategory`
- 三级目录 -> `legal_topic`

推荐目录结构：

```text
samples/
└─ 法律/
   └─ 法律/
      └─ 刑法/
         └─ 示例办法_20240102.docx
```

二级目录结构也有效，例如：

```text
samples/
└─ 行政法规/
   └─ 行政法规/
      └─ 示例条例_20240102.docx
```

这时 `legal_topic` 会写为 `null`。

推荐文件名格式：

```text
法规名称_YYYYMMDD.<ext>
```

例如：

- `示例办法_20240102.docx`
- `专项规定_20231201.md`

如果文件名不匹配推荐格式：

- `law_name` 退化为去掉扩展名后的文件名
- `effective_from` 退化为文件最后修改日期

如果输入文件不在至少两级标准分类目录下，则会写入 `failed_files.jsonl`，错误码为 `invalid_classification_path`。直接处理单文件时，建议显式传入 `--legal-category` 与 `--legal-subcategory`。

## 切片规则

会识别：

- `第X条`
- `第X条之Y`

会忽略：

- `目录`
- `第X章`
- `第X节`

正文跨行时，会持续拼接到当前法条，直到出现下一条法条标题。

## `.doc` 文件处理

`.doc` 不做原生解析，会统一记入 `failed_files.jsonl`，并使用错误码 `doc_requires_preconversion`。

推荐流程：

```text
.doc -> .docx -> 重新运行切片
```

这样做是为了避免对 Word、LibreOffice 或 COM 链路产生运行时依赖，保证批量处理更稳定。

## 输出契约与对接

如需字段级说明，请看：

- [references/output-schema.md](references/output-schema.md)

如需数据库与向量库对接建议，请看：

- [references/db-integration.md](references/db-integration.md)

推荐做法是把 `articles.jsonl` 当作稳定中间层，而不是让切片脚本直接绑定具体数据库。

## 验证

运行项目测试：

```bash
python -m pytest tests -q
```

Windows 下运行外部 skill 校验器时，建议显式开启 UTF-8 模式：

```powershell
$env:PYTHONUTF8 = "1"
python C:/Users/sxyt0/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

## 项目结构

```text
legal-regulation-slicer-skill/
├─ README.md
├─ SKILL.md
├─ requirements.txt
├─ requirements-ocr.txt
├─ agents/
├─ scripts/
│  └─ slice_regulations.py
├─ src/
│  └─ legal_regulation_slicer/
├─ references/
│  ├─ output-schema.md
│  └─ db-integration.md
└─ tests/
```

## 常见问题

### 为什么扫描版 PDF 没有切出法条？

因为当前版本按可提取文本的 PDF 处理，不自动执行 OCR。

### 为什么文件会出现在 `failed_files.jsonl`？

常见原因包括：

- 输入文件是 `.doc`
- 输入文件不在至少两级标准分类目录下
- 抽取出的文本为空
- 文本中没有识别到法条标题
- 文件编码无法解码

### 为什么不直接写数据库？

因为这个项目的目标是提供稳定切片和稳定中间契约，让同一份产物可以复用于数据库入库、向量化和知识库重建流程。
