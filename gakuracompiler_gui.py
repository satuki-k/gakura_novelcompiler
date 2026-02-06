#!/usr/bin/env python3
# tkinter必須
# (c)gaku-ura 2025
# http://bq.f5.si/
#nuitka --mingw64 --follow-imports --standalone --onefile --windows-console-mode=disable --enable-plugin=tk-inter --windows-icon-from-ico="favicon.ico" gakuracompiler_gui.py

import os
if "REQUEST_METHOD" in os.environ:
	print("content-type:text/html;charset=UTF-8\n\nThis is not website.")
	exit()
import sys
import webbrowser as web
import tkinter as tk
from tkinter import ttk
import gakuracompiler as gkrs
from tkinter import filedialog
def tk_nc(n):
	return "1.0+"+str(n)+"c"
class GsEditor:
	__slots__ = ("fs","fname","ftype","fcontent","expect","expectTab","lids","textArea","hltags","hltagsM","msgArea","fileArea","fileData","fdArea","fscpArea","rcmenu")
	def __init__(self):
		#メニュースタイルはあてにならない
		m = tk.Menu(root,bg="#fff",fg="#111",font=("",14))
		mt = {}
		for i in ["File","Edit","Insert","View","Build","Import","Export","Help"]:
			mt[i] = tk.Menu(root,tearoff=0,bg="#fff",fg="#111",font=("",14))
		self.fs = 12
		self.fname = ""
		self.ftype = ""
		self.fcontent = ""
		self.fileData = {}
		self.expect = {}
		NOBD = {"bd":0,"highlightthickness":0}
		HFONT = ("Courier",self.fs)
		BODY = {"bg":"#ffc","fg":"#000"}
		PTAG = {"spacing1":self.lh(),"spacing3":self.lh()}
		#根幹
		bW = tk.PanedWindow(root,orient=tk.VERTICAL) #上 menu code
		mW = tk.PanedWindow(bW,orient=tk.HORIZONTAL,height=500) #下 message
		eTA = tk.Frame(root,height=20,bg=BODY["bg"]) #上tab
		msF = tk.Frame(bW) #下 message
		meF = tk.Frame(mW,bg=BODY["bg"]) #右 menu
		# 上tab
		self.expectTab = ttk.Combobox(eTA,state="readonly",width=1<<10,font=HFONT)
		#左 code
		cdF = tk.Frame(mW)
		self.lids = tk.Text(cdF,takefocus=0,**PTAG,**NOBD,bg="#ccc",state="disabled",font=HFONT)
		self.textArea = tk.Text(cdF,undo=True,wrap="none",**PTAG,**NOBD,bg="#fff",fg="#000",tabs=("1c"),font=HFONT)
		csx = tk.Scrollbar(self.textArea,orient="horizontal",width=5,**NOBD,command=self.textArea.xview)
		csy = tk.Scrollbar(cdF,orient="vertical",width=10,**NOBD,command=self.scroll)
		#for highlight
		self.hltags = {"comment":"#c00","command":"#03a","keyword":"#03a","string":"#f60","macro":"#0c0","variable":"#0a0","section":"#00f","name":"#a0c","hl":"","error":"#f00"}
		self.hltagsM = {"section":"#938","keyword":"#00f","error":"#f00"}
		hltgs = {"hl":{"underline":True},"error":{"underline":True,"underlinefg":"#f00"}}
		hltgsm = {"section":{"font":("",self.fs,"bold")},"keyword":{"font":("",self.fs,"bold")}}
		#message
		self.msgArea = tk.Text(msF,**PTAG,spacing2=self.lh(),**NOBD,wrap="word",**BODY,font=HFONT)
		#menu
		self.fileArea = tk.Label(meF,bg="#ffc",fg="#15b",anchor="w",font=("",10)) #filename
		self.fscpArea = tk.Label(meF,**BODY,anchor="w",font=("",10)) #scope
		self.fdArea = tk.Listbox(meF,**BODY,**NOBD,activestyle="none",font=("",10)) #symbols
		#remove emacsy
		for k in ["d","i","p","k","e","h","b","f"]:
			self.textArea.bind("<Control-Key-"+k+">",self.void_key)
			self.msgArea.bind("<Control-Key-"+k+">",self.void_key)
		#set tags
		for k,v in self.hltags.items():
			if v != "":
				self.textArea.tag_configure(k,foreground=v)
			if k in hltgs:
				self.textArea.tag_configure(k,**hltgs[k])
		for k,v in self.hltagsM.items():
			if v != "":
				self.msgArea.tag_configure(k,foreground=v)
			if k in hltgsm:
				self.msgArea.tag_configure(k,**hltgsm[k])
		#scroll
		self.textArea.config(yscrollcommand=csy.set,xscrollcommand=csx.set)
		self.lids.config(yscrollcommand=csy.set,xscrollcommand=csx.set)
		#event
		self.textArea.bind("<KeyRelease>",lambda e:self.key_in(e.keysym))
		self.textArea.bind("<KeyPress>",lambda e:self.key_in(e.keysym))
		self.textArea.bind("<MouseWheel>",self.sync_scroll)
		self.textArea.bind("<Button-1>",lambda e:[self.textArea.mark_set("insert","@"+str(e.x)+","+str(e.y)),self.key_in("mouse")])
		self.textArea.bind("<Button-4>",self.sync_scroll)
		self.textArea.bind("<Button-5>",self.sync_scroll)
		self.lids.bind("<MouseWheel>",self.sync_scrolll)
		self.lids.bind("<Button-4>",self.sync_scrolll)
		self.lids.bind("<Button-5>",self.sync_scrolll)
		#menu tool
		root.config(menu=m)
		mt["File"].add_command(label="Open/開く",command=self.open_file,accelerator="Ctrl+O")
		mt["File"].add_command(label="Save/保存",command=self.save_file,accelerator="Ctrl+S")
		mt["File"].add_command(label="Reload/再読み込み",command=lambda:self.show_file(),accelerator="Ctrl+R")
		mt["File"].add_command(label="New/新規",command=self.new_file,accelerator="Ctrl+N")
		mt["File"].add_command(label="main scenario このプロジェクトのエントリーポイント",command=lambda:self.new_open(gkrs.entry_point_gkrs,";main scenario file\n@define TITLE hello\nhello, world!\n"))
		mt["File"].add_command(label="README.txt",command=lambda:self.new_open(gkrs.d_root+"/README.txt","title:\nversion:\nyour name:\netc\n"))
		mt["File"].add_command(label="Exit/終了",command=lambda:root.quit(),accelerator="Ctrl+Q")
		mt["Edit"].add_command(label="undo/もとにもどす",command=self.undo,accelerator="Ctrl+Z")
		mt["Edit"].add_command(label="redo/やりなおす",command=self.redo,accelerator="Ctrl+Y")
		mt["Edit"].add_command(label="javascript",command=lambda:self.inscode('@eval code'))
		mt["Edit"].add_command(label="function/関数",command=lambda:self.inscode('@function my_function(args){code}'))
		mt["Edit"].add_command(label="define macro/マクロ定義",command=lambda:self.inscode(';KEY is always upper. KEYは大文字。\n;"[[KEY]]"is "value"\n@define KEY value'))
		mt["Edit"].add_command(label="define window/画面定義",command=lambda:self.inscode("@define WIDTH [[WIDTH]]\n@define HEIGHT [[HEIGHT]]"))
		mt["Edit"].add_command(label="escape char/エスケープ文字",command=lambda:self.inscode("\\",True))
		mt["Edit"].add_command(label="row commentout/行コメントアウト",command=lambda:self.row_comment())
		mt["Insert"].add_command(label="include lib/ファイル呼び出し",command=lambda:self.inscode("@include file(relative path/相対パス)"))
		mt["Insert"].add_command(label="define title/タイトル定義",command=lambda:self.inscode("@define TITLE game_title"))
		mt["Insert"].add_command(label="define speed/速度定義",command=lambda:self.inscode("@define SPEED 100(ms between char and char)"))
		mt["Insert"].add_command(label="character def/キャラクター宣言",command=lambda:self.inscode("@chara name imagefiles_path(画像ディレクトリ under static/chara/) show_name(表示名)"))
		mt["Insert"].add_command(label="character show/キャラクター表示",command=lambda:self.inscode("@chara_show name imagefile(画像ファイル) 1"))
		mt["Insert"].add_command(label="character hide/キャラクター退場",command=lambda:self.inscode("@chara_hide name 1"))
		mt["Insert"].add_command(label="background image/背景画像",command=lambda:self.inscode("@background_image imagefile(画像ファイル under static/background/) 1"))
		mt["Insert"].add_command(label="background color/背景色",command=lambda:self.inscode("@background_color #000 1"))
		mt["Insert"].add_command(label="background clear/背景スタイル削除",command=lambda:self.inscode("@background_clear"))
		mt["Insert"].add_command(label="speak serif/台詞を話す",command=lambda:self.inscode("#show_name/表示名\nspeak contents/喋る内容"))
		mt["Insert"].add_command(label="define variable/変数定義",command=lambda:self.inscode("@var a"))
		mt["Insert"].add_command(label="insert variable at serif or name/台詞か名前に変数埋め込み", command=lambda:self.inscode("<$var_name>",True))
		mt["Insert"].add_command(label="make button/ボタン作成",command=lambda:self.inscode('@<button> goto="label or none(任意)" text="" class="" style="css" menu="title,save,load,or none(任意)"\n@stop'))
		mt["Insert"].add_command(label="make form/入力欄作成",command=lambda:self.inscode('@<input> name="decleared variable" text="" class="" style="css" type="text" value="" min="" max=""\n;getElementBy "[[FORM]]"\n;@eval [[FORM]].style="";\n@stop'))
		mt["Insert"].add_command(label="put label/ラベル配置",command=lambda:self.inscode('[label]'))
		mt["Insert"].add_command(label="jump to label/ラベルにジャンプ",command=lambda:self.inscode('@goto label'))
		mt["Insert"].add_command(label="hide serif/台詞の枠 非表示",command=lambda:self.inscode('@serif_hide'))
		mt["Insert"].add_command(label="menu button/メニューボタン",command=lambda:self.inscode('@menu_button true/false'))
		mt["Insert"].add_command(label="ruby/ルビ",command=lambda:self.inscode("|漢字《kanji》",True))
		mt["View"].add_command(label="Zoom in/拡大",command=lambda:self.zoom(),accelerator="Ctrl++")
		mt["View"].add_command(label="Zoom out/縮小",command=lambda:self.zoom(False),accelerator="Ctrl+-")
		mt["View"].add_command(label="project:"+gkrs.d_root)
		mt["Build"].add_command(label="project compile/このプロジェクトをコンパイル",command=lambda:self.compile(True,False),accelerator="Ctrl+F8")
		mt["Build"].add_command(label="project build/このプロジェクトをビルド",command=lambda:self.compile(False,False),accelerator="Ctrl+F9")
		mt["Build"].add_command(label="project execute/このプロジェクトを実行",command=lambda:self.compile(True,True),accelerator="Ctrl+F5")
		mt["Build"].add_command(label="project build and execute/このプロジェクトをビルドして実行",command=lambda:self.compile(False,True))
		mt["Build"].add_command(label="compile this file/このファイルをコンパイル", command=lambda:self.compile(True,False,False),accelerator="F8")
		mt["Build"].add_command(label="build this file/このファイルをビルド",command=lambda:self.compile(False,False,False),accelerator="F9")
		mt["Build"].add_command(label="execute this file/このファイルを実行",command=lambda:self.compile(True,True,False),accelerator="F5")
		mt["Build"].add_command(label="build this file and execute/このファイルをビルドして実行",command=lambda:self.compile(False,True,False))
		mt["Import"].add_command(label="as gkrs file/gkrsファイルとする",command=lambda:self.chftype("gkrs"))
		mt["Export"].add_command(label="html document",command=lambda:self.export_as("html"))
		mt["Export"].add_command(label="markdown document",command=lambda:self.export_as("md"))
		mt["Help"].add_command(label="how to use/使い方",command=self.show_help,accelerator="F1")
		mt["Help"].add_command(label="version: 5.2.3") #バージョン番号を追加
		for k, v in mt.items():
			m.add_cascade(label=k,menu=v)
		root.bind("<Control-Key-q>",lambda x:root.quit())
		root.bind("<Control-Key-s>",lambda x:self.save_file())
		root.bind("<Control-Key-o>",lambda x:self.open_file())
		root.bind("<Control-Key-r>",lambda x:self.show_file())
		root.bind("<Control-Key-n>",lambda x:self.new_file())
		root.bind("<Control-Key-plus>",lambda x:self.zoom())
		root.bind("<Control-Key-minus>",lambda x:self.zoom(False))
		root.bind("<F1>",lambda x:self.show_help())
		root.bind("<Control-F5>",lambda x:self.compile(True,True))
		root.bind("<Control-F8>",lambda x:self.compile(True,False))
		root.bind("<Control-F9>",lambda x:self.compile(False,False))
		root.bind("<F5>",lambda x:self.compile(True,True,False))
		root.bind("<F8>",lambda x:self.compile(True,False,False))
		root.bind("<F9>",lambda x:self.compile(False,False,False))
		self.expectTab.bind("<<ComboboxSelected>>", lambda x:self.show_file_expect(self.expectTab.get()))
		self.textArea.bind("<Control-Key-a>",self.select_all)
		self.textArea.bind("<Control-Key-c>",self.copy)
		self.textArea.bind("<Control-Key-o>",self.k_open_file)
		self.textArea.bind("<Control-Key-x>",self.cut)
		self.textArea.bind("<Control-Key-v>",self.paste)
		self.textArea.bind("<Control-Key-z>",self.undo)
		self.textArea.bind("<Control-Key-y>",self.redo)
		self.textArea.bind("<Button-3>",self.show_rc)
		root.bind("<Button-1>",self.hide_rc)
		self.fdArea.bind("<Double-Button-1>",lambda x:self.symbol_select())
		self.rcmenu = tk.Menu(self.textArea,tearoff=0,font=("",14),bg="#fff",fg="#000")
		self.rcmenu.add_command(label="Cut", command=lambda:self.textArea.event_generate("<<Cut>>"))
		self.rcmenu.add_command(label="Copy", command=lambda:self.textArea.event_generate("<<Copy>>"))
		self.rcmenu.add_command(label="Paste", command=lambda:self.textArea.event_generate("<<Paste>>"))
		self.rcmenu.add_command(label="Select all", command=lambda:self.textArea.tag_add("sel", "1.0", "end-1c"))
		#show
		self.fileArea.pack()
		self.fscpArea.pack()
		self.fdArea.pack(fill="both",expand=True)
		csy.pack(side="right",fill="y")
		csx.pack(side="bottom",fill="x")
		self.lids.pack(side="left",fill="y")
		self.textArea.pack(side="left",fill="both",expand=True)
		self.msgArea.pack(fill="both",expand=True)
		self.expectTab.pack()
		eTA.pack()
		mW.pack(fill="both",expand=True)
		bW.pack(fill="both",expand=True)
		mW.add(meF)
		mW.add(cdF)
		bW.add(mW)
		bW.add(msF)
		root.title("gaku-ura editor/学裏エディター")
		self.show_msg("start gakuraeditor\n")
		#open
		if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
			self.show_file(sys.argv[1])
		else:
			self.new_open(gkrs.entry_point_gkrs, ";main scenario file\n@define TITLE hello\nhello, world!\n")
	def lh(self):
		return int(self.fs//4) #行間の半分(上下)
	def add_expect(self):
		if self.fname != "":
			self.expect[self.fname.replace("\\","/")] = {"fcontent":self.fcontent,"tcontent":self.textArea.get("1.0","end-1c").replace("\r\n","\n").replace("\r","\n"),"ftype":self.ftype,"focus":self.textArea.index("insert")}
			k = list(self.expect.keys())
			k.reverse()
			self.expectTab.config(values=k)
	def remove_expect(self, file):
		f = file.replace("\\","/")
		if f in self.expect:
			del self.expect[f]
			self.expectTab.config(values=list(self.expect.keys()))
	def open_file(self):
		try:
			f = filedialog.askopenfilename(filetypes=[("All Files","*.*")],initialdir=gkrs.d_root)
		except:
			return "break"
		if f:
			self.show_file(f)
		return "break"
	def show_file(self, file=""):
		f = file.replace("\\","/")
		self.add_expect()
		if f == "":
			if self.fname == "":
				return
			f = self.fname
		try:
			with open(f,"r",encoding="utf-8") as fp:
				c = fp.read()
		except:
			self.show_msg("can not open "+f)
			return
		self.fname = f
		self.ftype = f[f.rfind(".")+1:].lower()
		self.fcontent = c
		self.show_text(c, f)
		self.show_msg("open file:"+f)
		self.fileArea.config(text=os.path.basename(f))
		if f in self.expect:
			self.textArea.see(self.expect[f]["focus"])
			self.textArea.mark_set("insert",self.expect[f]["focus"])
			self.textArea.focus()
			self.sync_scroll()
			self.remove_expect(f)
	def show_file_expect(self, f):
		self.add_expect()
		if f not in self.expect or not os.path.isfile(f):
			self.show_msg("can not reopen "+f)
			self.remove_expect(f)
			return
		self.fname = f
		self.ftype = self.expect[f]["ftype"]
		self.fcontent = self.expect[f]["fcontent"]
		self.show_text(self.expect[f]["tcontent"], f)
		self.show_msg("reopen file:"+f)
		self.fileArea.config(text=os.path.basename(f))
		self.textArea.see(self.expect[f]["focus"])
		self.textArea.mark_set("insert",self.expect[f]["focus"])
		self.textArea.focus()
		self.sync_scroll()
		self.remove_expect(f)
	def show_save(self):
		try:
			f = filedialog.asksaveasfilename(filetypes=[("All Files","*.*")],initialdir=gkrs.d_root)
		except:
			return
		if f:
			self.save_file(f)
	def save_file(self, f=None):
		if f == None and self.fname == "":
			self.show_save()
		else:
			if self.fname != "" and f == None:
				f = self.fname
			c = self.textArea.get("1.0","end-1c").replace("\r\n","\n").replace("\r","\n")
			if c[-1:] != "\n":
				c += "\n"
				self.textArea.insert(tk.END,"\n")
			try:
				with open(f,"w",**gkrs.m_u8lf) as fp:
					fp.write(c)
			except:
				self.show_msg(f+" could not save")
				return
			self.fname = f
			self.ftype = f[f.rfind(".")+1:].lower()
			self.fcontent = c
			self.show_msg("save file:"+f)
			self.check_his()
			self.fileArea.config(text=os.path.basename(f))
			self.hlstring()
		return "break"
	def new_open(self, path, notexists=""):
		if not os.path.exists(path):
			with open(path,"w",encoding="utf-8") as fp:
				fp.write(notexists+"\n")
		self.show_file(path)
	def new_file(self):
		self.add_expect()
		self.fname = ""
		self.ftype = ""
		self.fcontent = ""
		self.fscpArea.config(text="")
		self.fdArea.delete(0,tk.END)
		self.fileArea.config(text="United")
		self.show_text("")
	def chftype(self, t):
		self.ftype = t
		self.hlstring()
		self.show_msg("reload as "+t)
	def show_text(self, text, title="United"):
		self.textArea.delete("1.0",tk.END)
		self.textArea.insert(tk.END,text)
		self.textArea.edit_reset()
		self.textArea.mark_set("insert","@1,1")
		self.hlstring()
		self.update_lids()
		root.title(title+" -gaku-ura")
		self.check_his()
	def export_as(self, to):
		if self.fname == "" or self.ftype != "gkrs":
			self.show_msg("file type is not 'gkrs'.")
			return
		r = gkrs.export_as(self.fname, to)
		if r[0] == gkrs.e_none:
			self.fname = ""
			self.ftype = to
			self.fcontent = ""
			self.show_text(r[1],"exported "+to)
		else:
			self.show_msg(r[1])

	def show_msg(self, text, c=False):
		text = ">> "+text+"\n"
		if c:
			self.msgArea.delete("1.0",tk.END)
		self.msgArea.insert(tk.END,text)
		self.msgArea.see(tk.END)
		for k, v in self.hltagsM.items():
			self.msgArea.tag_remove(k,"1.0",tk.END)
		t = self.msgArea.get("1.0",tk.END)
		for i, l in enumerate(t.splitlines()):
			li = str(i+1)+"."
			ls = li+"0"
			le = li+"end"
			row = l.strip()
			if row[:3] == ">> ":
				self.msgArea.tag_add("keyword",ls,li+"2")
			if l.find("line") != -1:
				self.msgArea.tag_add("keyword",li+str(l.find("line")),le)
		p = 0
		while (f1:=t[p:].find("[")) != -1 and (f2:=t[p+f1+1:].find("]")) != -1:
			f2 += f1+2
			self.msgArea.tag_add("section",tk_nc(f1+p),tk_nc(f2+p))
			p += f2
	def check_his(self):
		if self.fcontent == self.textArea.get("1.0","end-1c"):
			self.fileArea.config(fg="#15b")
		else:
			self.fileArea.config(fg="#c00")
	def zoom(self, z=True):
		if z:
			self.fs = min(self.fs+1,50)
		else:
			self.fs = max(self.fs-1,1)
		self.textArea.config(spacing1=self.lh(),spacing3=self.lh(),font=("Courier",self.fs))
		self.lids.config(spacing1=self.lh(),spacing3=self.lh(),font=("Courier",self.fs))
	def hlstring(self):
		if self.ftype == "":
			return
		content = self.textArea.get("1.0",tk.END)
		mlcomment = False
		self.fileData = {}
		symbol = {}
		scp = ""
		cin = float(self.textArea.index("insert"))
		self.fdArea.delete(0,tk.END)
		for k, v in self.hltags.items():
			self.textArea.tag_remove(k,"1.0",tk.END)
		if self.ftype == "gkrs":
			symbol = {"section":[],"function":[],"variable":[],"include":[],"character":[]}
			for i,l in enumerate(content.splitlines(),1):
				is_h = False
				is_n = False
				is_dq = False
				li = str(i)+"."
				ls = li+"0"
				le = li+"end"
				row = l.strip()
				if row.startswith(";") or row.startswith("//"):
					self.textArea.tag_add("comment",ls,le)
					continue
				if row.startswith("@"):
					if row.find(" ") == -1:
						self.textArea.tag_add("command",ls,le)
					else:
						self.textArea.tag_add("command",ls,li+str(row.find(" ")+l.find("@")))
						cm = gkrs.subrpos("@"," ",row)
						if gkrs.subrpos("@<",">",l[:l.find(" ")]) != "":
							is_dq = True
						elif cm == "function":
							if row.find("(") != -1:
								symbol["function"].append([gkrs.subrpos(" ","(",row).strip(),i])
								self.textArea.tag_add("command",li+str(l.find(" ")),li+str(l.find("(")))
						elif cm == "html":
							is_h = True
						elif cm == "eval" or cm == "regist":
							is_dq = True
							p = 0
							while (f1:=l[p:].find("'")) != -1 and (f2:=l[p+f1+1:].find("'")) != -1:
								f2 += f1+2
								self.textArea.tag_add("string",li+str(f1+p),li+str(f2+p))
								p += f2
						else:
							self.textArea.tag_add("string",li+str(row.find(" ")+l.find("@")),le)
						if cm == "var":
							symbol["variable"].append([l.replace("@"+cm+" ","").strip(),i])
						elif cm == "include":
							symbol["include"].append([l.replace("@"+cm+" ","").strip(),i])
						elif cm == "chara":
							ags = l.split(" ")
							if len(ags) > 3:
								symbol["character"].append([ags[1]+"("+ags[3]+")",i])
							else:
								symbol["character"].append([ags[1],i])
				elif row.startswith("[") and row.endswith("]"):
					ps = gkrs.subrpos("[", "]", row).strip()
					if ps not in ["else","end"]:
						symbol["section"].append([ps,i])
						if cin >= i and ps[:2] != "if":
								scp = ps
					self.textArea.tag_add("section",ls,le)
				elif row.startswith("#"):
					is_n = True
					self.textArea.tag_add("name",ls,le)
				else:
					is_n = True
					is_h = True
				p = 0
				while (f1:=l[p:].find("[[")) != -1 and (f2:=l[p+f1+2:].find("]]")) != -1:
					f2 += f1+4
					for k, v in self.hltags.items():
						self.textArea.tag_remove(k,li+str(f1+p),li+str(f2+p))
					self.textArea.tag_add("macro",li+str(f1+p),li+str(f2+p))
					p += f2
				if is_h:
					p = 0
					while (f1:=l[p:].find('<')) != -1 and (f2:=l[p+f1+1:].find('>')) != -1:
						f2 += f1+2
						self.textArea.tag_add("command",li+str(f1+p),li+str(f2+p))
						p += f2
				if is_n:
					p = 0
					while (f1:=l[p:].find("<$")) != -1 and (f2:=l[p+f1+2:].find(">")) != -1:
						f2 += f1+3
						for k, v in self.hltags.items():
							self.textArea.tag_remove(k,li+str(f1+p),li+str(f2+p))
						self.textArea.tag_add("variable",li+str(f1+p),li+str(f2+p))
						p += f2
				if is_dq:
					p = 0
					while (f1:=l[p:].find('"')) != -1 and (f2:=l[p+f1+1:].find('"')) != -1:
						f2 += f1+2
						self.textArea.tag_add("string",li+str(f1+p),li+str(f2+p))
						p += f2
		elif self.ftype == "html":
			symbol = {"section":[]}
			content = content.replace(r"\'","''").replace(r'\"','""')
			p = 0
			while (f1:=content[p:].find("<")) != -1 and (f2:=content[p+f1+1:].find(">")) != -1:
				f2 += f1+2
				self.textArea.tag_add("command",tk_nc(f1+p),tk_nc(f2+p))
				tg = content[f1+p:f2+p]
				if tg in ["<title>","<h1>","<h2>","<h3>","<h4>","<h5>","<h6>","<main>","<article>","<aside>"]:
					symbol["section"].append([tg[1:-1].strip(),len(content[:f2+p].splitlines())])
				p += f2
			p = 0
			while (f1:=content[p:].find('"')) != -1 and (f2:=content[p+f1+1:].find('"')) != -1:
				f2 += f1+2
				self.textArea.tag_add("string",tk_nc(f1+p),tk_nc(f2+p))
				p += f2
			p = 0
			while (f1:=content[p:].find("<!--")) != -1 and (f2:=content[p+f1+4:].find("-->")) != -1:
				f2 += f1+7
				for k, v in self.hltags.items():
					self.textArea.tag_remove(k,tk_nc(f1+p),tk_nc(f2+p))
				self.textArea.tag_add("comment",tk_nc(f1+p),tk_nc(f2+p))
				p += f2
		elif self.ftype == "css":
			symbol = {"function":[]}
			mlcomment = True
			p = 0
			sts = 0
			rl = []
			while (f1:=content[p:].find("{")) != -1 and (f2:=content[p:].find("}")) != -1:
				f2 += 1
				l = len(content[:sts+f1].splitlines())
				if l not in rl:
					sl = content[sts:sts+f1]
					if len(sl.splitlines()) > 1:
						sl = sl.splitlines()[-1:]
					symbol["function"].append([sl.strip(),l])
					rl.append(l)
				self.textArea.tag_add("command",tk_nc(sts),tk_nc(p+f1))
				sts += f2
				lb = content[p+f1:f2+p]
				p2 = 0
				while (f3:=lb[p2:].find(":")) != -1 and (f4:=lb[p2+f3+1:].find(";")) != -1:
					f4 += f3+2
					self.textArea.tag_add("string",tk_nc(f3+p2+f1+p+1),tk_nc(f4+p2+f1+p))
					p2 += f4
				p += f2
		elif self.ftype == "js":
			mlcomment = True
			for i,l in enumerate(content.splitlines(),1):
				li = str(i)+"."
				ls = li+"0"
				le = li+"end"
				rf = l.find("//")
				if rf != -1:
					self.textArea.tag_add("comment",li+str(rf),le)
		elif self.ftype == "md":
			symbol = {"section":[]}
			for i,l in enumerate(self.textArea.get("1.0",tk.END).splitlines(),1):
				li = str(i)+"."
				ls = li+"0"
				le = li+"end"
				row = l.strip()
				if row.find("# ") != -1:
					self.textArea.tag_add("section",ls,le)
					s = row[row.find("# ")+2:].strip()
					symbol["section"].append([s,i])
					if cin >= i:
						scp = s
		if mlcomment:
			p = 0
			while (f1:=content[p:].find("/*")) != -1 and (f2:=content[p+f1+2:].find("*/")) != -1:
				f2 += f1+4
				for k,v in self.hltags.items():
					self.textArea.tag_remove(k,tk_nc(f1+p),tk_nc(f2+p))
				self.textArea.tag_add("comment",tk_nc(f1+p),tk_nc(f2+p))
				p += f2
		for k,v in symbol.items():
			self.fileData[k] = "title"
			for i in v:
				if i[0] in self.fileData:
					self.fileData[i[0]+"("+str(list(self.fileData.keys()).count(i[0]))+")"] = i[1]
				else:
					self.fileData[i[0]] = i[1]
		i = 0
		for k,v in self.fileData.items():
			if v == "title":
				self.fdArea.insert(tk.END,k+"▼")
				self.fdArea.itemconfig(i,fg="#938")
			else:
				self.fdArea.insert(tk.END,"  "+k+" ["+str(v)+"]")
			i += 1
		self.fscpArea.config(text=scp)
	def update_lids(self):
		lines = self.textArea.get("1.0",tk.END).split("\n")
		self.lids.config(state="normal")
		self.lids.delete("1.0",tk.END)
		self.lids.insert("1.0","\n".join(map(str,range(1,len(lines)))))
		self.lids.config(state="disabled")
		self.lids.config(width=len(str(len(lines)-1)))
	def void_key(self,e):
		return "break"
	def hide_rc(self,e):
		try:
			self.rcmenu.unpost()
		except:
			pass
	def show_rc(self,e):
		self.rcmenu.post(e.x_root,e.y_root)
	def key_in(self, k):
		self.check_his()
		self.hlstring()
		self.update_lids()
		self.sync_scroll()
	def inscode(self, c, r=False):
		i = self.textArea.index("insert")
		if r:
			self.textArea.insert("insert",c)
		else:
			if i[i.find(".")+1:] == "0":
				self.textArea.insert("insert",c+"\n")
			else:
				self.textArea.insert("insert","\n"+c+"\n")
		self.textArea.see(i)
		self.key_in("")
	def row_comment(self):
		i = self.textArea.index("insert")
		if self.fname.endswith(".gkrs"):
			self.textArea.insert(i[:i.find(".")]+".0",";")
		else:
			self.textArea.insert(i[:i.find(".")]+".0","//")
		self.textArea.see(i)
		self.key_in("")
	def k_open_file(self,e):
		self.open_file()
		return "break"
	def select_all(self,e):
		self.textArea.tag_add("sel","1.0","end-1c")
		return "break"
	def copy(self,e):
		self.textArea.event_generate("<<Copy>>")
		return "break"
	def cut(self,e):
		self.textArea.event_generate("<<Cut>>")
		return "break"
	def paste(self,e):
		self.textArea.event_generate("<<Paste>>")
		return "break"
	def undo(self,e=0):
		try:
			self.textArea.edit_undo()
		except:
			pass
		if e == 0:
			self.key_in("")
		return "break"
	def redo(self,e=0):
		try:
			self.textArea.edit_redo()
		except:
			pass
		if e == 0:
			self.key_in("")
		return "break"
	def scroll(self, *args):
		self.textArea.yview(*args)
		self.lids.yview(*args)
		self.sync_scroll()
	def sync_scroll(self, e=None):
		self.lids.yview_moveto(self.textArea.yview()[0])
	def sync_scrolll(self, e=None):
		self.textArea.yview_moveto(self.lids.yview()[0])
	def symbol_select(self):
		if not self.fdArea.curselection():
			return
		k = list(self.fileData.keys())
		i = self.fdArea.curselection()[0]
		if k[i]:
			if self.fileData[k[i]] == "title":
				return
			s = str(self.fileData[k[i]])+"."
			self.textArea.yview(s+"0")
			self.sync_scroll()
			if "hl" in self.textArea.tag_names(s+"0"):
				self.textArea.tag_remove("hl",s+"0",s+"end")
			else:
				self.textArea.tag_add("hl",s+"0",s+"end")
	def compile(self, o, b, use_main=True):
		if self.fname!="" and self.fcontent!=self.textArea.get("1.0","end-1c"):
			self.save_file(self.fname)
		if use_main:
			r = gkrs.start_build(o, b)
			self.show_msg("[gakuracompiler this project] "+r[1])
		else:
			r = gkrs.start_build(o, b, {"first":True,"file":self.fname})
			self.show_msg("[gakuracompiler "+self.fname+"]"+r[1])
		if r[0] != gkrs.e_none:
			if r[3] != self.fname:
				self.show_file(r[3])
			self.textArea.tag_add("error",str(r[2])+".0",str(r[2])+".end")
			self.textArea.see(str(r[2])+".0")
			self.sync_scroll()
	def show_help(self):
		web.open("http://bq.f5.si/?Page=novelcompiler")
if __name__ == "__main__":
	root = tk.Tk()
	root.geometry("1000x600")
	root.config(bg="#ffc")
	i = gkrs.d_root+"/favicon.ico"
	if os.path.isfile(i):
		try:
			root.iconbitmap(default=i)
		except:
			pass
	GsEditor()
	root.mainloop()

