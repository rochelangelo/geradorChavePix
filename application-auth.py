import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver_path = "./chromedriver-win64/chromedriver.exe"
service = Service(driver_path)
options = Options()
options.add_argument(r'--user-data-dir=C:\Users\roche\AppData\Local\Google\Chrome\User Data')
driver = webdriver.Chrome(service=service, options=options)


# driver_path = "./chromedriver-win64/chromedriver.exe"
# service = Service(driver_path)
# options = webdriver.ChromeOptions()
# driver = webdriver.Chrome(service=service, options=options)



def abrir_mercado_pago():
    driver.get("https://www.mercadopago.com.br/pix/home")

# Início do processo
abrir_mercado_pago()

try:
    print("Faça o login manualmente na janela aberta. Aguardando confirmação de login...")
    WebDriverWait(driver, 300).until(
        EC.visibility_of_element_located((By.XPATH, "/html/body/div/main/header/h1"))
    )
    print("Login detectado com sucesso. Salvando os cookies para futuras execuções...")

except Exception as e:
    print("Erro ao fazer o login:", e)

driver.quit()
