# PNG Color Pattern Generator
## 概要
任意のPNG画像から、色相、彩度違いの画像を生成するプログラムです。

色相、彩度を何通り生成するかを指定することも可能です。

## 環境構築
### VSCodeでDev Containerを使用する場合
このリポジトリをクローンし、コンテナをビルドするだけで実行環境が作れます。

### Pyhon実行環境で行う場合
ライブラリのインストール
```pip install Pillow```

main.pyと同じ階層にinputフォルダを作成します。

### 使い方
1. inputフォルダに任意のPNG画像を入れます(複数枚対応)
2. ```python main.py --hue_steps (色相の数) --saturation_steps (彩度の数)``` として実行
※--hue_steps と --saturation_steps はオプション引数です。```python main.py``` のみでも実行する場合、色相10通り、彩度3通りの30通りの画像が生成されます。
3. 生成された画像はoutputフォルダに生成される元画像の名前のフォルダに保存されます。
4. 全ての処理が終わった際に、inputフォルダに入れていた画像もoutputフォルダに移動されます。
