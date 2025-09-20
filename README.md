# gaku-ura novel compiler 4.2
2025-9-19
http://bq.f5.si/

## 必要なもの/runtime
gakuracompiler_gui.exe(editor and compiler): nothing
gakuracompiler.py(compiler only): **python3**
gakuracompiler_gui.py(editor and compiler): **python3 and tkinter**

## 実行/execute
gakuracompiler_gui.py(or exe): choose option in menu "Build"
gakuracompiler.py:
linux:
```
python3 gakuracompiler.py
```
windows:
```
python gakuracompiler.py
```
arguments: filepath(=script.gkrs) -y(debug mode) -n(publish mode) -WEB(open html file in web after compile)


## 文法の解説/how to coding
http://bq.f5.si/?Page=novelcompiler
**All of text files are must be "LF" and "UTF-8".**

## コーディング規約
1. 定義や宣言は可能な限り最初に行う
2. 伏線は必ず回収する
3. 偶然か第六感でしかクリア出来ないような仕様を避ける
4. 宣言した登場人物や変数は必ず使われなければならない
5. 記述するファイルパスや変数の名前は1バイト文字でなければならない
6. ラベルやマクロなどコンパイル後に消失する情報はこの限りではない
7. コンパイラの魔法は完璧でなない
8. 分割プリロードが必要なほどの量の画像を使ってはならない
9. 実行時にインラインscriptやevalをやってはいけない


## ライセンス/license
MIT license.


