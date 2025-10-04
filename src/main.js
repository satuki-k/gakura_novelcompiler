/* gaku-ura9.4 lib javascript抜粋 */

//なるべくエラー検出したい
<debug>"use strict";</debug>

#!include element.js;
#!include string.js;
#!include array.js;

/* 進行クラス */
//セーブidは他の作品と競合を防止するためのものです。使用環境に合わせて変更してください
const save_id = location.href.replace(location.protocol,"")+"_gaku-ura4.6.1_save_";
class Gs{
	#page; //進行管理id
	#wait; //表示の未完了
	#unbind; //強制停止
	#serifSection; //次へ進む方法が次の会話か
	#sptid; //インターバルid(セリフ)
	#antfn_l; //タイムアウト関数
	#serifText; //話す内容
	#serifTextPoint; //話す内容id
	#chara_list; //キャラ一覧
	#chara_index; //キャラ登場順
	#viewArea; //表示場所
	#hideArea; //clearで消されない場所
	#speakArea; //セリフ表示枠
	#speakAreaName; //キャラ名表示欄
	#speakAreaSerifBase; //セリフ表示枠
	#speakAreaSerif; //セリフ表示欄
	#nextButton; //次へのボタン
	#msgHideButton; //セリフ枠非表示ボタン(画面が小さくてセリフで重なってしまう対策)
	#menu_button_enable; //それまでメニューボタンが有効だったか
	#isclear; //クリアしたか
	[VAR];

	//初期化 下地作成
	constructor(){
		if (!$ID("gaku-ura_base")||$ID("gaku-ura_display_w")){
			try{
				$QS(":root").remove();
			} catch {}
			return;
		}
		//初期化
		this.#page = 0;
		this.#wait = false;
		this.#unbind = false;
		this.#serifSection = true;
		this.#sptid = null;
		this.#menu_button_enable = false;
		this.#isclear = false;
		this.#chara_list = [CHARA_LIST];
		this.#chara_index = [];
		this.#antfn_l = [];
		this.#serifText = [];
		this.#serifTextPoint = 0;
		//dom作成
		const vw = document.createElement("div");
		vw.id = "gaku-ura_display_w";
		this.#viewArea = document.createElement("div");
		this.#hideArea = document.createElement("div");
		this.#speakArea = document.createElement("div");
		this.#speakAreaName = document.createElement("h2");
		this.#speakAreaSerifBase = document.createElement("div");
		this.#speakAreaSerif = document.createElement("p");
		this.#speakAreaSerifBase.append(this.#speakAreaSerif);
		this.#nextButton = document.createElement("span");
		this.#msgHideButton = document.createElement("span");
		this.#nextButton.classList.add("next_btn");
		this.#msgHideButton.classList.add("msg_hide_btn");
		this.#speakArea.append(this.#speakAreaName);
		this.#speakArea.append(this.#speakAreaSerifBase);
		this.#speakArea.append(this.#msgHideButton);
		this.#viewArea.classList.add("gaku-ura_display");
		this.#viewArea.id = "gaku-ura_display";
		this.#speakArea.classList.add("gaku-ura_speak");
		this.#speakArea.id = "gaku-ura_speak";
		this.#speakAreaSerifBase.classList.add("gaku-ura_speak_base");
		this.#speakAreaSerifBase.id = "gaku-ura_speak_base";
		this.#speakArea.style.display = "none";
		this.#hideArea.id = "gaku-ura_hide";
		vw.append(this.#viewArea);
		$ID("gaku-ura_base").append(vw);
		$ID("gaku-ura_base").append(this.#speakArea);
		$ID("gaku-ura_base").append(this.#hideArea);
		//入力受け入れ
		$ID("gaku-ura_base").addEventListener("click", ()=>{this.input_action("Return")});
		document.addEventListener("keydown", (e)=>{this.input_action(e.key)});
		document.addEventListener("contextmenu", (e)=>{e.preventDefault();this.input_action("hidemsg")});
		document.addEventListener("touchmove", (e)=>{if(this.#speakArea.style.display==="none"){e.preventDefault();this.input_action("hidemsg");}});
		this.#msgHideButton.addEventListener("click", (e)=>{e.stopPropagation();this.input_action("hidemsg")});
		//プリロード
		[PRELOAD].forEach((v)=>{
			<debug>console.log("プリロード:"+v);</debug>
			const i = document.createElement("img");
			i.src = v;
		});
		this.show();
	}

	//順序逆転防止
	setTimer(fn, s){
		const id = setTimeout(fn, s);
		const n = Date.now();
		this.#antfn_l.push({fn, id, s, n});
		<debug>console.log("タイマーセット:"+s+"ms");</debug>
	}
	killTimer(){
		for (const {id, fn, s, n} of this.#antfn_l){
			clearTimeout(id);
			const d = Date.now() -n;
			if (d < s){
				<debug>console.log("アニメーション強制終了: id"+id+" 原因"+s+"ms>"+d+"ms");</debug>
				fn();
				this.speak_all();
			}
		}
		if (this.#sptid){
			clearInterval(this.#sptid);
			<debug>console.log("セリフ強制終了(スキップ): id",this.#sptid);</debug>
		}
		this.#antfn_l = [];
	}

	//ここに追加メソッド
	[METHOD];

	//next有効化
	start(){
		this.#serifSection = true;
	}
	//一時停止
	stop(){
		this.#serifSection = false;
	}
	//画面クリア
	clear(){
		this.#viewArea.innerHTML = "";
		for (let i = 0; i < this.#chara_index.length; ++i){
			this.chara_hide(this.#chara_index[i]);
		}
		this.#isclear = true;
	}


	//背景の色または画像
	bgcolor(c, s=0){
		this.#viewArea.style.backgroundColor = c;
		this.#viewArea.style.animation = s==0?"":"bgfade "+s+"s linear 1";
		<debug>console.log("背景色: "+c);</debug>
	}
	bgimage(i, s=0, c=""){
		if (c === ""){
			if (s){
				if (i){
					this.#viewArea.style.transition = s+"s";
					this.#viewArea.style.animation = "bgfade "+s+"s linear 1";
					this.#viewArea.style.backgroundImage="url("+i+")";
					this.setTimer(()=>{this.#viewArea.style.animation="";this.#viewArea.style.transition=""}, s*1000);
				} else {
					this.#viewArea.style.animation = "bgfade "+s+"s linear 1 reverse";
					this.setTimer(()=>{this.#viewArea.style.backgroundImage="";this.#viewArea.style.animation="";this.#viewArea.style.transition=""}, s*1000);
				}
			} else {
				this.#viewArea.style.backgroundImage = i?"url("+i+")":"";
			}
			<debug>console.log("背景画像: "+i);</debug>
		} else {
			this.#viewArea.style.backgroundImage = c;
			this.#viewArea.style.animation = s==0?"":"bgfade "+s+"s linear 1";
			<debug>console.log("背景CSS画像:"+c);</debug>
		}
	}

	//登場した順番を維持して整列
	chara_sort(){
		let l = 0;
		let c = [];
		for (let k = 0; k < this.#chara_index.length; ++k){
			const kn = this.#chara_index[k];
			if ($ID("chara_"+kn)){
				this.#chara_list[kn].e = $ID("chara_"+kn);
				this.#chara_list[kn].s = true;
			} else {
				this.#chara_list[kn].s = false;
			}
			if (this.#chara_list[kn].s){
				++l;
				c.push(kn);
			}
		}
		if (l > 0){
			if (l === 1){
				this.#chara_list[c[0]].e.style.left = "50%";
				this.#chara_list[c[0]].e.style.transform = "translateX(-50%)";
			} else {
				for (let i = 0; i < l; ++i){
					this.#chara_list[c[i]].e.style.left = (100*i/(l-1))+"%";
					this.#chara_list[c[i]].e.style.transform = "translateX(-"+(100*i/(l-1))+"%)";
				}
			}
		}
		<debug>console.log("キャラ:", c);</debug>
	}
	//キャラ登場
	chara_show(name, status, s=0, r=true){
		if ($ID("chara_"+name)){
			this.#chara_list[name].e = $ID("chara_"+name);
		} else {
			this.#chara_list[name].s = false;
		}
		if (!this.#chara_list[name].s){
			this.#chara_list[name].e = document.createElement("img");
			this.#chara_list[name].e.classList.add("chara");
			if (r){
				this.#viewArea.append(this.#chara_list[name].e);
				this.#chara_index.push(name);
			} else {
				this.#viewArea.prepend(this.#chara_list[name].e);
				this.#chara_index.unshift(name);
			}
			this.#chara_list[name].e.style += this.#chara_list[name].e;
			this.#chara_list[name].e.id = "chara_"+name;
		}
		this.#chara_list[name].p = status;
		if (s !== 0){
			this.#chara_list[name].e.style.animation = "fade "+s+"s linear 1";
		}
		this.#chara_list[name].e.src = this.#chara_list[name].d+"/"+this.#chara_list[name].p;
		this.#chara_list[name].s = true;
		this.chara_sort();
	}
	//キャラ退場
	chara_hide(name){
		if (this.#chara_list[name].s){
			if ($ID("chara_"+name)){
				this.#chara_list[name].e = $ID("chara_"+name);
			}
			this.#chara_list[name].e.remove();
			this.#chara_list[name].s = false;
			this.#chara_index.splice(this.#chara_index.indexOf(name), 1);
			this.chara_sort();
		}
	}
	//キャラフェードアウト
	chara_hide_fade(name, s){
		if (this.#chara_list[name].s && $ID("chara_"+name)){
			this.#chara_list[name].e.style.opacity = "0";
			this.#chara_list[name].e.style.animation = "fade "+s+"s linear 1 reverse";
			this.setTimer((n=name)=>{this.chara_hide(n);}, s*1000);
		}
	}

	//内部以外では使用禁止
	asyspeak(){
		this.#wait = true;
		if (this.#serifTextPoint > this.#serifText.length){
			this.#speakAreaSerif.innerHTML = this.#serifText.join("");
			this.#speakAreaSerif.append(this.#nextButton);
			this.#serifTextPoint = this.#serifText.length;
			clearInterval(this.#sptid);
			this.#wait = false;
			this.#sptid = null;
			return;
		}
		if (this.#serifText){
			if (this.#speakArea.style.display === "none"){
				this.#speakArea.style.display = "block";
			}
			this.#speakAreaSerif.innerHTML = this.#serifText.slice(0, this.#serifTextPoint).join("");
		}
		++this.#serifTextPoint;
	}

	//全部表示する
	speak_all(){
		if (this.#wait){
			clearInterval(this.#sptid);
			this.#sptid = setInterval(()=>{this.asyspeak()}, 10);
		}
	}

	//セリフ喋る
	speak(name, txt_list, speed, add=false){
		if (!this.#serifSection) return;
		if (this.#wait){
			this.speak_all();
			return;
		}
		if (add && this.#serifText){
			this.#serifText = this.#serifText.concat(txt_list);
		} else {
			this.#serifText = txt_list;
			this.#speakAreaSerif.innerHTML = "";
			this.#serifTextPoint = 0;
		}
		this.#speakAreaName.innerHTML = this.#chara_list[name]&&this.#chara_list[name].n?this.#chara_list[name].n:name;
		this.#nextButton.remove();
		this.#sptid = setInterval(()=>{this.asyspeak()}, speed);
	}

	//表示(メイン進行)
	show(isload=false){
		<debug>console.log("%c \nページ:"+this.#page, 'color:#00f;');</debug>
		this.killTimer();
		switch (this.#page){
			[PAGES]
			<debug>default:console.log("未定義領域に突入しました。シナリオの終端にgotoが無いか無効なgotoです。");break;</debug>
		}
		this.#isclear = false;
	}

	//次の会話へ
	next(){
		if (this.#unbind) return;
		if (this.#serifSection && this.#page < [PAGE_MAX]){
			++this.#page;
			this.show();
		}
	}
	move_page(p, isload=false){
		if (this.#unbind) return;
		<debug>console.log("%c \n\ngoto セクション:"+p, 'color:#f50;');</debug>
		this.#page = p;
		this.start();
		this.show(isload);
	}

	//キーボード入力
	input_action(key){
		if (this.#unbind) return;
		if (key === "hidemsg"){
			if (this.#speakArea.style.display === "none" && this.#serifSection){
				this.#speakArea.style.display = "block";
			} else {
				if (this.#wait){
					this.#speakAreaSerif.innerHTML = this.#serifText.join("");
					this.#serifTextPoint = this.#serifText.length;
					this.speak_all();
				}
				this.#speakArea.style.display = "none";
			}
		}
		if (this.#serifSection){
			if (key === "Return" || key === "Enter"){
				if (this.#wait){
					this.speak_all();
				} else {
					this.next();
				}
			}
		}
	}

	//メニュー
	menu_button(show=true){
		if (show){
			if (!$ID("gaku-ura_menu_button")){
				const b = document.createElement("a");
				b.href = "#";
				b.id = "gaku-ura_menu_button";
				$ID("gaku-ura_base").append(b);
				b.addEventListener("click", (e)=>{
					e.preventDefault();
					this.menu_show();
				});
			}
		} else {
			if ($ID("gaku-ura_menu_button")){
				$ID("gaku-ura_menu_button").remove();
			}
		}
	}
	//innerHTMLで追加した要素を取得しないように
	menu_page(show=true){
		this.#unbind = show;
		if ($ID("gaku-ura_menu")) $ID("gaku-ura_menu").remove();
		if (show){
			this.menu_button(false);
		} else if (this.#menu_button_enable){
			this.menu_button();
		}
	}
	/* メニューオプション画面 */
	menu_show(){
		this.menu_page();
		const m = document.createElement("div");
		const l = ["to_title", "save", "load", "clear", "close_menu"];
		const n = ["タイトルへ", "セーブ", "ロード", "ローカルストレージ削除", "とじる"];
		const t = {};
		m.innerHTML = "<h2>めにゅー</h2>";
		m.id = "gaku-ura_menu";
		for (let i = 0; i < l.length; ++i){
			const a = document.createElement("a");
			a.href = "#";
			a.id = l[i];
			a.innerHTML = "<div>"+n[i]+"</div>";
			t[l[i]] = a;
			m.append(a);
		}
		$ID("gaku-ura_base").append(m);
		m.addEventListener("click", (e)=>{e.stopPropagation()});
		t["to_title"].addEventListener("click", (e)=>{
			e.preventDefault();
			location.reload();
		});
		t["save"].addEventListener("click", (e)=>{
			e.preventDefault();
			this.save_show();
		});
		t["load"].addEventListener("click", (e)=>{
			e.preventDefault();
			this.load_show();
		});
		t["clear"].addEventListener("click", (e)=>{
			e.preventDefault();
			this.clear_show();
		});
		t["close_menu"].addEventListener("click", (e)=>{
			e.preventDefault();
			this.menu_page(false);
		});
	}
	//セーブする内容はよく検討すること
	save(sid=0){
		const n = new Date();
		const jn = {"p":this.#page,"cl":this.#chara_list,"ci":this.#chara_index,"sp":this.#speakArea.style.display,"h":this.#viewArea.innerHTML,"hw":$ID("gaku-ura_display_w").innerHTML,"hh":this.#hideArea.innerHTML,"tl":this.#serifText,"mb":this.#menu_button_enable,
			"d":n.getFullYear()+"年 "+(n.getMonth()+1)+"月"+n.getDate()+"日 "+n.getHours()+"時"+n.getMinutes()+"分"+"  page "+this.#page, "t":this.#speakAreaSerif.innerHTML
		[SAVE_REGIST]};
		const o = JSON.stringify(jn);
		try {
			localStorage.setItem(save_id+sid, o);
		} catch {}
	}
	save_show(){
		this.menu_page();
		const m = document.createElement("div");
		const t = [];
		m.innerHTML = "<h2>セーブ</h2><p>保存する場所を選択してください。</p>";
		m.id = "gaku-ura_menu";
		for (let i = 0; i < {SAVE_MAX}; ++i){
			let s = ["no data", "no data"];
			try {
				const j = localStorage.getItem(save_id+i);
				if (j){
					const jj = JSON.parse(j);
					s = [jj.d, jj.t];
				}
			} catch {
				continue;
			}
			const a = document.createElement("a");
			a.href = "#";
			a.id = "save_data_"+i;
			a.innerHTML = "<dl><dt>"+s[0]+"</dt><dd>"+s[1]+"</dd></dl>";
			t.push(a);
			m.append(a);
		}
		const a = document.createElement("a");
		a.href = "#";
		a.id = "close_menu";
		a.innerHTML = "<div>とじる</div>";
		m.append(a);
		$ID("gaku-ura_base").append(m);
		m.addEventListener("click", (e)=>{e.stopPropagation()});
		for (let i = 0; i < {SAVE_MAX}; ++i){
			t[i].addEventListener("click", (e)=>{
				e.preventDefault();
				this.save(i);
				this.menu_page(false);
			});
		}
		a.addEventListener("click", (e)=>{
			e.preventDefault();
			this.menu_page(false);
		});
	}
	load_show(){
		this.menu_page();
		const m = document.createElement("div");
		const t = [];
		m.innerHTML = "<h2>ロード</h2><p>読み込むものを選んでください。</p>";
		m.id = "gaku-ura_menu";
		for (let i = 0; i < {SAVE_MAX}; ++i){
			try {
				const j = localStorage.getItem(save_id+i);
				if (j){
					const jj =  JSON.parse(j);
					const a = document.createElement("a");
					a.href = "#";
					a.id = "save_data_"+i;
					a.innerHTML = "<dl><dt>"+jj.d+"</dt><dd>"+jj.t+"</dd></dl>";
					t.push(a);
					m.append(a);
				} else {
					t.push(null);
				}
			} catch {
				t.push(null);
			}
		}
		const a = document.createElement("a");
		a.href = "#";
		a.id = "close_menu";
		a.innerHTML = "<div>とじる</div>";
		m.append(a);
		$ID("gaku-ura_base").append(m);
		m.addEventListener("click", (e)=>{e.stopPropagation()});
		for (let i = 0; i < {SAVE_MAX}; ++i){
			if (t[i] === null) continue;
			t[i].addEventListener("click", (e)=>{
				e.preventDefault();
				try {
					const s = JSON.parse(localStorage.getItem(save_id+i));
					if (list_isset(s, ["mb","sp","ci","cl","h","hw","hh","tl","t","p"])){
						this.clear();
						$ID("gaku-ura_display_w").innerHTML = s.hw;
						this.#viewArea = $ID("gaku-ura_display");
						this.#menu_button_enable = s.mb;
						this.menu_page(false);
						this.#speakArea.style.display = s.sp;
						this.#chara_index = s.ci;
						this.#chara_list = s.cl;
						this.#viewArea.innerHTML = s.h;
						this.#hideArea.innerHTML = s.hh;
						this.#serifText = [];
						this.#serifTextPoint = 0;
						this.#speakAreaSerif.innerHTML = "";
						this.chara_sort();
						[LOAD_REGIST]
						this.move_page(s.p, true);
					} else {
						this.menu_page(false);
					}
				} catch {
					this.menu_page(false);
				}
			});
		}
		a.addEventListener("click", (e)=>{
			e.preventDefault();
			this.menu_page(false);
		});
	}
	clear_show(){
		this.menu_page();
		const m = document.createElement("div");
		m.id = "gaku-ura_menu";
		m.innerHTML = '<h2>データ削除</h2><p>バージョン変更などで取り残されたデータを削除するための機能です。<b style="color:red;">他のページにもセーブデータがある場合はそれも消えます。</b>通常は上書きセーブで対応してください。</p><p><br></p>';
		const a = document.createElement("a");
		const b = document.createElement("a");
		a.href = "#";
		b.href = "#";
		a.id = "clear_data";
		b.id = "close_menu";
		a.innerHTML = "<div>全てローカルストレージをリセット</div>";
		b.innerHTML = "<div>とじる</div>";
		m.append(a);
		m.append(b);
		$ID("gaku-ura_base").append(m);
		m.addEventListener("click", (e)=>{e.stopPropagation()});
		a.addEventListener("click", (e)=>{
			e.preventDefault();
			try {
				localStorage.clear();
			} catch {}
			this.menu_page(false);
		});
		b.addEventListener("click",(e)=>{
			e.preventDefault();
			this.menu_page(false);
		});
	}
}

//右クリックはメニューじゃなくてserifhide
/*
document.addEventListener("contextmenu", (e)=>{
	<debug>return;</debug>
	e.preventDefault();
});
*/
document.addEventListener("keydown", (e)=>{
	<debug>return;</debug>
	if (e.ctrlKey){
		if (e.key === "u" || e.key === "r" || e.key === "i"){
			e.preventDefault();
		}
	} else if (e.key === "F5" || e.key === "F12"){
		e.preventDefault();
	}
});

<debug>const g = </debug>new Gs();


#!include fit.js;
