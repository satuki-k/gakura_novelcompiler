/* 配列について */

function list_isset(dict, keys){
	for (let i = 0; i < keys.lengt; ++i){
		if (keys[i] in dict){
			return false;
		}
	}
	return true;
}

