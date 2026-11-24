"""
Teste de usabilidade (UI) do login com Selenium.
Pré-requisitos:
  1. pip install selenium pytest
  2. Subir o auth-service:  python app.py   (http://127.0.0.1:5000/auth/login)
  3. Ter um usuário cadastrado (ajuste EMAIL/SENHA abaixo)
Rodar:  pytest tests_selenium -v
"""
import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://127.0.0.1:5000/auth"
EMAIL = "aula1795556425@teste.com"
SENHA = "123456"
PAUSA = 1.5   # segundos entre cada acao (0 = velocidade normal)


def pausa():
    time.sleep(PAUSA)


@pytest.fixture
def driver():
    d = webdriver.Chrome()          # Selenium 4 baixa o driver sozinho
    d.implicitly_wait(10)
    yield d
    pausa()
    pausa()
    d.quit()


def preencher_login(driver, email, senha):
    driver.get(f"{BASE_URL}/login")
    pausa()
    driver.find_element(By.NAME, "email").send_keys(email)
    pausa()
    driver.find_element(By.NAME, "password").send_keys(senha)
    pausa()
    driver.find_element(By.CSS_SELECTOR, "button.btn-primary").click()
    pausa()


# 1) A página carrega e mostra os elementos esperados
def test_pagina_login_tem_campos(driver):
    driver.get(f"{BASE_URL}/login")
    assert "Login" in driver.title
    assert driver.find_element(By.NAME, "email").is_displayed()
    assert driver.find_element(By.NAME, "password").is_displayed()
    assert driver.find_element(By.TAG_NAME, "button").text == "Entrar"


# 2) Caminho feliz: login válido leva ao dashboard
def test_login_valido(driver):
    preencher_login(driver, EMAIL, SENHA)
    WebDriverWait(driver, 5).until(EC.url_contains("/dashboard"))
    assert "/dashboard" in driver.current_url


# 3) Login inválido: continua no /login
def test_login_invalido(driver):
    preencher_login(driver, "naoexiste@teste.com", "errada")
    WebDriverWait(driver, 5).until(EC.url_contains("/login"))
    assert "/login" in driver.current_url


# 4) Variações: campos vazios / email mal formatado -> validação HTML5 bloqueia o envio
@pytest.mark.parametrize("email,senha", [
    ("", ""),
    ("teste@teste.com", ""),
    ("", "123456"),
    ("email-sem-arroba", "123456"),
])
def test_validacao_campos(driver, email, senha):
    preencher_login(driver, email, senha)
    campo_email = driver.find_element(By.NAME, "email")
    campo_senha = driver.find_element(By.NAME, "password")
    invalido = driver.execute_script(
        "return !arguments[0].checkValidity() || !arguments[1].checkValidity();",
        campo_email, campo_senha)
    assert invalido
    assert "/login" in driver.current_url


# 5) Navegação: link "Cadastre-se aqui" existe e aponta para o cadastro
def test_link_cadastro(driver):
    driver.get(f"{BASE_URL}/login")
    link = driver.find_element(By.LINK_TEXT, "Cadastre-se aqui")
    pausa()
    assert "/register" in link.get_attribute("href")


# 6) Segurança/usabilidade: dashboard sem login redireciona para /login
def test_dashboard_sem_login(driver):
    driver.get(f"{BASE_URL}/dashboard")
    pausa()
    assert "/login" in driver.current_url
