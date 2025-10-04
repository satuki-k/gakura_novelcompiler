/* cssで補正しきれないレスポンシブ対応 */

//ウィンドウサイズに応じてフォントサイズを変更
function fit(){
	$ID("gaku-ura_base").style.fontSize = Math.max(12, Math.min(window.innerHeight*0.03, window.innerWidth*0.03))+"px";
}
fit();
window.addEventListener("resize", fit);

