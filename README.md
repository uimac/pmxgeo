# pmxgeo
PMX Geometry Exporter for Blender

## Overview
これはBlender用PMXエクスポーターですが、2015/11/10の時点で存在するどんなPMXエクスポーターにも無い
圧倒的なエクスポート機能を持ったエクスポーターで、ジオメトリキャッシュを出力します。

## 具体的な動作
Blenderで選択したメッシュを、指定したフレーム数分、PMXファイルとVMDファイルに書き出します。
PMXファイルには、1つのセンターボーンと、頂点数が変化しないフレーム数分のモーフデータが含まれます。
つまり、通常、1モーフ = 1フレームです。

ただし、PMX/VMDファイルは通常1つずつできますが、頂点数が変化する場合複数個出力されます。
パーティクルの場合フレーム数分の個数のPMX/VMDファイルが出力されます。
この場合は、1PMX = 1フレームとなります。

VMDファイルには、上記モーフデータを1フレームごとに切り替えるキー、
またはモデルデータを1フレームごとに切り替えるキーが打ってあります

## 出力されるデータ
・1本のセンターボーン、複数のモーフデータが入った、PMXファイル(複数個)
・VMDファイル(複数個)
・MMMでインポート時に使用するデータ(予定)

## 動作環境
Windows Vista以降(今のところ64bitのみ。32bitも対応予定)
Blender 2.73以降(今のところ64bitのみ。32bitも対応予定)
MikuMikuMoving

## 動作しない環境
MikuMikuDance

## 今のところの実行方法
1. Blender\バージョン\python\lib\site-packages にmmformat.pydを設置
2. Blenderのテキストエディタでexport_pmx_geo.py を開く
3. エクスポートしたいメッシュを選択（今のところ複数メッシュは未対応)
4. BlenderのテキストエディタでRun Script

## その他
mmformat.pydのソースはこちらです
https://github.com/uimac/MMDFormats/tree/python

## License
GPLv2 or GPLv3 or MIT
