// Script de prueba para verificar la configuración de email
require('dotenv').config();

const nodemailer = require('nodemailer');

console.log('=== Configuración de Email ===');
console.log('SMTP_HOST:', process.env.SMTP_HOST);
console.log('SMTP_PORT:', process.env.SMTP_PORT);
console.log('SMTP_USER:', process.env.SMTP_USER);
console.log('SMTP_PASS:', process.env.SMTP_PASS ? '***configurada***' : 'NO CONFIGURADA');
console.log('EMAIL_FROM_NAME:', process.env.EMAIL_FROM_NAME);
console.log('EMAIL_FROM_ADDRESS:', process.env.EMAIL_FROM_ADDRESS);
console.log('From completo:', `${process.env.EMAIL_FROM_NAME} <${process.env.EMAIL_FROM_ADDRESS}>`);
console.log('================================\n');

// Crear transporter de prueba
const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST,
  port: parseInt(process.env.SMTP_PORT),
  secure: false,
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS,
  },
});

// Verificar conexión
transporter.verify((error, success) => {
  if (error) {
    console.error('❌ Error de conexión SMTP:', error);
  } else {
    console.log('✅ Servidor SMTP listo para enviar emails');
    
    // Enviar email de prueba
    const mailOptions = {
      from: `${process.env.EMAIL_FROM_NAME} <${process.env.EMAIL_FROM_ADDRESS}>`,
      to: process.env.SMTP_USER, // Enviar al mismo correo
      subject: 'Prueba de configuración - Soft PetPlace',
      html: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #4F46E5;">¡Configuración Correcta!</h2>
          <p>Este es un email de prueba desde <strong>${process.env.EMAIL_FROM_ADDRESS}</strong></p>
          <p>Si recibes este email, la configuración está funcionando correctamente.</p>
          <hr>
          <small>Enviado desde el worker de Soft PetPlace</small>
        </div>
      `,
    };
    
    transporter.sendMail(mailOptions, (err, info) => {
      if (err) {
        console.error('❌ Error al enviar email:', err);
      } else {
        console.log('✅ Email de prueba enviado exitosamente');
        console.log('Message ID:', info.messageId);
        console.log('Revisa la bandeja de entrada de:', process.env.EMAIL_FROM_ADDRESS);
      }
      process.exit(0);
    });
  }
});
