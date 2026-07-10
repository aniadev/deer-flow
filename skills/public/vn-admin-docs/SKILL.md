---
name: vn-admin-docs
description: "Vietnamese administrative document templates (Decree 30/2020/NĐ-CP) and tooling. Use whenever creating Công văn, Quyết định, Tờ trình, Báo cáo, Thông báo, or any formal Vietnamese .docx deliverable. Provides pre-built compliant templates, a token-fill script, and a compliance audit script. ALWAYS prefer filling a template over building document formatting from scratch."
---

# vn-admin-docs — Văn bản hành chính Việt Nam

## Nguyên tắc cốt lõi
KHÔNG tự dựng thể thức từ đầu. Thể thức đã được bake sẵn trong template
(khổ A4, lề, font, bố cục header 2 cột). Nhiệm vụ của agent chỉ là:
soạn NỘI DUNG → điền token → audit → giao.

## Chọn template
| Loại văn bản | Template | Đặc thù |
|---|---|---|
| Công văn | `templates/cong_van.docx` | KHÔNG có tên loại; trích yếu "V/v" nằm dưới Số/ký hiệu ở cột trái header |
| Quyết định | `templates/quyet_dinh.docx` | Có THAM_QUYEN + CAN_CU (nghiêng) + "QUYẾT ĐỊNH:" + các Điều |
| Tờ trình | `templates/to_trinh.docx` | Tên loại + trích yếu giữa trang, có "Kính gửi" |
| Báo cáo | `templates/bao_cao.docx` | Tên loại + trích yếu giữa trang |
| Thông báo | `templates/thong_bao.docx` | Tên loại + trích yếu giữa trang |

## Token theo template
Chung (mọi template): `CO_QUAN_CHU_QUAN`, `CO_QUAN_BAN_HANH` (in hoa),
`SO_KY_HIEU`, `DIA_DANH`, `NGAY`, `THANG`, `NAM`, `TRICH_YEU`, `NOI_DUNG`,
`DON_VI_LUU`, `QUYEN_HAN_CHUC_VU` (in hoa), `HO_TEN_NGUOI_KY`.

Riêng:
- cong_van: `KINH_GUI`. (Nơi nhận cố định "- Như trên;")
- quyet_dinh: `THAM_QUYEN` (in hoa), `CAN_CU`, `NOI_NHAN`
- to_trinh: `KINH_GUI`, `NOI_NHAN`
- bao_cao / thong_bao: `NOI_NHAN`

## Quy trình chuẩn (4 lệnh)
```bash
# 1. Soạn dữ liệu — metadata thiếu thì để "[...]" và báo user, KHÔNG bịa
cat > /tmp/data.json << 'JSONEOF'
{ "SO_KY_HIEU": "[...]/QĐ-XXX", "NOI_DUNG": "Điều 1. ...\nĐiều 2. ...", ... }
JSONEOF

# 2. Điền template
python3 scripts/fill_template.py \
  --template templates/<loai>.docx --data /tmp/data.json \
  --out /mnt/user-data/outputs/<ten_file>.docx

# 3. Audit tuân thủ (exit 0 = pass)
python3 scripts/audit_docx.py /mnt/user-data/outputs/<ten_file>.docx

# 4. Render kiểm tra bằng mắt
soffice --headless --convert-to pdf --outdir /tmp <file>.docx
pdftoppm -jpeg -r 100 /tmp/<file>.pdf /tmp/page   # rồi XEM ảnh /tmp/page-1.jpg
```

## Quy tắc soạn nội dung token
- MỌI token đều hỗ trợ nhiều đoạn: xuống dòng bằng `\n`, mỗi dòng thành một
  đoạn riêng thừa hưởng format chuẩn của template.
- `NOI_DUNG` Quyết định: mỗi điều bắt đầu bằng "Điều N. " — script tự bôi
  đậm tiền tố. Điều cuối kết thúc bằng `./.`
- `CAN_CU` (Quyết định): mỗi căn cứ một dòng, kết thúc `;`, dòng cuối
  (thường "Theo đề nghị của ...") kết thúc `.` — tự render nghiêng.
- `NOI_NHAN`: mỗi nơi nhận một dòng dạng "- Tên nơi nhận;". Dòng
  "- Lưu: VT, ..." đã có sẵn trong template, không đưa vào token.
- Câu kết công văn/tờ trình kết thúc bằng `./.`
- `TRICH_YEU`: chữ thường, không dấu chấm cuối (template tự thêm
  "V/v " hoặc "Về việc ").

## Quy tắc an toàn
- Token thiếu dữ liệu → giữ nguyên dạng `[...]`, liệt kê trong báo cáo giao
  hàng. KHÔNG tự bịa số văn bản, tên người ký, ngày tháng, căn cứ pháp lý.
- Căn cứ pháp lý chưa được user cung cấp/xác nhận → ghi
  "[Căn cứ: ...]" và flag cho user.
- Không sửa file template gốc; luôn ghi ra file mới.
- audit_docx.py exit != 0 → sửa cho pass rồi mới giao, không bỏ qua.
- Hợp đồng (HĐLĐ...) KHÔNG thuộc phạm vi NĐ 30 — không áp cứng specs này.
