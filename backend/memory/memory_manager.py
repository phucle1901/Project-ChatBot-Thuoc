import os
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, 'long_term_memory.txt')
def get_all_memories():
    with open(file_path,'r',encoding='utf-8') as f:
        lines=f.read().split('\n')
        if len(lines)>0:
            numbered_lines = [f"{i+1}. {line}" for i, line in enumerate(lines)]
            return '\n'.join(numbered_lines)
        else :
            return "Chưa có thông tin nào trong bộ nhớ dài hạn."
def add_memory(new_memory):
    if not new_memory or not new_memory.strip():
        return get_all_memories()
    with open(file_path,'a',encoding='utf-8') as f: 
        f.write(new_memory + '\n')
        return get_all_memories()
def update_memory(line_number, new_content):
    if not new_content or not new_content.strip():
        return get_all_memories()
    with open(file_path,'a',encoding='utf-8') as f: 
        lines=f.read().split('\n')
    index=int(line_number)-1
    if 0<=index<=len(lines):
        lines[index]=new_content
        with open(file_path,'w',encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        return get_all_memories 
    else:
        return f"Lỗi: Dòng {line_number} không tồn tại. Có {len(lines)} dòng."
def delete_memory(line_number):
    """Xóa dòng tại vị trí cụ thể (1-indexed)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.read().split('\n')
        
        index = int(line_number) - 1  # Convert to 0-indexed
        if 0 <= index < len(lines):
            deleted = lines.pop(index)
            with open(file_path, 'w', encoding='utf-8') as f:
                if lines:
                    f.write('\n'.join(lines) + '\n')
                else:
                    f.write('')
            return get_all_memories()
        else:
            return f"Lỗi: Dòng {line_number} không tồn tại. Có {len(lines)} dòng."
    except Exception as e:
        return f"Lỗi khi xóa: {str(e)}"
