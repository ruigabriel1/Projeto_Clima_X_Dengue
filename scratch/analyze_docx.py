import zipfile
import sys
import xml.etree.ElementTree as ET

def analyze_docx(filepath):
    try:
        with zipfile.ZipFile(filepath, 'r') as z:
            # Check for images
            media_files = [f for f in z.namelist() if f.startswith('word/media/')]
            
            # Read document.xml
            doc_xml = z.read('word/document.xml')
            
            root = ET.fromstring(doc_xml)
            
            # namespaces
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            tables = root.findall('.//w:tbl', ns)
            
            print(f"Total de Imagens/Gráficos encontrados: {len(media_files)}")
            for m in media_files:
                print(f" - {m}")
                
            print(f"\nTotal de Tabelas encontradas: {len(tables)}")
            
            for i, tbl in enumerate(tables):
                print(f"\nTabela {i+1}:")
                # get all text in the first row or first few cells to give a preview
                rows = tbl.findall('.//w:tr', ns)
                if rows:
                    for row in rows[:2]: # First 2 rows for context
                        cells = row.findall('.//w:tc', ns)
                        row_text = []
                        for cell in cells:
                            texts = cell.findall('.//w:t', ns)
                            cell_text = "".join([t.text for t in texts if t.text])
                            row_text.append(cell_text.strip())
                        print(" | ".join(row_text))
                        
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")

if __name__ == "__main__":
    analyze_docx(sys.argv[1])
