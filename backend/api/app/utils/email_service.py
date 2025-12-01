"""
Email service for sending verification codes and notifications
Uses SMTP with secure connection
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Servicio para envío de emails con configuración SMTP"""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
    
    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Envía un email usando SMTP
        
        Args:
            to_email: Email del destinatario
            subject: Asunto del email
            html_content: Contenido HTML del email
            
        Returns:
            bool: True si se envió exitosamente, False en caso contrario
        """
        try:
            # Crear mensaje
            message = MIMEMultipart("alternative")
            message["From"] = self.smtp_user
            message["To"] = to_email
            message["Subject"] = subject
            
            # Agregar contenido HTML
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Conectar y enviar
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Activar encriptación TLS
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)
            
            logger.info(f"Email enviado exitosamente a {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email a {to_email}: {str(e)}")
            return False
    
    def send_verification_code(self, to_email: str, code: str) -> bool:
        """
        Envía el código de verificación al email del usuario
        
        Args:
            to_email: Email del usuario
            code: Código de verificación de 6 dígitos
            
        Returns:
            bool: True si se envió exitosamente
        """
        subject = "Código de Verificación - Distribuidora Perros y Gatos"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background-color: #ffffff;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 30px;
                    text-align: center;
                    color: white;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .content {{
                    padding: 40px 30px;
                    text-align: center;
                }}
                .code-container {{
                    background-color: #f8f9fa;
                    border: 2px dashed #667eea;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 30px 0;
                }}
                .verification-code {{
                    font-size: 36px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    color: #667eea;
                    margin: 0;
                    font-family: 'Courier New', monospace;
                }}
                .message {{
                    color: #555;
                    line-height: 1.6;
                    margin: 20px 0;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                    text-align: left;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                }}
                .footer a {{
                    color: #667eea;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🐕 Distribuidora Perros y Gatos 🐈</h1>
                </div>
                <div class="content">
                    <h2>¡Bienvenido!</h2>
                    <p class="message">
                        Gracias por registrarte en nuestra tienda. Para completar tu registro,
                        por favor verifica tu correo electrónico usando el siguiente código:
                    </p>
                    
                    <div class="code-container">
                        <p class="verification-code">{code}</p>
                    </div>
                    
                    <p class="message">
                        Este código es válido por <strong>10 minutos</strong>.
                    </p>
                    
                    <div class="warning">
                        <strong>⚠️ Importante:</strong><br>
                        • No compartas este código con nadie<br>
                        • Si no solicitaste este código, ignora este mensaje<br>
                        • El código solo funciona una vez
                    </div>
                </div>
                <div class="footer">
                    <p>
                        Este es un mensaje automático, por favor no respondas a este correo.<br>
                        © 2025 Distribuidora Perros y Gatos - Todos los derechos reservados
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(to_email, subject, html_content)
    
    def send_welcome_email(self, to_email: str, nombre: str) -> bool:
        """
        Envía email de bienvenida después de verificación exitosa
        
        Args:
            to_email: Email del usuario
            nombre: Nombre del usuario
            
        Returns:
            bool: True si se envió exitosamente
        """
        subject = "¡Bienvenido a Distribuidora Perros y Gatos!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 40px auto; background-color: #ffffff; 
                             border-radius: 10px; padding: 40px; }}
                .header {{ text-align: center; color: #667eea; }}
                .content {{ text-align: center; padding: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 ¡Bienvenido, {nombre}!</h1>
                </div>
                <div class="content">
                    <p>Tu cuenta ha sido verificada exitosamente.</p>
                    <p>Ya puedes disfrutar de todos nuestros productos para tus mascotas.</p>
                    <p><strong>¡Gracias por confiar en nosotros!</strong></p>
                </div>
                <div class="footer">
                    <p>© 2025 Distribuidora Perros y Gatos</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(to_email, subject, html_content)


# Instancia global del servicio
email_service = EmailService()
