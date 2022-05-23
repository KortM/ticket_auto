from argparse import Action
from msilib.schema import Class
from multiprocessing.sharedctypes import Value
from select import select
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import Select
import time
from bs4 import BeautifulSoup
import configparser
from os.path import exists

if exists('config.ini'):
    config = configparser.ConfigParser() 
    config.read('config.ini')
    if config.sections():
        print('Настраиваем chrome.')
        options = Options()
        options.headless = bool(config['Default']['headless'])
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.binary_location = config['Default']['ChromePath']
        #options.binary_location = 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
        #driver = webdriver.Chrome(executable_path='chromedriver.exe', chrome_options=options)
        driver = webdriver.Chrome(executable_path=config['Default']['ChromeDriverPath'], chrome_options=options)
else:
    print('Нет файла конфигурации - config.ini')
    with open('config.ini', 'w') as f:
        config = configparser.ConfigParser()
        config['Default'] = {
            'headless': True,
            'ChromePath': 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
            'ChromeDriverPath': 'chromedriver.exe'
        }
        config['User'] = {
            'fastcome_user_name': 'your_username',
            'fastcom_pwd': 'your_fast_password',
            'moncms_username': 'monc_username',
            'moncms_user_pwd': 'monc_password'
        }
        config.write(f)


def find_task(type_task = '16192762'):
    '''
    Открываем фастком, смотрим задания, в зависимости от type_task (фильтр - нужно вытаскивать из фасткома)
    По умолчанию восстановления.
    Выгружаем задания в файл task.html
    '''
    global driver

    driver.get('https://bill.ad.severen.net/')
    element = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.CLASS_NAME,"logon-user")))
    element.send_keys('marchenkoia')
    element = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.CLASS_NAME,"logon-password")))
    element.send_keys('1234')
    element = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.CLASS_NAME,"logon-button")))
    element.click()
    element = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.XPATH,"//*[text()='Документооборот тех. служб']")))
    action = ActionChains(driver)
    action.double_click(element).perform()
    element = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.XPATH,"//div[contains(text(),'Задания')]")))
    action = ActionChains(driver)
    action.double_click(element).perform()
    element = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.CLASS_NAME,"grid-configs")))
    element.click()
    select = Select(WebDriverWait(driver,30).until(EC.presence_of_element_located((By.CLASS_NAME,"grid-configs"))))
    select.select_by_value(type_task)
    time.sleep(10)
    element = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.TAG_NAME,"tbody")))

    with open('task.html', 'w') as f:
        f.write(element.get_attribute('innerHTML'))
        f.close()

def parse_task() -> list:
    '''
        Открываем файл task.html и формируем список заданий. 
    '''
    data = []
    with open('task.html', 'r') as f:
        soup = BeautifulSoup(f, 'html.parser')
        rows = soup.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            content = cols[1].find_all('div', class_ = 'cell-content')
            cols = [ele.text.strip() for ele in content]
            if cols:
                data.append(cols)
    #print(data)
    return data if data else None

def close_task(task_id):
    '''
        Закрываем задание по его ID (Фастком)
    '''
    element = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.XPATH,"//*[contains(text(),'{}')]".format(task_id))))
    element = element.find_element(by=By.XPATH, value = '../../../../../..')
    action = ActionChains(driver)
    action.context_click(element).perform()
    element = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.XPATH,"//*[contains(text(),'{}')]".format('Ввести дату завершения'))))
    element.click()
    element = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.XPATH,"//*[contains(text(),'{}')]".format('Выполнить'))))
    #element.click()

def check_phone_type() -> list:
    '''
        Проверяем тип номера, отсеиваем не voip задания.
        Возвращаем валидные задания и нет. Индексы 0 и 1 соответственно. 
    '''
    phone_types = ['VIOPPHONE', 'VOIPSER', 'VOIPTRUNK', 'PUCHEKL', 'ВИРДВО'.encode('utf-8'), 'ИНТПЛАТФОРМА'.encode('utf-8'), 'ТЕЛДВО'.encode('utf-8')]
    tasks = parse_task()
    valid_task = []
    invalid_task = []

    for task in tasks:
        print(task[28])
        if task[28] in phone_types:
            valid_task.append(task)
        else:
            invalid_task.append(task)

    return valid_task, invalid_task

def check_trunk(trunk: str, user_name: str, pwd: str) -> list:
    '''Авторизуемся в монс, ищем номер, смотрим транк ли это? 
    Если транк, то собираем список номеров.
    В любом случае будет возвращать список, даже если номер один.
    trunk -> номер транка (телефона),
    user_name -> имя пользователя для авторизации в монс, 
    pwd -> пароль. 
    '''

    url = 'https://moncms.ad.severen.net/request-support/add'
    driver.get(url)
    if driver.current_url != url:
        try:
            print('Нужна авторизация в монс')
            element = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.ID,"username")))
            element.send_keys(user_name)
            element = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.ID,"password")))
            element.send_keys(pwd)
            element = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.XPATH,"//*[text()='Войти']")))
            element.click()
            print('Авторизовались в монс')
            element = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.ID,"phone")))
            element.send_keys(trunk)
            element = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.XPATH,"//*[text()='Найти']")))
            element.click()
            element = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.TAG_NAME,"tbody")))
            #print(element.get_attribute('innerHTML'))
            soup = BeautifulSoup(element.get_attribute('innerHTML'), 'html.parser')
            rows = soup.find_all('tr')
            obj_id = []
            for row in rows:
                try:
                    cols = row.find_all('td')
                    obj_id.append(cols[0].find('input')['name'])
                    #print(cols[0].find('input')['name'])
                except Exception:
                    pass
                    #print('Class not found')
            if obj_id:
                element = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.NAME, obj_id[0])))
                element.click()
                element = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.XPATH,"//*[text()='Продолжить']")))
                element.click()
                element = WebDriverWait(driver,30).until(EC.presence_of_element_located((By.CLASS_NAME,"panel-body")))
                soup = BeautifulSoup(element.get_attribute('innerHTML'), 'html.parser')
                panel = soup.find('div', class_ = 'panel-group')
                table = panel.find('tbody')
                rows = table.find_all('tr')
                table_rows = []
                for row in rows:
                    cols = row.find_all('td')
                    cols = [ele.text.strip() for ele in cols]
                    table_rows.append(cols)
                table_rows = [line for line in table_rows if not line[2]]
                table_rows = [line[3] for line in table_rows]
                
                return table_rows
        except Exception as e:
            print('Авторизация в монс не удалась!', e)
            return None


if __name__ == '__main__':
    #parse_ui()
    #close_task('791707')
    print(check_phone_type())
    print(check_trunk(6415199, 'marchenkoia', '12345'))
