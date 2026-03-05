from docx import Document
import sys

# 设置输出编码
sys.stdout.reconfigure(encoding='utf-8')

def main():
    if len(sys.argv) < 2:
        print("Usage: python read_docx.py <path_to_docx>")
        print("Example: python read_docx.py 'document.docx'")
        sys.exit(1)
    
    doc_path = sys.argv[1]
    try:
        doc = Document(doc_path)
    except FileNotFoundError:
        print(f"Error: File not found: {doc_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading document: {e}")
        sys.exit(1)
    
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


if __name__ == "__main__":
    main()
