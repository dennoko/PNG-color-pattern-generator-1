import os
import shutil
from PIL import Image
import colorsys
import argparse

def adjust_image_color(image_path, hue_steps=10, saturation_steps=3):
    """
    指定された色相と彩度の段階数に基づいて画像の色バリエーションを生成
    
    :param image_path: 元画像のパス
    :param hue_steps: 色相の段階数
    :param saturation_steps: 彩度の段階数
    :return: 生成された画像のパスのリスト
    """
    print("processing image:", image_path)
    # 画像を開く
    img = Image.open(image_path).convert('RGBA')
    
    # 画像データを取得
    data = img.getdata()
    
    # 色相と彩度のステップを計算
    hue_increment = 360 / hue_steps
    saturation_increment = 1.0 / saturation_steps
    
    for hue_step in range(hue_steps):
        for sat_step in range(saturation_steps):
            # 新しい画像データリストを作成
            new_data = []
            
            # 色相と彩度の値を計算
            current_hue = (hue_step * hue_increment) / 360.0
            current_sat = (sat_step + 1) * saturation_increment
            
            for item in data:
                # アルファチャンネルは変更しない
                if item[3] == 0:
                    new_data.append(item)
                    continue
                
                # RGBをHSVに変換
                r, g, b = item[:3]
                h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
                
                # 色相と彩度を調整
                h = (h + current_hue) % 1.0
                s = min(s * current_sat, 1.0)
                
                # HSVをRGBに戻す
                r, g, b = colorsys.hsv_to_rgb(h, s, v)
                
                # 新しい色データを追加
                new_data.append((
                    int(r * 255), 
                    int(g * 255), 
                    int(b * 255), 
                    item[3]
                ))
            
            # 新しい画像を作成
            new_img = Image.new('RGBA', img.size)
            new_img.putdata(new_data)
            
            # 出力パスを生成
            filename = os.path.basename(image_path)
            name, ext = os.path.splitext(filename)
            output_dir = os.path.join('output', name)
            os.makedirs(output_dir, exist_ok=True)
            
            output_path = os.path.join(output_dir, f"{name}_hue{hue_step}_sat{sat_step}.png")
            new_img.save(output_path)
            print("generated image:", output_path)
    
    return 

def process_input_folder(input_folder='input', hue_steps=10, saturation_steps=3):
    """
    入力フォルダ内のすべてのPNG画像を処理
    
    :param input_folder: 入力画像が格納されているフォルダ
    :param hue_steps: 色相の段階数
    :param saturation_steps: 彩度の段階数
    """
    # 出力フォルダが存在しない場合は作成
    os.makedirs('output', exist_ok=True)
    
    # 入力フォルダ内のすべてのPNG画像を処理
    for filename in os.listdir(input_folder):
        if filename.lower().endswith('.png'):
            image_path = os.path.join(input_folder, filename)
            
            # 画像の色バリエーションを生成
            adjust_image_color(
                image_path, 
                hue_steps=hue_steps, 
                saturation_steps=saturation_steps
            )
            
            # 元の画像を出力フォルダにコピー
            name, _ = os.path.splitext(filename)
            output_dir = os.path.join('output', name)
            os.makedirs(output_dir, exist_ok=True)
            shutil.copy2(image_path, os.path.join(output_dir, filename))
            
            # 処理が完了したら入力フォルダから削除
            os.remove(image_path)
    
    print("画像の処理が完了しました。")

def main():
    """
    コマンドラインから引数を受け取り、画像処理を実行
    """
    parser = argparse.ArgumentParser(description='PNG画像の色相と彩度を変更')
    parser.add_argument('--hue_steps', type=int, default=10, 
                        help='色相の段階数 (デフォルト: 10)')
    parser.add_argument('--saturation_steps', type=int, default=3, 
                        help='彩度の段階数 (デフォルト: 3)')
    
    args = parser.parse_args()
    
    process_input_folder(
        hue_steps=args.hue_steps, 
        saturation_steps=args.saturation_steps
    )

if __name__ == '__main__':
    main()