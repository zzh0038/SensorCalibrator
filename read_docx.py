from docx import Document
import sys

# 设置输出编码
sys.stdout.reconfigure(encoding='utf-8')

doc = Document(r'D:\公司文件\软件开发\房屋安全智能监测系统搭建与开发.docx')

print("=" * 80)
print("文档中的表格内容（指令集部分）:")
print("=" * 80)

# 读取所有表格
for table_idx, table in enumerate(doc.tables):
    print(f"\n--- 表格 {table_idx + 1} ---")
    for row in table.rows:
        row_data = []
        for cell in row.cells:
            row_data.append(cell.text.strip())
        print(" | ".join(row_data))
