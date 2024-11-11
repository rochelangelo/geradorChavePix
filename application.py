import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import json
import os
import re
import time
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class MercadoPagoPixManager:
    def __init__(self, driver):
        self.driver = driver
        self.COOKIES_FILE = "mercado_pago_cookies.json"
        self.CHAVES = []

    def abrir_mercado_pago(self):
        self.driver.get("https://www.mercadopago.com.br/pix/home")

    def abrir_gerador_email(self):
        self.driver.execute_script("window.open('https://www.invertexto.com/gerador-email-temporario', '_blank');")

    def esperar_elemento(self, xpath, timeout=10, clickable=False):
        condition = EC.element_to_be_clickable((By.XPATH, xpath)) if clickable else EC.visibility_of_element_located(
            (By.XPATH, xpath))
        return WebDriverWait(self.driver, timeout).until(condition)

    def inserir_email(self, email, xpath):
        email_input = self.esperar_elemento(xpath)
        email_input.clear()
        email_input.send_keys(email)
        print(f"Email {email} inserido com sucesso.")

    def clicar_botao(self, xpath):
        button = self.esperar_elemento(xpath, clickable=True)
        button.click()

    def obter_codigo_email(self):
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.esperar_elemento("//div[@class='maillist expand']//tbody/tr", timeout=300).click()
        self.esperar_elemento("//div[@id='body']")
        corpo_email = self.driver.find_element(By.ID, "body").text
        codigo = re.search(r'\b\d{6}\b', corpo_email)
        return codigo.group(0) if codigo else None

    def inserir_codigo_verificacao(self, codigo):
        for i, digito in enumerate(codigo):
            input_digit = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, f":R6muh:-digit-{i}"))
            )
            input_digit.send_keys(digito)

    def criar_chave_pix(self, email_gerado):
        caminho_secundario = False

        # Tenta clicar no botão "Cadastrar chave" ou alternativo "Gerenciar chaves Pix"
        try:
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div/main/section/div/section[1]/div/div/div/div/button"))
            ).click()
        except:
            caminho_secundario = True
            print("Botão 'Cadastrar chave' não encontrado. Tentando o processo alternativo...")
            WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div/main/section/div/section[2]/div/div/div/div/button"))
            ).click()
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/main/section/div/div/div[3]/button"))
            ).click()

        # Cadastrar com email
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div/main/section/div/div/section/div/div[3]/ul/li/button"))
        ).click()

        if caminho_secundario:
            self.inserir_email(email_gerado, "/html/body/div/main/section/div/div/div[1]/div/input")
        else:
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div/main/section/div/div/div/section/div/div/div[2]/ul/li/button"))
            ).click()
            self.inserir_email(email_gerado, "/html/body/div/main/section/div/div/div[1]/div/input")

        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div/main/section/div/div/div[2]/button"))
        ).click()

        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/main/section/div/div/div/div[2]/button"))
        ).click()

        # Obtendo código de verificação do email
        codigo_verificacao = self.obter_codigo_email()
        if codigo_verificacao:
            print(f"Código de verificação: {codigo_verificacao}")
            self.driver.switch_to.window(self.driver.window_handles[0])
            time.sleep(2)
            self.inserir_codigo_verificacao(codigo_verificacao)
            time.sleep(1)
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/main/div/div[2]/div/form/button[1]"))
            ).click()
            time.sleep(5)
            self.CHAVES.append(email_gerado)
            print("Processo de validação do código concluído com sucesso!")
        else:
            print("Código de verificação não encontrado.")

    def limpar_chaves_pix(self):
        self.abrir_mercado_pago()
        time.sleep(2)
        # Clique no botão "Gerenciar chaves" ou equivalente
        try:
            WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div/main/section/div/section[2]/div/div/div/div/button"))
            ).click()
        except Exception as e:
            print(f"Erro ao clicar em 'Gerenciar chaves': {e}")
            return

        time.sleep(2)

        try:
            # Aguarda a presença dos itens de chave Pix
            chaves_pix_itens = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "andes-list__item"))
            )
        except TimeoutException:
            print("Não há mais chaves Pix para excluir.")
            return

        if not chaves_pix_itens:
            print("Não há mais chaves Pix para excluir.")
            return

        index_div = 1
        for chave_item in chaves_pix_itens:

            try:
                # Encontrar o botão de menu (dropdown) dentro do item
                menu_botao = chave_item.find_element(By.XPATH, "/html/body/div[1]/main/section/div/div/div[2]/div/div[2]/ul/div[1]/div/li/div/div/span/span/div/div/div/i")
                menu_botao.click()
                print("Abriu o menu dropdown da chave Pix.")
                time.sleep(2)
                # Aguarda o menu aparecer e clica na opção 'Excluir chave'
                excluir_opcao = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH,
                                                "/html/body/div[1]/main/section/div/div/div[2]/div/div[2]/ul/div[1]/div/li/div/div/span/span/div/div/div[2]/div/div/div/div/div[2]/div/div[2]/div"))
                )
                excluir_opcao.click()
                print("Clicou em 'Excluir chave'.")

                # Confirma a exclusão
                confirmar_botao = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div/div/div[2]/div[3]/button[1]"))
                )
                confirmar_botao.click()
                print("Chave Pix excluída com sucesso.")

                # Aguarda um pequeno intervalo para evitar problemas
                time.sleep(5)
                index_div += 1
            except Exception as e:
                print(f"Erro ao excluir a chave Pix: {e}")
                break

    def salvar_cookies(self):
        cookies = self.driver.get_cookies()
        with open(self.COOKIES_FILE, "w") as file:
            json.dump(cookies, file)
        print("Cookies salvos com sucesso.")

    def carregar_cookies(self):
        with open(self.COOKIES_FILE, "r") as file:
            cookies = json.load(file)
            for cookie in cookies:
                if "domain" in cookie:
                    del cookie["domain"]  # Remove o domínio para evitar incompatibilidades
                self.driver.add_cookie(cookie)
        print("Cookies carregados com sucesso.")

def run_action(action, num_chaves=5, chaves_text_widget=None):
    # Inicializa o driver
    driver_path = "./chromedriver-win64/chromedriver.exe"
    service = Service(driver_path)
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)

    # Inicializa o gerenciador de chaves PIX
    mp_manager = MercadoPagoPixManager(driver)

    try:
        mp_manager.abrir_mercado_pago()

        # Verifica se o arquivo de cookies existe
        if os.path.exists(mp_manager.COOKIES_FILE):
            mp_manager.carregar_cookies()
            driver.refresh()
        else:
            print("Faça o login manualmente na janela aberta. Aguardando confirmação de login...")
            WebDriverWait(driver, 300).until(
                EC.visibility_of_element_located((By.XPATH, "/html/body/div/main/header/h1"))
            )
            print("Login detectado com sucesso. Salvando os cookies para futuras execuções...")
            mp_manager.salvar_cookies()

        WebDriverWait(driver, 300).until(
            EC.visibility_of_element_located((By.XPATH, "/html/body/div/main/header/h1"))
        )

        if action == 'Criar':
            for i in range(num_chaves):
                mp_manager.abrir_gerador_email()
                driver.switch_to.window(driver.window_handles[1])  # Muda para a última aba aberta

                # Obtendo email temporário
                email_gerado = mp_manager.esperar_elemento("/html/body/main/div[1]/div[2]/div/div/input").get_attribute("value")
                print(f"Email gerado ({i + 1}/{num_chaves}): {email_gerado}")

                # Retornando para o MercadoPago
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(2)

                # Criar chave Pix com o email gerado
                mp_manager.criar_chave_pix(email_gerado)

                # Fecha a aba do gerador de email
                driver.switch_to.window(driver.window_handles[1])
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

                mp_manager.abrir_mercado_pago()

                # Atualiza o campo de texto com as chaves criadas
                if chaves_text_widget is not None:
                    chaves_text_widget.insert(tk.END, f"{email_gerado}\n")
                    chaves_text_widget.see(tk.END)

            print("Chaves geradas:")
            for chave in mp_manager.CHAVES:
                print(chave)
            messagebox.showinfo("Sucesso", "Chaves criadas com sucesso!")
        elif action == 'Limpar':
            mp_manager.limpar_chaves_pix()
            print("Todas as chaves PIX foram limpas com sucesso.")
            messagebox.showinfo("Sucesso", "Todas as chaves PIX foram limpas com sucesso.")

    except Exception as e:
        print("Erro:", e)
        messagebox.showerror("Erro", f"Ocorreu um erro: {e}")
    finally:
        # Finaliza o navegador
        driver.quit()

def start_action(action_var, num_chaves_var, chaves_text_widget):
    action = action_var.get()
    num_chaves = int(num_chaves_var.get())

    # Limpa o campo de texto antes de iniciar a criação
    if action == 'Criar':
        chaves_text_widget.delete('1.0', tk.END)

    # Executa em uma thread separada para não bloquear a interface
    threading.Thread(target=run_action, args=(action, num_chaves, chaves_text_widget)).start()

def main():
    root = tk.Tk()
    root.title("Gerenciador de Chaves PIX - Mercado Pago")

    # Configurações da janela
    root.geometry("500x400")
    root.resizable(False, False)

    # Variáveis
    action_var = tk.StringVar(value="Criar")
    num_chaves_var = tk.StringVar(value="5")

    # Widgets
    tk.Label(root, text="Selecione a ação:", font=("Arial", 12)).pack(pady=10)
    tk.Radiobutton(root, text="Criar Chaves PIX", variable=action_var, value="Criar", font=("Arial", 10)).pack()
    tk.Radiobutton(root, text="Limpar Chaves PIX", variable=action_var, value="Limpar", font=("Arial", 10)).pack()

    tk.Label(root, text="Número de chaves (apenas para criação):", font=("Arial", 12)).pack(pady=10)
    tk.Entry(root, textvariable=num_chaves_var, font=("Arial", 12), width=5).pack()

    # Botão "Iniciar" aumentado
    iniciar_btn = tk.Button(root, text="Iniciar", command=lambda: start_action(action_var, num_chaves_var, chaves_text), font=("Arial", 14), width=20, height=2)
    iniciar_btn.pack(pady=20)

    # Campo para exibir as chaves criadas
    chaves_label = tk.Label(root, text="Chaves Criadas:", font=("Arial", 12))
    chaves_label.pack(pady=5)
    chaves_text = scrolledtext.ScrolledText(root, width=60, height=10, font=("Arial", 10))
    chaves_text.pack(pady=5)

    root.mainloop()

if __name__ == '__main__':
    main()
