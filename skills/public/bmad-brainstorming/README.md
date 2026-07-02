# bmad-brainstorming (packaged skill)

Skill brainstorming BMad đóng gói self-contained để import vào LLM custom.

## Cấu trúc

```
bmad-brainstorming/
├── SKILL.md            # Entry: metadata + trỏ tới workflow.md
├── workflow.md         # Workflow chính, đọc trước
├── config.yaml         # Schema template (values rỗng) — KHÔNG cứng giá trị
├── template.md         # Template file output session
├── brain-methods.csv   # Thư viện kỹ thuật brainstorming (load on-demand)
└── steps/              # Micro-file mỗi bước
    ├── step-01-session-setup.md
    ├── step-01b-continue.md
    ├── step-02a-user-selected.md
    ├── step-02b-ai-recommended.md
    ├── step-02c-random-selection.md
    ├── step-02d-progressive-flow.md
    ├── step-03-technique-execution.md
    └── step-04-idea-organization.md
```

## Import

1. Nạp `SKILL.md` làm điểm vào. Nó trỏ tới `workflow.md`.
2. Mọi path nội bộ là tương đối trong thư mục skill (`./config.yaml`, `../template.md`, `../brain-methods.csv`) — giữ nguyên cấu trúc.
3. Trigger: user nói "help me brainstorm" / "help me ideate".

## Config behavior

- KHÔNG có config cứng. Mỗi session mới, skill LUÔN hỏi user setup config trước (step-01 Step 0): tên, project, ngôn ngữ, output language, skill level, output folder.
- `config.yaml` chỉ là schema template (values rỗng), document các key — không phải nguồn giá trị.
- Skill HALT chờ user xác nhận config xong mới chạy phần brainstorming.

## Khác bản gốc

- Config đổi từ `{project-root}/_bmad/core/config.yaml` (load cứng) → hỏi user runtime mỗi session.
