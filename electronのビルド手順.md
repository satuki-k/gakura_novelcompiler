# electron製ソフトのビルド手順(windows用)

1. nodejsをダウンロード・インストール

2. コマンドプロンプトやpowerShellを開く
フォルダーに移動する

3. 新しいフォルダーで以下をコマンド実行(1つずつ)
initではなるべく入力すること(package.jsonの生成が不完全になる)
```
npm init
npm install -D electron
npm install -g yarn
yarn add electron-builder --dev
```

4. 必要ファイルを作成したら以下を同ディレクトリで実行
場合によってpackage.jsonを編集。index.htmlを作成。index.jsとfavicon.icoをご利用下さい。
アイコンはindex.htmlと同じディレクトリに配置。(256x256以上必要)
package.jsonに以下を追加。
```
	"build": {
		"win": {
			"target": "nsis",
			"icon": "favicon.png"
		}
	}
```


ビルド
```
npx electron-builder --win --x64 --dir
```

5. dist/win-unpacked内の全てのファイルを配布します
再度ビルドする場合に、エラーが出たら、前の生成ファイルを「タスク終了」させて下さい。
(バックグラウンドプロセスに自分で作ったパッケージ名があったらそれを消す)


6. asarの展開
導入
```
npm install -g asar
```

展開
```
asar extract ファイル 出力先ディレクトリ
```

