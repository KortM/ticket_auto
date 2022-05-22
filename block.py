import numbers
from turtle import pos
from urllib import response
import requests
from bs4 import BeautifulSoup

def block_dp(phone: str, id: str, name: str) -> bool:
    url = 'http://10.80.201.12/block/mttblockapi.php?cmd=edit'
    post = {
			'number': '812%s' % phone,
			'description': '%s %s' % (id, name),
			'block_in': 'Да',
			'block_out': 'Да',
			'oper': 'add',
			'id': '_empty'
	    }
    response = requests.post(url, data=post)
    if response.status_code == 200:
        return True
    return False

def unblock_dp(phone: str) -> bool:
    url = 'http://10.80.201.12/block/mttblockapi.php?cmd=edit'
    post = {
			'oper':'del',
			'id':'812%s' % phone
		}
    response = requests.post(url, data=post)
    if response.status_code == 200: return True
    return False


if __name__ == '__main__':
    pass