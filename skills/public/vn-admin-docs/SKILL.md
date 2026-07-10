---
name: vn-admin-docs
description: "Vietnamese administrative document templates (Decree 30/2020/NĐ-CP) and tooling. Use whenever creating Công văn, Quyết định, Tờ trình, Báo cáo, Thông báo, hợp đồng, or any formal Vietnamese .docx deliverable. Provides pre-built compliant templates, a token-fill script, and a compliance audit script. ALWAYS prefer filling a template over building document formatting from scratch."
---

# vn-admin-docs — Văn bản hành chính Việt Nam

## Nguyên tắc cốt lõi
KHÔNG tự dựng thể thức từ đầu. Thể thức đã được bake sẵn trong template
(khổ A4, lề, font, bố cục header 2 cột). Nhiệm vụ của agent chỉ là:
soạn NỘI DUNG → điền vào token → audit → giao.

## Cấu trúc
```
vn-admin-docs/
├── SKILL.md                  # file này
├── templates/
│   └── cong_van.docx         # Công văn — chuẩn NĐ 30/2020/NĐ-CP
└── scripts/
    ├── fill_template.py      # điền {{TOKEN}} từ JSON, giữ nguyên format
    └── audit_docx.py         # kiểm tra tuân thủ NĐ30 (A4, lề, font, token sót)
```

## Quy trình chuẩn (4 lệnh)
```bash
# 1. Soạn dữ liệu — metadata thiếu thì để "[...]" và báo user, KHÔNG bịa
cat > /tmp/data.json << 'EOF'
{
  "CO_QUAN_CHU_QUAN":  "TÊN CƠ QUAN CẤP TRÊN (in hoa)",
  "CO_QUAN_BAN_HANH":  "TÊN CƠ QUAN BAN HÀNH (in hoa)",
  "SO_KY_HIEU":        "[...]/CV-XXX",
  "TRICH_YEU":         "nội dung trích yếu (chữ thường, không dấu chấm cuối)",
  "DIA_DANH":          "[Địa danh]",
  "NGAY": "[..]", "THANG": "[..]", "NAM": "[....]",
  "KINH_GUI":          "Tên cơ quan/đơn vị nhận",
  "NOI_DUNG":          "Đoạn 1.\nĐoạn 2.\nTrân trọng./.",
  "DON_VI_LUU":        "tên viết tắt đơn vị soạn thảo",
  "QUYEN_HAN_CHUC_VU": "CHỨC VỤ NGƯỜI KÝ (in hoa; thêm TM./KT./TL. nếu có)",
  "HO_TEN_NGUOI_KY":   "[Họ và tên]"
}
EOF

# 2. Điền template
python3 scripts/fill_template.py \
  --template templates/cong_van.docx \
  --data /tmp/data.json \
  --out /mnt/user-data/outputs/<ten_file>.docx

# 3. Audit tuân thủ (exit 0 = pass)
python3 scripts/audit_docx.py /mnt/user-data/outputs/<ten_file>.docx

# 4. Render kiểm tra bằng mắt
soffice --headless --convert-to pdf --outdir /tmp <file>.docx
pdftoppm -jpeg -r 100 /tmp/<file>.pdf /tmp/page   # rồi xem ảnh /tmp/page-1.jpg
```

## Ghi chú NOI_DUNG
- Xuống dòng bằng `\n` — mỗi dòng thành một đoạn riêng, tự thừa hưởng
  format chuẩn (Times New Roman 13pt, giãn dòng, thụt đầu dòng 1,27cm,
  canh đều 2 lề).
- Câu kết công văn kết thúc bằng `./.`

## Đặc thù từng loại văn bản
- **Công văn**: KHÔNG có tên loại văn bản (không ghi chữ "CÔNG VĂN").
  Trích yếu "V/v ..." nằm dưới Số/ký hiệu ở cột trái header, cỡ 12-13.
- **Quyết định / Tờ trình / Báo cáo** (template bổ sung sau): CÓ tên loại
  in hoa đậm giữa trang + trích yếu bên dưới; Quyết định có phần
  "Căn cứ ..." và bố cục Điều 1/2/3.
- **Hợp đồng (HĐLĐ...)**: KHÔNG thuộc phạm vi NĐ 30 — dùng template nhóm
  biểu mẫu doanh nghiệp, không áp cứng specs NĐ30 (audit có thể WARN
  về cỡ chữ, chấp nhận được).

## Quy tắc an toàn
- Token thiếu dữ liệu → giữ nguyên dạng `[...]`, liệt kê trong báo cáo
  giao hàng. KHÔNG tự bịa số văn bản, tên người ký, ngày tháng, căn cứ
  pháp lý.
- Không sửa file template gốc; luôn ghi ra file mới.
- audit_docx.py exit != 0 → sửa cho pass rồi mới giao, không được bỏ qua.
