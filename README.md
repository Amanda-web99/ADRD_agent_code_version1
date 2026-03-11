# ADRD Agent Code

一个用于 **ADRD（阿尔茨海默病及相关痴呆）病历文本分析** 的多模块项目，支持从临床笔记中自动生成结构化判断结果，例如：

- 是否存在 ADRD（Yes / No / Uncertain）
- ADRD 亚型（AD / VaD / FTD / LBD / Mixed / Unspecified）
- 证据片段与高亮定位
- 时间线事件提取
- 前端可视化图表审核（Chart Review）

该仓库包含前端应用、两个后端实现（基础版与 skills 管线版），以及测试与提示词相关文件，便于迭代开发和研究。

## 项目结构

```text
ADRD_agent_code/
├── frontend/                 # React + Vite 前端，文件上传与结果可视化
├── backend/                  # 基础 FastAPI 后端（Diagnosis/Subtype 两个核心 Agent）
├── skills_backend/           # 技能管线版 FastAPI 后端（推荐主线）
├── Chart review vocabulary V2(summary vocabulary).csv
├── test_frontend.html
└── README.md
```

## 各模块说明

### 1) `frontend/`
- 技术栈：React + TypeScript + Vite。
- 主要功能：
  - 上传 Excel 病历数据（Patient ID + Notes）
  - 调用后端分析接口
  - 展示诊断结果、证据、文本高亮、时间线
- 默认请求地址：`http://localhost:8002`（见 `frontend/src/app/services/aiAgentService.ts`）。

### 2) `backend/`（基础版）
- 技术栈：FastAPI。
- 当前主要 Agent：`DiagnosisAgent`、`SubtypeAgent`。
- 主要接口：`/analyze`、`/analyze_text`。
- 适合快速验证基础分类逻辑。

### 3) `skills_backend/`（技能管线版，推荐）
- 技术栈：FastAPI + Pydantic + Gemini SDK。
- 管线流程：
  - `SectionParserSkill`
  - `KeywordRecallSkill`
  - `LLMDecisionSkill`
  - `ConfidenceCalibratorSkill`
  - `TimelineBuilderSkill`
  - `EvidenceLinkerSkill`
- 返回更完整、前端友好的结构化结果（证据、高亮、section、timeline、meta 等）。

## 快速启动（推荐路径）

### 1) 启动 `skills_backend`（端口 8002）

```bash
cd skills_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 首次运行请先配置 .env（至少包含 GOOGLE_API_KEY）
cp .env.example .env

PYTHONPATH=$(pwd) uvicorn app.main:app --reload --port 8002
```

### 2) 启动前端（新开一个终端）

```bash
cd frontend
npm install
npm run dev
```

启动后，前端将调用 `http://localhost:8002/analyze_text` 进行病历分析。

## 可选：启动基础 `backend`（端口 8001）

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

基础后端测试脚本：

```bash
cd backend
python run_tests.py
```

## 接口示例（skills_backend）

```bash
curl -X POST http://localhost:8002/analyze_text \
  -H "Content-Type: text/plain" \
  --data 'Family reports memory decline over 5 years. Diagnosed with Alzheimer disease in 2021. Started donepezil in 2022.'
```

## 适用场景

- ADRD 相关病历文本自动初筛
- 结构化证据提取与可视化审核
- 多 Agent / 多 Skill 医疗 NLP 流程验证
- 前后端联调与模型提示词迭代

## 注意事项

- 当前仓库用于开发与研究，请勿直接用于临床决策。
- 若处理真实医疗数据，请补齐隐私保护与合规要求（如 HIPAA/本地法规）。
- API Key、`.env`、患者敏感信息请勿上传到公开仓库。
