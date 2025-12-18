import smtplib
import sys

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "paulagutierrez0872@gmail.com"
SMTP_PASSWORD = "smzqxhigmjateeoy"

print("Testing Gmail SMTP...")
print(f"Email: {SMTP_USER}")
print(f"Password length: {len(SMTP_PASSWORD)}")
print()

try:
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
    server.set_debuglevel(1)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)
    print("\n✅ Login successful!")
    server.quit()
except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ Authentication Error: {e}")
    print("\nPOSIBLES CAUSAS:")
    print("1. Verificación en 2 pasos NO activada")
    print("2. Contraseña incorrecta")
    print("3. Email incorrecto")
except Exception as e:
    print(f"\n❌ Error: {e}")
