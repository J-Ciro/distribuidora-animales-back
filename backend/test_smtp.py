"""
Test SMTP connection
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Leer configuración del .env
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "paulagutierrez0872@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "TU_CONTRASEÑA_DE_APLICACION_AQUI")

print(f"🔍 Testing SMTP Connection...")
print(f"Server: {SMTP_SERVER}:{SMTP_PORT}")
print(f"User: {SMTP_USER}")
print(f"Password: {'*' * len(SMTP_PASSWORD)}")
print()

try:
    # Test connection
    print("1. Connecting to SMTP server...")
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
    print("✅ Connected successfully")
    
    print("2. Starting TLS...")
    server.starttls()
    print("✅ TLS activated")
    
    print("3. Attempting login...")
    # Asegurar que las credenciales sean ASCII puro
    user = SMTP_USER.encode('ascii', 'ignore').decode('ascii')
    pwd = SMTP_PASSWORD.encode('ascii', 'ignore').decode('ascii')
    server.login(user, pwd)
    print("✅ Login successful!")
    
    print("4. Sending test email...")
    message = MIMEMultipart()
    message["From"] = SMTP_USER
    message["To"] = SMTP_USER  # Enviar a ti mismo
    message["Subject"] = "Test Email - Distribuidora Perros y Gatos"
    
    body = "<h1>Test Email</h1><p>Si ves este email, la configuración SMTP está correcta! ✅</p>"
    message.attach(MIMEText(body, "html"))
    
    server.send_message(message)
    print("✅ Test email sent successfully!")
    
    server.quit()
    print()
    print("🎉 All tests passed! SMTP is configured correctly.")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"❌ Authentication failed: {e}")
    print()
    print("⚠️  SOLUCIÓN:")
    print("1. Verifica que tienes 2FA habilitado en Gmail")
    print("2. Genera una contraseña de aplicación en:")
    print("   https://myaccount.google.com/apppasswords")
    print("3. Actualiza SMTP_PASSWORD en backend/api/.env")
    print("4. Reinicia el contenedor: docker-compose restart api")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Type: {type(e).__name__}")
