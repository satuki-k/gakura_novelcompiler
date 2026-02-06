/* 文字列ツール */
//エスケープ
function h(s){
	return s
	.replace(/&/g,"&amp;")
	.replace(/</g,"&lt;")
	.replace(/>/g,"&gt;")
	.replace(/"/g,"&quot;")
	.replace(/'/g,"&#39;");
}
function lh(s){
	return Array.from(s,(i)=>{h(i);});
}
//切り抜き
function subrpos(l, r, t){
	const s = t.indexOf(l);
	const e = t.indexOf(r, s+l.length);
	return (~s&&~e)?t.slice(s+l.length,e):"";
}
//切除
function remove_comment_rows(code, s, e){
	while(subrpos(s,e,code)!=="") code=code.replace(s+subrpos(s,e,code)+e,"");
	return code;
}
function not_empty(s=""){
	if(s===null||s===undefined) return false;
	return(s.replace(" ","").replace(/　/g,"").replace(/\s/g,"").replace(/\r|\n|\r\n/,"")!=="");
}

