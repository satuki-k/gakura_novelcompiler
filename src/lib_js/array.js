/* 配列について */

function list_isset(dict, keys){
	for (let i = 0; i < keys.lengt; ++i){
		if (dict.indexOf(keys[i]) == -1){
			return false;
		}
	}
	return true;
}

