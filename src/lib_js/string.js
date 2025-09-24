/* 文字列ツール */

/* エスケープ */
function h(str){
	return str
	.replace(/&/g, '&amp;')
	.replace(/</g, '&lt;')
	.replace(/>/g, '&gt;')
	.replace(/"/g, '&quot;')
	.replace(/'/g, '&#39;');
}
function lh(s){
	return Array.from(s,i=>h(i));
}

/* 切り抜き */
function subrpos(start, end, txt){
	let s = txt.indexOf(start);
	let e = txt.indexOf(end, s);
	if (s !== -1 && e !== -1){
		return txt.slice(s +start.length, e);
	} else {
		return '';
	}
}
/* 切除 */
function remove_comment_rows(code, s, e){
	while (subrpos(s, e, code) !== ''){
		code = code.replace(s+subrpos(s, e, code)+e, '');
	}
	return code;
}

function not_empty(s=""){
	if (s === null || s === undefined) return false;
	if (s
		.replace(" ", "")
		.replace(/　/g, "")
		.replace(/\s/g, "")
		.replace(/\r|\n|\r\n/, "") === ""){
		return false;
	} else {
		return true;
	}
}

