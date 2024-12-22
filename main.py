import os
import shutil
from PIL import Image
import colorsys
import argparse
from multiprocessing import Pool, cpu_count
from collections import defaultdict
import datetime

def process_image_with_params(args):
    """
    特定の画像、色相、彩度の組み合わせを処理
    RGBの変換結果をキャッシュして再利用
    """
    image_path, hue_step, sat_step, hue_steps, saturation_steps = args
    img = Image.open(image_path).convert('RGBA')
    data = img.getdata()
    
    print(f"{datetime.datetime.now()} start processing: " + image_path + " hue: " + str(hue_step) + " sat: " + str(sat_step))
    
    hue_increment = 360 / hue_steps
    saturation_increment = 1.0 / saturation_steps
    
    # RGBの変換結果をキャッシュするための辞書
    # キー: (r, g, b, current_hue, current_sat)
    # 値: (new_r, new_g, new_b)
    color_cache = {}
    
    new_data = []
    current_hue = (hue_step * hue_increment) / 360.0
    current_sat = (sat_step + 1) * saturation_increment
    
    # 出力先に既にフォルダと同一名のファイルが存在する場合はスキップ
    filename = os.path.basename(image_path)
    name, ext = os.path.splitext(filename)
    output_dir = os.path.join('output', name)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{name}_hue{hue_step}_sat{sat_step}.png")
    if os.path.exists(output_path):
        print(f"スキップ: {output_path} は既に存在します。")
        return
    
    # 色の出現頻度を数える（最適化のため）
    color_frequency = defaultdict(int)
    for item in data:
        if item[3] != 0 and not (item[0] == item[1] == item[2]):  # 透明でなく、グレースケールでもない
            color_frequency[item[:3]] += 1
    
    # 頻度順にソート
    sorted_colors = sorted(color_frequency.items(), key=lambda x: x[1], reverse=True)
    
    # 頻出色を先にキャッシュに登録
    for (r, g, b), _ in sorted_colors[:1000]:  # 上位1000色をプリキャッシュ
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        h = (h + current_hue) % 1.0
        s = min(s * current_sat, 1.0)
        new_r, new_g, new_b = colorsys.hsv_to_rgb(h, s, v)
        color_cache[(r, g, b)] = (
            int(new_r * 255),
            int(new_g * 255),
            int(new_b * 255)
        )
    
    for item in data:
        # 透明度0のピクセルはそのまま追加
        if item[3] == 0:
            new_data.append(item)
            continue
            
        # 彩度0（グレースケール）のピクセルはそのまま追加
        if item[0] == item[1] == item[2]:
            new_data.append(item)
            continue
        
        r, g, b = item[:3]
        
        # キャッシュにある場合はそれを使用
        if (r, g, b) in color_cache:
            new_r, new_g, new_b = color_cache[(r, g, b)]
        else:
            # キャッシュにない場合は計算して保存
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            h = (h + current_hue) % 1.0
            s = min(s * current_sat, 1.0)
            new_r, new_g, new_b = colorsys.hsv_to_rgb(h, s, v)
            new_r = int(new_r * 255)
            new_g = int(new_g * 255)
            new_b = int(new_b * 255)
            color_cache[(r, g, b)] = (new_r, new_g, new_b)
        
        new_data.append((new_r, new_g, new_b, item[3]))
    
    new_img = Image.new('RGBA', img.size)
    new_img.putdata(new_data)
    
    new_img.save(output_path)
    print(f"{datetime.datetime.now()} 生成: {output_path} (キャッシュサイズ: {len(color_cache)})")

def process_input_folder(input_folder='input', hue_steps=10, saturation_steps=3, num_cores=None):
    """
    入力フォルダ内の全てのPNG画像を処理
    """
    if num_cores is None:
        num_cores = cpu_count()
    
    os.makedirs('output', exist_ok=True)
    png_files = [os.path.join(input_folder, f) for f in os.listdir(input_folder) 
                if f.lower().endswith('.png')]
    
    if not png_files:
        print("入力フォルダに処理対象のPNG画像がありません。")
        return
    
    print(f"使用するコア数: {num_cores}")
    
    # 全ての画像、色相、彩度の組み合わせを生成
    tasks = []
    for image_path in png_files:
        for hue_step in range(hue_steps):
            for sat_step in range(saturation_steps):
                tasks.append((image_path, hue_step, sat_step, hue_steps, saturation_steps))
    
    # タスクを並列処理
    with Pool(num_cores) as p:
        p.map(process_image_with_params, tasks)
    
    # 元の画像をoutputフォルダにコピーして削除
    for image_path in png_files:
        name, _ = os.path.splitext(os.path.basename(image_path))
        output_dir = os.path.join('output', name)
        os.makedirs(output_dir, exist_ok=True)
        shutil.copy2(image_path, os.path.join(output_dir, os.path.basename(image_path)))
        os.remove(image_path)
    
    print("全ての画像の処理が完了しました。")

def main():
    """
    コマンドラインから引数を受け取り、画像処理を実行
    """
    parser = argparse.ArgumentParser(description='PNG画像の色相と彩度を変更')
    parser.add_argument('--hue_steps', type=int, default=10, 
                        help='色相の段階数 (デフォルト: 10)')
    parser.add_argument('--saturation_steps', type=int, default=3, 
                        help='彩度の段階数 (デフォルト: 3)')
    parser.add_argument('--input_folder', type=str, default='input', 
                        help='入力フォルダのパス (デフォルト: input)')
    parser.add_argument('--num_cores', type=int, default=None,
                        help='使用するコア数 (デフォルト: システムの最大コア数)')
    
    args = parser.parse_args()
    
    process_input_folder(
        input_folder=args.input_folder,
        hue_steps=args.hue_steps,
        saturation_steps=args.saturation_steps,
        num_cores=args.num_cores
    )

if __name__ == '__main__':
    main()