import os
from lxml import etree

# ==========================================
# 1. CÁC HÀM XỬ LÝ ASCII PORTRAIT (MỚI)
# ==========================================

def load_ascii_portrait(path="ascii_portrait.txt"):
    """Đọc file ASCII chân dung và căn lề phải (pad spaces) cho đều các dòng."""
    if not os.path.exists(path):
        print(f"Cảnh báo: Không tìm thấy file {path}")
        return []
        
    with open(path, "r", encoding="utf-8") as f:
        rows = f.read().splitlines()
        
    if not rows:
        return []
        
    max_w = max(len(r) for r in rows)
    return [r.ljust(max_w) for r in rows]

def inject_ascii_portrait(root, rows, prefix="ascii_row_"):
    """Bơm từng dòng ASCII vào các thẻ <tspan> tương ứng trong SVG."""
    # Xóa sạch các dòng cũ để tránh bị dính rác nếu ảnh mới ngắn hơn ảnh cũ
    for el in root.iter():
        elem_id = el.get("id", "")
        if elem_id.startswith(prefix):
            el.text = ""
            
    # Bơm dữ liệu từng dòng vào SVG
    for i, row in enumerate(rows):
        elem_id = f"{prefix}{i:02d}"
        element = root.find(f".//*[@id='{elem_id}']")
        if element is not None:
            element.text = row

# ==========================================
# 2. CÁC HÀM XỬ LÝ SVG (CŨ + NÂNG CẤP)
# ==========================================

def justify_format(root, element_id, data, length=0):
    """
    (Hàm này là từ code gốc của bạn, dùng để điền text vào SVG)
    Đảm bảo bạn dán code gốc của hàm này vào đây.
    """
    element = root.find(f".//*[@id='{element_id}']")
    if element is not None:
        # Ví dụ logic ljust gốc của bạn
        element.text = str(data).ljust(length) if length > 0 else str(data)

def svg_overwrite(filename, age_data, commit_data, star_data, repo_data,
                  contrib_data, follower_data, loc_data, ascii_rows=None):
    """Đọc file SVG template, ghi đè các chỉ số GitHub và chèn ảnh chân dung ASCII."""
    tree = etree.parse(filename)
    root = tree.getroot()
    
    # --- Điền dữ liệu thống kê (Code cũ) ---
    justify_format(root, 'commit_data',  commit_data,  22)
    justify_format(root, 'star_data',    star_data,    14)
    justify_format(root, 'repo_data',    repo_data,     6)
    justify_format(root, 'contrib_data', contrib_data)
    justify_format(root, 'follower_data',follower_data,10)
    
    # Lưu ý: Cấu trúc mảng loc_data của bạn có thể khác, hãy chỉnh sửa lại cho khớp
    justify_format(root, 'loc_data',     loc_data[2],   9) 
    justify_format(root, 'loc_add',      loc_data[0])
    justify_format(root, 'loc_del',      loc_data[1],   7)
    
    # --- Điền ảnh ASCII (Code mới) ---
    if ascii_rows:
        inject_ascii_portrait(root, ascii_rows)
        
    # Ghi lại thành file SVG hoàn chỉnh
    tree.write(filename, encoding='utf-8', xml_declaration=True)

# ==========================================
# 3. KHỐI THỰC THI CHÍNH
# ==========================================

if __name__ == "__main__":
    print("Bắt đầu cập nhật Neofetch cho GitHub Profile...")

    # TODO: Đặt đoạn code fetch dữ liệu từ GitHub API của bạn ở đây
    # Ví dụ:
    # age_data = fetch_age()
    # commit_data = fetch_commits()
    # star_data = fetch_stars()
    # repo_data = fetch_repos()
    # contrib_data = fetch_contribs()
    # follower_data = fetch_followers()
    # total_loc = [15000, 5000, 10000] # [Thêm, Xóa, Tổng]

    # --- Dữ liệu giả lập (Xóa phần này khi ghép với API thật của bạn) ---
    age_data = "2 yrs"
    commit_data = "1,024"
    star_data = "42"
    repo_data = "12"
    contrib_data = "5"
    follower_data = "100"
    total_loc = [1000, 200, 800] # Giả lập mảng loc
    # ---------------------------------------------------------------------

    # 1. Đọc file text chứa ảnh chân dung
    print("Đang tải ascii_portrait.txt...")
    ascii_rows = load_ascii_portrait("ascii_portrait.txt")
    
    if not ascii_rows:
        print("Lỗi: Không có dữ liệu ảnh ASCII. Vẫn tiếp tục ghi đè các thông số khác...")

    # 2. Ghi đè vào Dark Mode SVG
    if os.path.exists('dark_mode.svg'):
        print("Đang cập nhật dark_mode.svg...")
        svg_overwrite('dark_mode.svg', age_data, commit_data, star_data, repo_data,
                      contrib_data, follower_data, total_loc, ascii_rows)
    else:
        print("Không tìm thấy dark_mode.svg")

    # 3. Ghi đè vào Light Mode SVG
    if os.path.exists('light_mode.svg'):
        print("Đang cập nhật light_mode.svg...")
        svg_overwrite('light_mode.svg', age_data, commit_data, star_data, repo_data,
                      contrib_data, follower_data, total_loc, ascii_rows)
    else:
        print("Không tìm thấy light_mode.svg")

    print("Hoàn tất!")