import shutil
from PIL import Image
import colorsys
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def process_color_variation(params):
    """
    1つの色相・彩度の組み合わせに対する画像処理を行う
    
    :param params: (image_path, img_data, img_size, hue_step, sat_step, hue_increment, saturation_increment)
    :return: (output_path, new_img)
    """
    image_path, data, img_size, hue_step, sat_step, hue_increment, saturation_increment = params
    
    new_data = []
    current_hue = (hue_step * hue_increment) / 360.0
    current_sat = (sat_step + 1) * saturation_increment
    
    for item in data:
        if item[3] == 0:
            new_data.append(item)
            continue
        
        r, g, b = item[:3]
        h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
        
        h = (h + current_hue) % 1.0
        s = min(s * current_sat, 1.0)
        
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        
        new_data.append((
            int(r * 255),
            int(g * 255),
            int(b * 255),
            item[3]
        ))
    
    new_img = Image.new('RGBA', img_size)
    new_img.putdata(new_data)
    
    filename = os.path.basename(image_path)
    name, ext = os.path.splitext(filename)
    output_dir = os.path.join('output', name)
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, f"{name}_hue{hue_step}_sat{sat_step}.png")
    new_img.save(output_path)
    
    return output_path

def adjust_image_color(image_path, hue_steps=10, saturation_steps=3, max_workers=None):
    """
    指定された色相と彩度の段階数に基づいて画像の色バリエーションを生成（マルチスレッド版）
    
    :param image_path: 元画像のパス
    :param hue_steps: 色相の段階数
    :param saturation_steps: 彩度の段階数
    :param max_workers: 最大スレッド数（Noneの場合はCPUコア数×5）
    :return: 生成された画像のパスのリスト
    """
    img = Image.open(image_path).convert('RGBA')
    data = img.getdata()
    img_size = img.size
    
    hue_increment = 360 / hue_steps
    saturation_increment = 1.0 / saturation_steps
    
    # 全ての組み合わせのパラメータを生成
    params_list = [
        (image_path, data, img_size, hue_step, sat_step, hue_increment, saturation_increment)
        for hue_step in range(hue_steps)
        for sat_step in range(saturation_steps)
    ]
    
    generated_images = []
    total_variations = len(params_list)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 進捗バーを表示しながら並列処理を実行
        futures = [executor.submit(process_color_variation, params) for params in params_list]
        
        for future in tqdm(as_completed(futures), total=total_variations, 
                         desc="画像バリエーション生成中", unit="枚"):
            try:
                output_path = future.result()
                generated_images.append(output_path)
            except Exception as e:
                print(f"処理中にエラーが発生: {str(e)}")
    
    return generated_images

def process_input_folder(input_folder='input', hue_steps=10, saturation_steps=3, max_workers=None):
    """
    入力フォルダ内のすべてのPNG画像を処理
    
    :param input_folder: 入力画像が格納されているフォルダ
    :param hue_steps: 色相の段階数
    :param saturation_steps: 彩度の段階数
    :param max_workers: 最大スレッド数
    """
    os.makedirs('output', exist_ok=True)
    
    png_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.png')]
    
    for filename in tqdm(png_files, desc="画像処理中", unit="ファイル"):
        image_path = os.path.join(input_folder, filename)
        print(f"\n画像を処理中: {image_path}")
        
        generated_images = adjust_image_color(
            image_path,
            hue_steps=hue_steps,
            saturation_steps=saturation_steps,
            max_workers=max_workers
        )
        
        name, _ = os.path.splitext(filename)
        output_dir = os.path.join('output', name)
        os.makedirs(output_dir, exist_ok=True)
        shutil.copy2(image_path, os.path.join(output_dir, filename))
        
        os.remove(image_path)
    
    print("\n全ての画像の処理が完了しました。")

def main():
    """
    コマンドラインから引数を受け取り、画像処理を実行
    """
    parser = argparse.ArgumentParser(description='PNG画像の色相と彩度を変更（マルチスレッド版）')
    parser.add_argument('--hue_steps', type=int, default=10,
                      help='色相の段階数 (デフォルト: 10)')
    parser.add_argument('--saturation_steps', type=int, default=3,
                      help='彩度の段階数 (デフォルト: 3)')
    parser.add_argument('--max_workers', type=int, default=None,
                      help='最大スレッド数 (デフォルト: CPUコア数×5)')
    
    args = parser.parse_args()
    
    process_input_folder(
        hue_steps=args.hue_steps,
        saturation_steps=args.saturation_steps,
        max_workers=args.max_workers
    )

if __name__ == '__main__':
    main()