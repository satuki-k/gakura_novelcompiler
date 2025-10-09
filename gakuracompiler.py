#!/usr/bin/env python3
# コンパイラ本体
# (c)gaku-ura 2025
# http://bq.f5.si/
#gaku-ura9.5抜粋・翻訳
import sys
import os
import re
import shutil
if "REQUEST_METHOD" not in os.environ:
	import webbrowser as web
def row_js(j):
	return re.sub(r"( |)(,|=|{|}|\(|\)|[|]|\?|!|\&|-|\+|<|>|:|;|\*|\/)( |)",r"\2",j)
def subrpos(start, end, text):
	f1 = text.find(start)
	len1 = len(start)
	if f1 != -1:
		f2 = text[f1+len1:].find(end)
		if f2 != -1:
			return text[f1+len1:f1+f2+len1]
	return ""
def remove_comment_rows(code, s="/*", g="*/"):
	while (p:=subrpos(s, g, code)) != "":
		code = code.replace(s+p+g, "")
	return code
def css_out(css_file):
	if css_file == "":
		return ""
	r = ""
	css_list = []
	if os.path.isdir(css_file):
		for f in os.listdir(css_file):
			if f.endswith(".css"):
				css_list.append(css_file+"/"+f)
	elif os.path.isfile(css_file):
		css_list = [css_file]
	for css in css_list:
		with open(css, "r") as fp:
			r += fp.read()
	r = remove_comment_rows(r)
	r = re.sub(r"\r|\n|\r\n|\t", "", r)
	return re.sub(r"( |)(,|:|;|{|})( |)", r"\2", r)
def js_out(js_file, minify=True):
	if js_file == "":
		return ""
	r = ""
	js_list = []
	if os.path.isdir(js_file):
		for f in os.listdir(js_file):
			if f.endswith(".js"):
				js_list.append(js_file+"/"+f)
	elif os.path.isfile(js_file):
		js_list = [js_file]
	for js in js_list:
		with open(js, "r") as fp:
			j = fp.read()
		if subrpos("#!option ",";", j) == "notminify":
			minify = False
		j = remove_comment_rows(j, "#!option ", ";")
		if minify:
			j = remove_comment_rows(j)
			t = ""
			for row in j.splitlines():
				t += re.sub(r"\/\/.*", "", row.strip())
			r += row_js(t)
		else:
			r += j
	return r
#文字列リテラル用htmlエンティティ化
def row_h(text):
	h = lambda s:s.replace("{","&#123;").replace("}","&#125;").replace("(","&#40;").replace(")","&#41;").replace(" ","&nbsp;").replace("=","&#61;")
	n = ""
	s = ""
	fd = False
	fs = False
	for i in list(text):
		s += i
		if i == "'" or i == '"':
			if i == "'":
				if not fd:
					if fs:
						fs = False
						n += h(s)
					else:
						fs = True
						n += s
					s = ""
			else:
				if not fs:
					if fd:
						fd = False
						n += h(s)
					else:
						fd = True
						n += s
					s = ""
	return n+s
#joinはシングルクォーテーションですること
def split_with_html(text):
	r = []
	l = list(text)
	i = 0
	while i < len(l):
		if l[i] == "\\":
			l[i] = "\\\\"
		if l[i] == "<" and text[i:].find(">") != -1:
			t = [l[i]]
			while l[i] != ">":
				i += 1
				if l[i] == "'":
					l[i] = '"'
				t.append(l[i])
			r.append("".join(t))
		elif l[i] == "&" and text[i:].find(";") != -1:
			t = [l[i]]
			while l[i] != ";":
				i += 1
				if l[i] == "'":
					l[i] = '"'
				t.append(l[i])
			r.append("".join(t))
		else:
			if l[i] == "'":
				l[i] = "&#39;"
			elif l[i] == '"':
				l[i] = "&#34;"
			r.append(l[i])
		i += 1
	return r
def ruby(t):
	p = t.find("|")
	while (c:=subrpos("|","》",t[p:])) != "":
		l = c.split("《")
		if len(l) == 2:
			t = t.replace("|"+c+"》", "<ruby><rb>"+l[0]+"</rb><rt>"+l[1]+"</rt></ruby>")
		p = t.find("|")
	return t
m_u8lf = {"encoding":"utf-8","newline":"\n"}
d_root = os.path.abspath(os.path.dirname(sys.argv[0]))
entry_point_gkrs = d_root+"/script.gkrs"
export_dir = d_root+"/export"
#結果管理用
e_none = 0
e_init = 1
e_pars = 2
e_fatl = 3
e_warn = 4
def e_fmt(typ, msg, lid=0, f=""):
	if typ == e_none:
		return [typ,msg+"\n",lid,f]
	else:
		return [typ,"("+f+")["+{e_init:"preprocess",e_pars:"parse",e_fatl:"fatal",e_warn:"warning"}[typ]+"]"+msg+", line"+str(lid)+"\n",lid,f]
#コンパイルメモ用変数
config = {}
replace = {}
p_method = {}
section = ""
page_list = []
uqid = 0
def start_build(deb=False, web_bw=False, nest={"first":True,"file":entry_point_gkrs}):
	global config
	global replace
	global p_method
	global section
	global page_list
	global uqid
	#初期化
	if nest["first"]:
		if not os.path.isfile(nest["file"]):
			return e_fmt(e_init,"対象ファイルが存在しません/"+nest["file"]+" is not file.")
		config = {"SPEED":100,"TITLE":"","SAVE_MAX":4,"WIDTH":1100,"HEIGHT":700}
		if deb:
			config["DEB"] = "true"
		else:
			config["DEB"] = "false"
		replace = {
			"VAR":"","PAGES":"","CHARA_LIST":{},"METHOD":"",
			"PAGE_MAX":0,"SAVE_REGIST":"","LOAD_REGIST":"","PRELOAD":[]}
		#数値:使用可能か str:引数形式
		p_method = {
			"background_clear":"",
			"background_image":"file(static/background/*) fadein=0",
			"background_color":"color fadein=0",
			"<button>":1,"chara":"name path=name show_name=''",
			"chara_show":"name file fadein=0 apear_from_right=false",
			"chara_hide":"name fadeout=0","clear":"","close_section":"",
			"define":"key ...value","eval":"...js_code",
			"function":"...name(args){code}","goto":"label","html":"...html",
			"include":"file","<input>":1,"menu_button":"true_or_false",
			"regist":"...js_code","serif_show":"","serif_hide":"",
			"speak":"show_name array speed clear=false","stop":"",
			"var":"name",
			#以下、jsに定義済(@で呼び出しも禁止)
			"asyspeak":0,"setTimer":0,"killTimer":0,"start":0,
			"bgcolor":0,"bgimage":0,"chara_sort":0,"chara_hide_fade":0,
			"speak_all":0,"show":0,"next":0,"move_page":0,
			"input_action":0,"menu_page":0,"menu_show":0,"save":0,
			"save_show":0,"load_show":0,"clear_show":0}
		page_list = []
		section = ""
		uqid = 0
		for f in ["index.html","src/main.js","src/main.css"]:
			if not os.path.isfile(d_root+"/"+f):
				return e_fmt(e_init,"必須ファイルが無い/"+d_root+"/"+f+" is not exists.")
	#コンパイル開始
	section_start = len(page_list)
	row_id = 0
	label = {}
	p_label = {}
	memo = {
	"name":"''","function":"","if_stack":[],"bottom_shift":"",
	"button_open":False,"form":False,"form_input":[],
	"form_shift":"","form_submit":"","dom_wait":""}
	fname = nest["file"]
	with open(fname, "r") as fp:
		rows = fp.readlines()
	#前処理
	for i in rows:
		row_id += 1
		row = remove_comment_rows(i.strip(), "/*", "*/")
		if row == "" or row[0] == ";" or row[:2] == "//" or row[:2] == "#!":
			continue
		f1 = row[0]
		#ラベルプロトタイプ
		if row[0] == "[" and row[-1] == "]" and subrpos("[[", "]]", row) == "":
			lb = row[1:len(row)-1].strip()
			if lb == "EOF":
				return e_fmt(e_pars,"label name 'EOF' is booked",row_id,fname)
			if lb == "":
				return e_fmt(e_pars,"ラベル名が空です/label name is empty. did you mean \\[\\]?",row_id,fname)
			#特殊ラベル
			lbl = lb.split(" ")
			if lbl[0] == "if":
				if len(lbl) < 2:
					return e_fmt(e_pars,"式がありません/'if label' require value",row_id,fname)
				memo["if_stack"].append({"type":"if"})
			elif lbl[0] == "elseif":
				if len(lbl) < 2:
					return e_fmt(e_pars,"式がありません/'elseif label' require value",row_id,fname)
				for j in range(len(memo["if_stack"]) -1, -1, -1):
					if memo["if_stack"][j]["type"] == "if":
						break
				else:
					return e_fmt(e_pars,"対応するifがありません/'if label' is not found",row_id,fname)
				memo["if_stack"].append({"type":"elseif"})
			elif lbl[0] == "else":
				if memo["if_stack"][-1]["type"] == "else":
					return e_fmt(e_pars,"elseの連続禁止/'else label' in else label",row_id,fname)
				for j in range(len(memo["if_stack"]) -1, -1, -1):
					if memo["if_stack"][j]["type"] == "if":
						break
				else:
					return e_fmt(e_pars,"対応するifがありません/'if label' is not found",row_id,fname)
				memo["if_stack"].append({"type":"else"})
			elif lb == "end":
				if len(memo["if_stack"]) < 1:
					return e_fmt(e_pars,"まだ開いていません/label has not open yet",row_id,fname)
				while memo["if_stack"] != []:
					if memo["if_stack"].pop(-1)["type"] == "if":
						break
			else:
				if " " in lb:
					return e_fmt(e_pars,"ラベル名に空白禁止/must not space in label name",row_id,fname)
				if lb in p_label:
					return e_fmt(e_pars,"'ラベルの多重定義禁止/label "+lb+"' has already defined in line "+str(p_label[lb]),row_id,fname)
				p_label[lb] = row_id
	if memo["if_stack"] != []:
		return e_fmt(e_pars,"ラベルが閉じられていません/'if label' was not closed",row_id,fname)
	#本番
	row_id = 0
	for i in rows:
		asect = ""
		close_fl = False
		row_id += 1
		i = remove_comment_rows(i, "/*", "*/")
		row = i.strip()
		if row == "" or row[0] == ";" or row[:2] == "//" or (row_id == 1 and row[:2] == "#!"):
			continue
		#マクロの解決
		for k, v in config.items():
			row = row.replace("[["+k+"]]", str(v))
		f1 = row[0]
		f2 = row[1:]
		ptr = 0
		while (bp:=subrpos("[[", "]]", row[ptr:])) != "":
			if bp.find("GOTO ") != 0:
				return e_fmt(e_fatl,"未定義マクロ/macro '"+bp+"' is not defined",row_id,fname)
			ptr += 4+len(bp)
		#[と]だけで構成される行は[]内部がラベル
		if row[0] == "[" and row[-1] == "]" and subrpos("[[", "]]", row) == "":
			if memo["function"] != "":
				return e_fmt(e_fatl,"関数内のラベル禁止/label must not exists in function",row_id,fname)
			lb = row[1:len(row)-1].strip()
			#特殊ラベル
			lbl = lb.split(" ")
			if lbl[0] == "if":
				memo["if_stack"].append({"type":"if","eval":" ".join(lbl[1:]),"id":replace["PAGE_MAX"]})
				asect += "[[IF open]]"
			elif lbl[0] == "elseif":
				memo["if_stack"].append({"type":"elseif","eval":" ".join(lbl[1:]),"id":replace["PAGE_MAX"]})
				asect += "[[ELSEIF open]]"
			elif lbl[0] == "else":
				memo["if_stack"].append({"type":"else","id":replace["PAGE_MAX"]})
				asect += "[[ELSE open]]"
			elif lb == "end":
				memo["if_stack"].append({"type":"end","id":replace["PAGE_MAX"]})
				asect += "[[END end]]"
			else:
				label[lb] = replace["PAGE_MAX"]
		# @制御命令
		elif f1 == "@" and len(row) > 1:
			#手動マクロ
			while (p:=subrpos("SERIF(", ")", row)) != "":
				row = row.replace("SERIF("+p+")", "'"+"','".join(split_with_html(ruby(p)))+"'")
			if subrpos("[[GOTO ", "]]", row) != "":
				g = subrpos("[[GOTO ", "]]", row)
				if g not in p_label:
					return e_fmt(e_fatl,"未定義ラベル/label '"+g+"' is not defined",row_id,fname)
			f2l = f2.split(" ")
			#定義確認・引数検査
			if f2l[0] not in p_method.keys() or p_method[f2l[0]] == 0:
				return e_fmt(e_fatl,"未定義・使用禁止の関数/'"+f2l[0]+"' is not defined or blocked.",row_id,fname)
			ags = p_method[f2l[0]]
			if ags != 1:
				if ags == "":
					max_argc = 0
					min_argc = 0
				else:
					max_argc = ags.count(" ") +1
					min_argc = max_argc -ags.count("=")
				if len(f2l) <= min_argc:
					return e_fmt(e_fatl,"引数が足りません/too few arguments. @"+f2l[0]+" "+ags,row_id,fname)
				elif not ags.split(" ")[-1].startswith("...") and max_argc+1 < len(f2l):
					return e_fmt(e_fatl,"引数が多すぎです/too much arguments. @"+f2l[0]+" "+ags,row_id,fname)
			#以下引数は検査済みなので範囲内が保証
			#goto文
			if f2l[0] == "goto":
				if memo["form"]:
					return e_fmt(e_fatl,"'@<input>' is must be closed by '@stop'",row_id,fname)
				if f2l[1] == "EOF":
					asect += "this.move_page([[GOTO EOF "+fname+"]]);"
				elif f2l[1] in p_label:
					asect += "this.move_page([[GOTO "+f2l[1]+"]]);"
				else:
					return e_fmt(e_fatl,"未定義ラベル/label '"+f2l[1]+"' is not defined",row_id,fname)
				close_fl = True
			#外部ファイル読み込み
			elif f2l[0] == "include":
				f = " ".join(f2l[1:]).strip()
				if f[0] == "/" or (len(f) > 1 and f[1] == ":"):
					pth = f
				else:
					pth = d_root+"/"+f
				if os.path.isfile(pth):
					for k, v in label.items():
						section = section.replace("[[GOTO "+k+"]]", str(v))
					rt = start_build(deb,web_bw,{"first":False,"file":pth})
					if rt[0] != e_none:
						return rt
				else:
					return e_fmt(e_fatl,pth+"ファイルが存在しません/is not file",row_id,fname)
			#リンクボタン
			elif f2l[0] == "<button>":
				c = subrpos('class="', '"', f2)
				s = subrpos('style="', '"', f2)
				t = subrpos('text="', '"', f2)
				menu = subrpos('menu="', '"', f2)
				g = subrpos('goto="', '"', f2)
				if menu == "":
					if g == "":
						gid = str(replace["PAGE_MAX"] +1)
					elif g == "EOF":
						gid = "[[GOTO EOF "+fname+"]]"
					elif g in p_label:
						gid = "[[GOTO "+g+"]]"
					else:
						return e_fmt(e_fatl,"未定義ラベル/label '"+g+"' is not defined",row_id,fname)
				else:
					if menu not in ["save","load","to_title"]:
						return e_fmt(e_fatl,"不正な引数です/an argument 'menu' must input 'save', 'load' or 'to_title'",row_id,fname)
					gid = str(replace["PAGE_MAX"])
				lbn = "goto_"+str(uqid)
				#buttonを作成
				asect += "const "+lbn+"=document.createElement('button');"+lbn+".id='"+lbn+"';"
				if t != "":
					asect += lbn+".innerHTML+='"+t+"';"
				if c != "":
					if " " in c:
						for j in c.split(" "):
							if j != "":
								asect += lbn+".classList.add('"+j+"');"
					else:
						asect += lbn+".classList.add('"+c+"');"
				if s != "":
					asect += lbn+'.style="'+s+'";'
				if memo["form"] and memo["form_submit"] == "":
					asect += lbn+".id='"+lbn+"';"+config["FORM"]+".append("+lbn+");"
					memo["form_shift"] += "this.move_page("+gid+");"
					memo["form_submit"] = lbn
				else:
					if memo["button_open"] == False:
						asect += "if($ID('gkbn'))$ID('gkbn').remove();this.#viewArea.innerHTML+='<div id=\"gkbn\"></div>';"
						memo["button_open"] = True
					asect += "$ID('gkbn').append("+lbn+");"
					if menu == "":
						memo["dom_wait"] += "$ID('"+lbn+"').addEventListener('click',(e)=>{e.stopPropagation();if(this.#unbind)return;if($ID('gkbn'))$ID('gkbn').remove();this.move_page("+gid+")});"
					else:
						memo["dom_wait"] += "$ID('"+lbn+"').addEventListener('click',(e)=>{e.stopPropagation();if(this.#unbind)return;"
						if menu in ["save","load","clear"]:
							memo["dom_wait"] += "this."+menu+"_show();"
						elif menu == "to_title":
							memo["dom_wait"] += "location.reload();"
						memo["dom_wait"] += "});"
				uqid += 1
			#入力 (フォーム形式 ボタンとセット ボタンが無いと脱出出来ない)
			elif f2l[0] == "<input>":
				c = subrpos('class="', '"', f2)
				s = subrpos('style="', '"', f2)
				#labelの文字列
				t = subrpos('text="', '"', f2)
				#未指定はtext
				y = subrpos('type="', '"', f2)
				v = subrpos('value="', '"', f2)
				mmin = subrpos('min="', '"', f2)
				mmax = subrpos('max="', '"', f2)
				if y == "":
					y = "text"
				#必須
				n = subrpos('name="', '"', f2)
				if n == "" or replace["VAR"].find("#"+n+";") == -1:
					return e_fmt(e_fatl,"変数が存在しないか未指定です/an argument 'name' is not set or it is not defined",row_id,fname)
				nen = "input_"+str(uqid)
				lnen = "l_"+nen
				if memo["form"] == False:
					frn = "form_"+str(uqid)
					config["FORM"] = frn
					#後でフォームを作るために記憶
					memo["form"] = True
					#イベント伝播防止
					asect += "if($ID('form'))$ID('form').remove();const "+frn+"=document.createElement('div');"+frn+".id='form';"+frn+".addEventListener('click',(e)=>{e.stopPropagation()});"+frn+".addEventListener('keydown',(e)=>{e.stopPropagation()});"
				asect += "const "+lnen+"=document.createElement('label');const "+nen+"=document.createElement('input');"+nen+".id='"+nen+"';"
				if mmin != "":
					if y == "text":
						asect += nen+'.minLength='+mmin+';'
					elif y == "range" or "munber":
						asect += nen+'.min='+mmin+';'
				if mmax != "":
					if y == "text":
						asect += nen+'.maxLength='+mmax+';'
					elif y == "range" or "munber":
						asect += nen+'.max='+mmax+';'
				asect += "this.#"+n+"='';"+nen+".name='"+nen+"';"+nen+".type='"+y+"';"+lnen+".innerHTML='"+t+"';"
				if y == "radio" or y == "checkbox":
					asect += lnen+".prepend("+nen+");"
				else:
					asect += lnen+".append("+nen+");"
				if c != "":
					if " " in c:
						for j in c.split(" "):
							if j != "":
								asect += nen+".classList.add('"+j+"');"
					else:
						asect += nen+".classList.add('"+c+"');"
				if s != "":
					asect += nen+'.style="'+s+'";'
				if v != "":
					asect += nen+'.value="'+v+'";'
				asect += frn+".append("+lnen+");"
				if y == "checkbox":
					asect += lnen+".onclick=()=>{this.#"+n+"="+nen+".checked;};"
				else:
					memo["form_input"].append({"name":n,"id":nen})
				uqid += 1
			#クリア
			elif f2l[0] == "clear":
				asect += "this.clear();"
			#セリフ欄の表示
			elif f2l[0] == "serif_show":
				asect += 'this.#speakArea.style.display="block";'
			elif f2l[0] == "serif_hide":
				asect += 'this.#speakArea.style.display="none";'
			#メニューボタン
			elif f2l[0] == "menu_button":
				if f2l[1] == "true" or f2l[1] == "false":
					asect += "this.menu_button("+f2l[1]+");this.#menu_button_enable="+f2l[1]+";"
				else:
					return e_fmt(e_fatl,"引数が不正です/first argument must be true or false",row_id,fname)
			#キャラ宣言
			elif f2l[0] == "chara":
				if len(f2l) < 3:
					f2l.append(f2l[1])
				if not os.path.isdir(d_root+"/static/chara/"+f2l[2]):
					return e_fmt(e_fatl,"static/chara/"+f2l[2]+" is not dir",row_id,fname)
				replace["CHARA_LIST"][f2l[1]] = {
				"d":"static/chara/"+f2l[2],
				"p":"","e":"","s":"","c":"","n":f2l[2]}
				#d=dir_path, p=status, e=element, s=show, c=css_style n=name
				if len(f2l) > 2:
					replace["CHARA_LIST"][f2l[1]]["n"] = "&nbsp;".join(f2l[3:])
			#キャラ表示
			elif f2l[0] == "chara_show":
				if f2l[1] not in replace["CHARA_LIST"]:
					return e_fmt(e_fatl,"未定義のキャラ/a character '"+f2l[1]+"' is not decleared",row_id,fname)
				if not os.path.isfile(d_root+"/"+replace["CHARA_LIST"][f2l[1]]["d"]+"/"+f2l[2]):
					return e_fmt(e_fatl,"ファイルがありません/"+f2l[2]+" is not file",row_id,fname)
				replace["PRELOAD"].append(replace["CHARA_LIST"][f2l[1]]["d"]+"/"+f2l[2])
				if len(f2l) > 3:
					try:
						float(f2l[3])
					except:
						return e_fmt(e_fatl,"型が違う/3rd arguments type is number in '@"+f2l[0]+"'.",row_id,fname)
					if len(f2l) > 4:
						asect += 'this.chara_show("'+f2l[1]+'","'+f2l[2]+'",'+f2l[3]+','+f2l[4]+');'
					else:
						asect += 'this.chara_show("'+f2l[1]+'","'+f2l[2]+'",'+f2l[3]+');'
				else:
					asect += 'this.chara_show("'+f2l[1]+'","'+f2l[2]+'");'
			elif f2l[0] == "chara_hide":
				if f2l[1] not in replace["CHARA_LIST"]:
					return e_fmt(e_fatl,"a character '"+f2l[1]+"' is not decleared",row_id,fname)
				if len(f2l) > 2:
					try:
						float(f2l[2])
					except:
						return e_fmt(e_fatl,"型が違う/2nd arguments type is number in '@"+f2l[0]+"'.",row_id,fname)
					asect += 'this.chara_hide_fade("'+f2l[1]+'",'+f2l[2]+');'
				else:
					asect += 'this.chara_hide("'+f2l[1]+'");'
			#背景
			elif f2l[0] == "background_clear":
				asect += "this.#viewArea.style='';"
			elif f2l[0] == "background_image":
				if f2l[1] == "none":
					if len(f2l) > 2:
						try:
							float(f2l[2])
						except:
							return e_fmt(e_fatl,"型が違う/2nd arguments type is number '@"+f2l[0]+"'.",row_id,fname)
						asect += "this.bgimage('',"+f2l[2]+");"
					else:
						asect += "this.bgimage('');"
				else:
					if not os.path.isfile(d_root+"/static/background/"+f2l[1]):
						return e_fmt(e_fatl,"static/background/"+f2l[1]+" is not file",row_id,fname)
					replace["PRELOAD"].append("static/background/"+f2l[1])
					if len(f2l) > 2:
						try:
							float(f2l[2])
						except:
							return e_fmt(e_fatl,"型が違う/2nd arguments type is number '@"+f2l[0]+"'.",row_id,fname)
						asect += "this.bgimage('static/background/"+f2l[1]+"',"+f2l[2]+");"
					else:
						asect += "this.bgimage('static/background/"+f2l[1]+"');"
			elif f2l[0] == "background_color":
				if f2l[1] == "none":
					f2l[1] = ""
				if len(f2l) > 2:
					try:
						float(f2l[2])
					except:
						return e_fmt(e_fatl,"型が違う/2nd arguments type is number '@"+f2l[0]+"'.",row_id,fname)
					asect += 'this.bgcolor("'+f2l[1]+'",'+f2l[2]+');';
				else:
					asect += 'this.bgcolor("'+f2l[1]+'");';
			#強制区切り
			elif f2l[0] == "close_section":
				if section != "":
					if memo["form"]:
						return e_fmt(e_warn,"'@<input>' is must be closed by '@stop'",row_id,fname)
					close_fl = True
				else:
					return e_fmt(e_warn,"this page section has already closed",row_id,fname)
			#次へ進むとき次の会話ではない(選択肢とか) close_sectionを伴う 会話に突入したら自動で復帰
			elif f2l[0] == "stop":
				if memo["form"]:
					if memo["form_submit"] == "":
						return e_fmt(e_fatl,"送信ボタンが無い/did you forget '@<button>'?",row_id,fname)
					#dom_waitの内容
					asect += "this.#viewArea.append("+config["FORM"]+");"+memo["bottom_shift"]+"$ID('"+memo["form_submit"]+"').addEventListener('click',(e)=>{if(this.#unbind)return;"
					for j in memo["form_input"]:
						asect += "this.#"+j['name']+"="+j['id']+".value;"
					asect += "$ID('form').remove();"+memo['form_shift']+"});"
					memo["form_input"] = []
					memo["form_shift"] = ""
					memo["form_submit"] = ""
					config["FORM"] = ""
					if memo["button_open"]:
						asect += memo["dom_wait"]
				elif memo["button_open"]:
					asect += memo["bottom_shift"]+memo["dom_wait"]
				asect += "this.stop();"
				memo["button_open"] = False
				memo["form"] = False
				memo["bottom_shift"] = ""
				memo["dom_wait"] = ""
				close_fl = True
			#html挿入(evalでも可能だが冗長になるからラップする)
			elif f2l[0] == "html":
				hc = "t"+str(uqid)
				if len(f2l) > 1:
					jc = "const "+hc+"='"+" ".join(f2l[1:]).replace("'",'"')+"';if(isload){this.#viewArea.innerHTML=this.#viewArea.innerHTML.replace("+hc+",'');}this.#viewArea.innerHTML+="+hc+";"
					if memo["form"] or memo["button_open"]:
						memo["bottom_shift"] += jc
					else:
						asect += jc
				uqid += 1
			#設定変更
			elif f2l[0] == "define":
				k = f2l[1].upper()
				v = " ".join(f2l[2:])
				if k != "TITLE" or config[k] == "":
					config[k] = v
				if k == "TITLE":
					asect += "$QS('title').innerHTML='"+v.replace("'",r"\'")+"';"
			#変数
			elif f2l[0] == "var":
				if "#" in f2l[1] or "." in f2l[1] or "-" in f2l[1] or f2l[1][0].isdigit():
					return e_fmt(e_fatl,"variable can not includes '#', '.' or '-' or start number",row_id,fname)
				replace["VAR"] += "#"+f2l[1]+";"
			#ロード対策用
			elif f2l[0] == "regist":
				replace["LOAD_REGIST"] += " ".join(f2l[1:])
			#メソッド追加
			elif f2l[0] == "function":
				if memo["function"] != "":
					return e_fmt(e_fatl,"function in function",row_id,fname)
				memo["function"] = " ".join(f2l[1:])
			#javascript埋め込み
			elif f2l[0] == "eval":
				jc = " ".join(f2l[1:])
				if memo["form"] or memo["button_open"]:
					memo["bottom_shift"] += jc
				else:
					asect += jc
			#関数はここまで
			else:
				asect += 'this.'+f2l[0]+"("
				if len(f2l) > 1:
					asect += row_h(" ".join(f2l[1:])).replace(" ", ",")
				asect += ");"
		#その他ブロック内
		elif memo["function"] != "":
			asect += row
		#名前表示
		elif f1 == "#":
			f2 = "'"+ruby(f2)+"'"
			while (p:=subrpos("<$", ">", f2)) != "":
				if replace["VAR"].find("#"+p+";") == -1:
					return e_fmt(e_warn,"未定義の変数です/undefined variable "+p,row_id,fname)
				f2 = f2.replace("<$"+p+">", "'+h(this.#"+p+")+'")
			memo['name'] = f2
		else:
			#通常はそのまま表示
			for c in ["@",";","#","*","[","]","/"]:
				row = row.replace("\\"+c, c)
			if "name" not in memo:
				memo["name"] = ""
			if row[-1] == "\\":
				row = row[0:len(row)-1]
				nk = True
			else:
				nk = False
			txt_list = "['"+"','".join(split_with_html(ruby(row)))+"']"
			isvar = False
			while (p:=subrpos("'<$", ">'", txt_list)) != "":
				if replace["VAR"].find("#"+p+";") == -1:
					return e_fmt(e_warn,"未定義の変数です/undefined variable "+p,row_id,fname)
				isvar = True
				txt_list = txt_list.replace("'<$"+p+">'", "lh(this.#"+p+")") #実行時に配列化とエスケープが必要
			#次元下げ
			if isvar:
				txt_list = txt_list+".flat()"
			if "keep_speak" in memo and memo["keep_speak"]:
				asect += 'this.speak('+memo["name"]+','+txt_list+','+str(config["SPEED"])+',true);'
			else:
				asect += 'this.speak('+memo["name"]+','+txt_list+','+str(config["SPEED"])+');'
			memo["keep_speak"] = nk
			if memo["form"]:
				return e_fmt(e_fatl,"'@<input>' is must be closed by '@stop'",row_id,fname)
			close_fl = True
		#共通
		if memo["function"] != "":
			memo["function"] += asect
			m = row_h(memo["function"])
			if m[-1] == "}" and m.count("{") == m.count("}") and m.count("{") > 0:
				if (f1:=m.find("(")) != -1 and m[f1:].find(")") != -1:
					if m[:f1].strip() in p_method.keys():
						return e_fmt(e_fatl,"関数の多重定義禁止/function "+m[:f1]+" has already defined",row_id,fname)
					p_method[m[:f1].strip()] = " ".join(map(lambda s:s.strip(),subrpos("(",")",m).split(",")))
					replace["METHOD"] += memo["function"]
					memo["function"] = ""
					if deb:
						replace["METHOD"] += "\n\t"
				else:
					return e_fmt(e_fatl,"関数の形式が不正です/'@function' require '(' and ')'",row_id,fname)
			continue
		if asect != "":
			section += asect
			if deb:
				section += "\n\t\t"
		if close_fl:
			page_list.append(section)
			section = ""
			replace["PAGE_MAX"] += 1
	if memo["function"] != "":
		return e_fmt(e_fatl,"'@function' is not close.",row_id,fname)
	if nest["first"] == True and section != "":
		if memo["form"]:
			return e_fmt(e_fatl,"'@<input>' is must be closed by '@stop'",row_id,fname)
		page_list.append(section)
		section = ""
		replace["PAGE_MAX"] += 1
	#特殊ラベル
	label["EOF "+fname] = replace["PAGE_MAX"]
	oeval = ""
	nst = 0
	not_end_id = 0
	page_add_list = []
	for i in range(len(memo["if_stack"])):
		v = memo["if_stack"][i]
		if v["type"] != "end":
			not_end_id = v["id"]
		if v["type"] == "if":
			nst += 1
			oeval = v["eval"]
			page_list[v["id"]] = page_list[v["id"]].replace("[[IF open]]","if("+oeval+"){",1)
			nc = 1
			for j in memo["if_stack"][i +1:]:
				if j["type"] == "if":
					nc += 1
				elif j["type"] in ["end","elseif","else"]:
					nc -= 1
					if nc == 0:
						endid = j["id"]
						break
			if v["id"] != endid:
				page_add_list.append({"id":v["id"],"c":"}else{this.move_page("+str(endid)+");}"})
		elif v["type"] == "elseif":
			not_list = ""
			for j in range(i -1, -1, -1):
				not_list += "("+memo["if_stack"][j]["eval"]+")"
				if memo["if_stack"][j]["type"] == "if":
					break
				else:
					not_list += "||"
			oeval = "!("+not_list+")&&("+v["eval"]+")"
			page_list[v["id"]] = page_list[v["id"]].replace("[[ELSEIF open]]","if("+oeval+"){",1)
			if v["id"] != memo["if_stack"][i +1]["id"]:
				page_add_list.append({"id":v["id"],"c":"}else{this.move_page("+str(memo["if_stack"][i +1]["id"])+");}"})
		elif v["type"] == "else":
			not_list = ""
			ct = 0
			for j in range(i -1, -1, -1):
				if memo["if_stack"][j]["type"] not in ["if","elseif"]:
					continue
				ct += 1
				not_list += "("+memo["if_stack"][j]["eval"]+")"
				if memo["if_stack"][j]["type"] == "if":
					break
				else:
					not_list += "||"
			if ct < 2:
				oeval = "!"+not_list
			else:
				oeval = "!("+not_list+")"
			page_list[v["id"]] = page_list[v["id"]].replace("[[ELSE open]]","if("+oeval+"){", 1)
			if v["id"] != memo["if_stack"][i +1]["id"]:
				page_add_list.append({"id":v["id"],"c":"}else{this.move_page("+str(memo["if_stack"][i +1]["id"])+");}"})
		elif v["type"] == "end":
			nst -= 1
			if len(page_list) > v["id"]:
				if v["id"] == not_end_id:
					page_list[v["id"]] = page_list[v["id"]].replace("[[END end]]","}",1)
				elif page_list[v["id"]].lstrip().find("[[END end]]") > 0:
					page_list[v["id"]] = page_list[v["id"]].replace("[[END end]]","}",1)
					page_list[v["id"]] = "if("+oeval+"){"+page_list[v["id"]]
				else:
					page_list[v["id"]] = page_list[v["id"]].replace("[[END end]]","",1)
			else:
				if v["id"] == not_end_id:
					section = section.replace("[[END end]]","}", 1)
				elif section.lstrip().find("[[END end]]") > 0:
					section = section.replace("[[END end]]","}", 1)
					section = "if("+oeval+"){"+section
				else:
					section = section.replace("[[END end]]","", 1)
	for i in range(len(page_add_list) -1, -1, -1):
		page_list[page_add_list[i]["id"]] += page_add_list[i]["c"]
	#gotoの修正
	for i in range(section_start, len(page_list)):
		while (ln:=subrpos("[[GOTO ","]]", page_list[i])) != "":
			rp = "[[GOTO "+ln+"]]"
			if ln in label:
				page_list[i] = page_list[i].replace(rp, str(label[ln]))
			else:
				return e_fmt(e_fatl,"label "+ln+" is not defined",0,fname)
	msg = e_fmt(e_none,"コンパイル完了。/compile is successed.",0,fname)
	if not nest["first"]:
		return msg #mainじゃなければ次へ

	#ビルド開始
	with open(d_root+"/index.html","r") as fp:
		html = fp.read()
	if not deb:
		html = remove_comment_rows(html,"<!--","-->").replace("\t","").replace("\r","").replace("\n","")
	js = js_out(d_root+"/src/main.js", not deb)
	css = css_out(d_root+"/src/main.css")
	ald = []
	while (p:=subrpos("#!include ",";", css)) != "":
		f = d_root+"/src/lib_css/"+p
		r = ""
		if p not in ald and os.path.exists(f):
			r = css_out(f)
			ald.append(f)
		css = css.replace("#!include "+p+";",r)
	ald = []
	while (p:=subrpos("#!include ",";", js)) != "":
		f = d_root+"/src/lib_js/"+p
		r = ""
		if f not in ald and os.path.exists(f):
			r = js_out(f)
			ald.append(f)
		js = js.replace("#!include "+p+";",r)
	html = html.replace("{CSS}",css)
	replace["CHARA_LIST"] = str(replace["CHARA_LIST"]).replace(" ","")+";"
	replace["PRELOAD"] = str(list(set(replace["PRELOAD"]))).replace(" ","")
	if not deb:
		replace["METHOD"] = row_js(replace["METHOD"])
	for i in replace["VAR"].split(";"):
		if i != "":
			replace["SAVE_REGIST"] += ",'"+i[1:]+"':this."+i
			replace["LOAD_REGIST"] += "this."+i+"=s."+i[1:]+";"
	#ページ割り当て
	for i in range(replace["PAGE_MAX"]):
		replace["PAGES"] += "case "+str(i)+":"+page_list[i]
		if deb:
			replace["PAGES"] += "\n\t\t"
		replace["PAGES"] += "break;"
		if deb:
			replace["PAGES"] += "\n\t\t"
	#置換子
	for k, v in config.items():
		html = html.replace("{"+str(k).upper()+"}", str(v))
		js = js.replace("{"+str(k).upper()+"}", str(v))
		css = css.replace("{"+str(k).upper()+"}", str(v))
	#jsへコンパイル
	for k, v in replace.items():
		js = js.replace("["+str(k)+"];", str(v))
		js = js.replace("["+str(k)+"]", str(v))
	if deb:
		js = js.replace("<debug>", "")
		js = js.replace("</debug>", "")
	else:
		js = remove_comment_rows(js, "<debug>","</debug>")
	#出力先の初期化
	if os.path.exists(export_dir):
		shutil.rmtree(export_dir)
	os.mkdir(export_dir)
	#htmlにリンク
	html = html.replace("{JS}", js)
	#htmlファイル作成
	with open(export_dir+"/index.html","w", **m_u8lf) as fp:
		fp.write(html+"\n")
	#静的ディレクトリをコピー
	shutil.copytree(d_root+"/static", export_dir+"/static")
	#css,jsファイルを作成
	os.mkdir(export_dir+"/parts")
	with open(export_dir+"/parts/main.css","w", **m_u8lf) as fp:
		fp.write(css+"\n")
	with open(export_dir+"/parts/main.js","w", **m_u8lf) as fp:
		fp.write(js+"\n")
	if os.path.isfile(d_root+"/README.txt"):
		shutil.copy(d_root+"/README.txt", export_dir+"/README.txt")

	#electron向けビルド
	if os.name == "nt" and deb == False:
		electron_dir = export_dir+"/electron"
		os.mkdir(electron_dir)
		e = r"const {app,BrowserWindow}=require('electron');let mainWindow;app.on('ready',function(){mainWindow=new BrowserWindow({width:"+str(config["WIDTH"])+",height:"+str(config["HEIGHT"])+",autoHideMenuBar:true,webPreferences:{nodeIntegration:false,contextIsolation:false,devTools:false}});mainWindow.setMenuBarVisibility(false);mainWindow.loadURL('file://'+__dirname+'/index.html');});"
		with open(electron_dir+"/index.html","w",**m_u8lf) as fp:
			fp.write(html+"\n")
		with open(electron_dir+"/index.js","w",**m_u8lf) as fp:
			fp.write(e+"\n")
		shutil.copytree(d_root+"/static",electron_dir+"/static")
		with open(electron_dir+"/init.bat","w") as fp:
			fp.write("npm init\n")
		with open(electron_dir+"/install_electron.bat","w") as fp:
			fp.write("npm install -D electron\nnpm install -g yarn\nyarn add electron-builder --dev\n")
		with open(electron_dir+"/build.bat","w") as fp:
			fp.write("npx electron-builder --win --x64 --dir\n")
		if os.path.isfile(d_root+"/favicon.png"):
			shutil.copy(d_root+"/favicon.png", electron_dir+"/favicon.png")
		if os.path.isfile(d_root+"/README.txt"):
			shutil.copy(d_root+"/README.txt", electron_dir+"/README.txt")
	msg[1] += "if you use electron to make exefile, please execute init.bat, install_electron.bat and build.bat\n"
	if "REQUEST_METHOD" not in os.environ:
		if web_bw:
			web.open(export_dir+"/index.html")
			msg[1] += "ファイルを開きます.../open the file...\n"
		else:
			msg[1] += "出力先ディレクトリ: "+d_root+"/export is output dir.\n"
	return msg
#他言語へ
def export_as(file, to, first=True):
	if not os.path.isfile(file):
		return [e_init,file+" is not file."]
	with open(file, "r") as fp:
		rows = fp.readlines()
	r = ""
	if to == "html":
		for i,l in enumerate(rows,1):
			row = l.strip()
			if row == "":
				r += "\n"
				continue
			if row[0] == "@" or row[0] == ";" or row[:2] == "//" or (i == 0 and row[:2] == "#!"):
				r += "<!-- "+row+" -->"
			elif row[0] == "#":
				r += "<h3>"+row[1:].strip()+"</h3>"
			elif row[0] == "[" and row[-1] == "]" and subrpos("[[","]]",row) == "":
				lb = row[1:len(row)-1].strip()
				lbl = lb.split(" ")
				if lbl[0] in ["if","elseif","else","end"]:
					r += "<!-- "+row+" -->"
				else:
					r += "<h2>"+row+"</h2>"
			else:
				if row[-1] == "\\":
					row = row[:len(row)-1]
				r += "<p>"+row+"</p>"
			r += "\n"
		r = '<!DOCTYPE html><html lang="ja"><head><meta http-equiv="content-type" content="text/html;charset=UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><style>*{margin:0 auto;}body{padding:1em;}</style></head><body>'+r+"</body></html>\n"
	elif to == "md":
		for i,l in enumerate(rows,1):
			row = l.strip()
			if row == "":
				r += "\n"
				continue
			if row[0] == "@" or row[0] == ";" or row[:2] == "//" or (i == 0 and row[:2] == "#!"):
				r += "<!-- "+row+" -->"
			elif row[0] == "#":
				r += "### "+row[1:].strip()
			elif row[0] == "[" and row[-1] == "]" and subrpos("[[","]]",row) == "":
				lb = row[1:len(row)-1].strip()
				lbl = lb.split(" ")
				if lbl[0] in ["if","elseif","else","end"]:
					r += "<!-- "+row+" -->"
				else:
					r += "## "+row
			else:
				if row[-1] == "\\":
					row = row[:len(row)-1]
				r += row
			r += "\n"
	return [e_none,r]

if __name__ == "__main__":
	o = None
	f = None
	b = False
	if len(sys.argv) > 1:
		for i in sys.argv[1:]:
			if i.upper() == "-Y":
				o = True
			elif i.upper() == "-N":
				o = False
			elif i.upper() == "-WEB":
				b = True
			elif f == None:
				f = i
	if o == None:
		try:
			s = input("Do you want to set to debug mode?(n/Y)")
		except:
			print("Canceled.")
			exit(-1)
		if s.strip() == "Y":
			o = True
		else:
			o = False
	if f == None:
		r = start_build(o, b)
	else:
		r = start_build(o, b, {"first":True,"file":f})
	print(r[1])
	exit(r[0])
