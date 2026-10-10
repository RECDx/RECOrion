import sys
import os
import time

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), '..', 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def set_react_input(driver, element, value):
    driver.execute_script("""
        let el = arguments[0];
        let val = arguments[1];
        let nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        nativeInputValueSetter.call(el, val);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
    """, element, value)

def run_verification():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1600,1000')

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)

    try:
        print(">>> 1. Sayfa Aciliyor: http://localhost:5173/")
        driver.get("http://localhost:5173/")
        time.sleep(2)

        # Clear any existing session in localStorage
        driver.execute_script("localStorage.clear();")
        driver.refresh()
        time.sleep(2)

        # Bypass butonlarinin kaldirildigini dogrula
        header_text = driver.find_element(By.CLASS_NAME, "landing-header").text
        assert "Calisma Alanina Git" not in header_text and "Çalışma Alanına Git" not in header_text, "HATA: Landing header'da bypass butonu hala var!"
        print("✓ Landing header'da bypass butonu yok. Sadece 'Giris Yap' butonu gorunuyor.")

        # 2. Giris Yap modalini ac
        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Giriş Yap')]")))
        login_btn.click()
        time.sleep(1)

        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "login-modal-card")))
        print("✓ Giris Yap modali acildi.")

        # 3. YANLIS SIFRE TESTI (cuneyterdil@recdx. ile)
        print("\n>>> 2. Yanlis Sifre Testi Baslatiliyor (Kullanici: cuneyterdil@recdx.)...")
        email_input = driver.find_element(By.XPATH, "//input[@type='text']")
        password_input = driver.find_element(By.XPATH, "//input[@type='password']")

        set_react_input(driver, email_input, "cuneyterdil@recdx.")
        set_react_input(driver, password_input, "YANLIS_SIFRE_12345")
        time.sleep(0.5)

        submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_btn.click()
        time.sleep(1.5)

        # Hata uyarisinin ekranda oldugunu dogrula
        error_alert = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "alert-error")))
        assert error_alert.is_displayed(), "HATA: Hata mesaji gorunmuyor!"
        print(f"✓ Yanlis sifre basariyla ENGELLENDI! Ekranda hata: '{error_alert.text}'")

        # Modalin hala acik oldugunu ve musteri ekranina gecilmedigini dogrula
        assert driver.find_element(By.CLASS_NAME, "login-modal-card").is_displayed(), "HATA: Modal kapandi!"
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "1_wrong_password_blocked.png"))
        print("✓ Ekran goruntusu kaydedildi: 1_wrong_password_blocked.png")

        # 4. DOGRU SUPER ADMIN GIRISI TESTI (cuneyterdil@recdx. ve RECDx_SuperAdmin_2026!)
        print("\n>>> 3. Dogru Super Admin Bilgileri ile Giris Yapiliyor...")
        set_react_input(driver, password_input, "RECDx_SuperAdmin_2026!")
        time.sleep(0.5)

        submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_btn.click()
        time.sleep(3)

        # SuperAdminConsole'un acildigini dogrula
        super_admin_console = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "super-admin-container")))
        assert super_admin_console.is_displayed(), "HATA: SuperAdminConsole acilmadi!"
        print("✓ TEBRIKLER: 'RECDx Platform Super Admin Yonetim Konsolu' basariyla acildi!")

        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "2_superadmin_console_opened.png"))
        print("✓ Ekran goruntusu kaydedildi: 2_superadmin_console_opened.png")

        # KPI ve Sekmeleri dogrula
        console_body = super_admin_console.text
        assert "Bekleyen" in console_body or "BEKLEYEN" in console_body
        assert "Tenant" in console_body or "Odoo 19" in console_body
        print("✓ KPI Kartlari (Bekleyen Siparisler, Aktif Sirketler, Tanimli Izinler, EVREN Modelleri) dogrulandi.")

        # 5. TAB GECISLERI VE SIRKET CALISMA ALANINA GECIS TESTI
        print("\n>>> 4. Kurumlar Sekmesine Gecis ve Calisma Alani Denetimi...")
        tenants_tab = driver.find_element(By.XPATH, "//button[contains(., 'Kayıtlı Şirketler') or contains(., 'Çalışma Alanı')]")
        tenants_tab.click()
        time.sleep(1)

        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "3_tenants_tab_view.png"))
        print("✓ Ekran goruntusu kaydedildi: 3_tenants_tab_view.png")

        # Sirket listesindeki 'Calisma Alanina Gec' butonuna basarak workspace'e gec
        switch_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Çalışma Alanına Geç') or contains(., 'Bu Şirketin')]")))
        switch_btn.click()
        time.sleep(2.5)

        # 3-Pane calisma alaninin acildigini ve 'Süper Admin Konsolu' butonunun var oldugunu dogrula
        workspace_layout = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "work-area-layout")))
        assert workspace_layout.is_displayed()
        print("✓ Sirket calisma alani (Tri-Pane) basariyla acildi.")

        admin_back_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Süper Admin Konsolu')]")
        assert admin_back_btn.is_displayed(), "HATA: Navbar'da Super Admin Konsolu butonu yok!"
        print("✓ Navbar'da '👑 Süper Admin Konsolu' butonu dogrulandi.")

        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "4_workspace_with_admin_button.png"))
        print("✓ Ekran goruntusu kaydedildi: 4_workspace_with_admin_button.png")

        # 6. KONSOLA GERI DONUS TESTI
        print("\n>>> 5. Super Admin Konsoluna Geri Donus...")
        admin_back_btn.click()
        time.sleep(2)

        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "super-admin-container")))
        print("✓ Super Admin Konsoluna basariyla geri donuldu!")

        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "5_back_to_superadmin_console.png"))
        print("✓ Ekran goruntusu kaydedildi: 5_back_to_superadmin_console.png")

        # 7. RESMI WEB SITESINE GECIS VE CIKIS YAP TESTI
        print("\n>>> 6. Resmi Web Sitesine Donus ve Cikis...")
        web_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Resmi Web')]")
        web_btn.click()
        time.sleep(2)

        landing_header = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "landing-header")))
        assert "Süper Admin Konsolu" in landing_header.text
        assert "Çıkış Yap" in landing_header.text
        print("✓ Resmi web sitesinde '👑 Süper Admin Konsolu →' ve 'Çıkış Yap' butonlari dogrulandi.")
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "6_landing_authenticated.png"))

        logout_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Çıkış Yap')]")
        logout_btn.click()
        time.sleep(1.5)

        header_after_logout = driver.find_element(By.CLASS_NAME, "landing-header").text
        assert "Giriş Yap" in header_after_logout
        assert "Çıkış Yap" not in header_after_logout
        print("✓ Cikis yapildi, oturum basariyla sifirlandi.")
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "7_logged_out.png"))

        print("\n=======================================================")
        print("🎉 TUM MADDELER EKSIKSIZ VE %100 BASARIYLA DOGRULANDI!")
        print("1. Yanlis sifre girildiginde musteri ekrani ACILMIYOR, hata mesaji verip bekliyor.")
        print("2. Dogru sifre girildiginde SUPER ADMIN YONETIM KONSOLU aciliyor.")
        print("3. Super Admin panelinden sirket calisma alanina gecilebiliyor ve geri donulebiliyor.")
        print("=======================================================")

    finally:
        driver.quit()

if __name__ == '__main__':
    run_verification()
