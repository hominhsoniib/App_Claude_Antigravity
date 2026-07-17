import os
import math
from PIL import Image, ImageDraw, ImageFont

def get_font(font_size=12, bold=False):
    font_path = r"C:\Windows\Fonts\arial.ttf"
    if bold:
        font_path = r"C:\Windows\Fonts\arialbd.ttf"
    if os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, font_size)
        except Exception:
            pass
    return ImageFont.load_default()

def get_stamp_and_signature_path(date_str=None):
    """
    Tạo con dấu đỏ của OMRI Group và chữ ký của Giám đốc dạng file PNG nền trong suốt.
    Trả về đường dẫn tuyệt đối đến file PNG.
    """
    export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
    os.makedirs(export_dir, exist_ok=True)
    file_path = os.path.join(export_dir, "omri_approved_stamp.png")
    
    # Tạo ảnh 200x200 nền trong suốt (RGBA)
    img = Image.new("RGBA", (200, 200), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    red_color = (220, 38, 38, 255)  # Màu đỏ dấu
    blue_color = (29, 78, 216, 255) # Màu xanh mực bút bi ký
    
    # 1. Vẽ vòng tròn ngoài và vòng tròn trong
    draw.ellipse([10, 10, 190, 190], outline=red_color, width=4)
    draw.ellipse([20, 20, 180, 180], outline=red_color, width=1)
    
    font_bold = get_font(11, bold=True)
    font_normal = get_font(9, bold=False)
    font_center = get_font(13, bold=True)
    
    # 2. Vẽ chữ trung tâm
    draw.text((100, 75), "ĐÃ DUYỆT", fill=red_color, font=font_center, anchor="mm")
    
    if date_str:
        draw.text((100, 95), date_str, fill=red_color, font=font_normal, anchor="mm")
    else:
        draw.text((100, 95), "OMRI GROUP", fill=red_color, font=font_bold, anchor="mm")
        
    company_text = "CÔNG TY CỔ PHẦN OMRI GROUP"
    location_text = "* M.S.D.N: 0312345678 *"
    
    # Hàm vẽ chữ xoay quanh tâm
    def draw_curved_text(text, radius, start_angle, step_angle, is_top=True):
        for i, char in enumerate(text):
            angle = start_angle + i * step_angle
            rad = math.radians(angle)
            x = 100 + radius * math.cos(rad)
            y = 100 + radius * math.sin(rad)
            
            char_img = Image.new("RGBA", (40, 40), (255, 255, 255, 0))
            char_draw = ImageDraw.Draw(char_img)
            char_draw.text((20, 20), char, fill=red_color, font=font_bold, anchor="mm")
            
            rotate_angle = -angle - 90 if is_top else -angle + 90
            rotated = char_img.rotate(rotate_angle, resample=Image.Resampling.BILINEAR)
            
            w, h = rotated.size
            img.paste(rotated, (int(x - w/2), int(y - h/2)), rotated)

    try:
        # Vòng trên: chữ xoay theo hướng đỉnh đầu
        draw_curved_text(company_text, 62, -155, 11, is_top=True)
        # Vòng dưới: chữ xoay theo hướng đáy
        draw_curved_text(location_text, 62, 25, 12, is_top=False)
    except Exception:
        # Dự phòng nếu không hỗ trợ thư viện ảnh đầy đủ
        draw.text((100, 45), "CÔNG TY CP OMRI GROUP", fill=red_color, font=font_bold, anchor="mm")
        draw.text((100, 155), "MSDN: 0312345678", fill=red_color, font=font_bold, anchor="mm")
    
    # 3. Vẽ nét ký tay nghệ thuật chồng lên dấu (màu xanh mực)
    sig_points = [
        (55, 110), (70, 95), (85, 115), (95, 75), (110, 130), 
        (125, 90), (140, 110), (165, 95), (180, 105)
    ]
    for i in range(len(sig_points) - 1):
        draw.line([sig_points[i], sig_points[i+1]], fill=blue_color, width=3)
        
    # Tên viết tay ở góc dưới chữ ký
    draw.text((120, 132), "An", fill=blue_color, font=get_font(13, bold=True))
    
    img.save(file_path, "PNG")
    return file_path
