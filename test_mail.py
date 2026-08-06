# test_mail.py
"""
Teste simples para envio SMTP (Brevo). Edite o destinatário e rode:
    py test_mail.py
"""
import os
from app import create_app, mail
from flask_mail import Message

def send_test_email(to_address: str):
    app = create_app()
    with app.app_context():
        msg = Message(
            subject="Teste de envio - Sabor Express",
            recipients=[to_address],
            body="Olá — este é um teste de envio real via Brevo SMTP.",
            sender=app.config.get('en')
        )
        try:
            mail.send(msg)
            print("✅ E-mail enviado — verifique a caixa de entrada do destinatário.")
        except Exception as e:
            print("❌ Erro ao enviar e-mail:", e)

if __name__ == "__main__":
    # Altere para o e-mail que quer testar
    send_test_email("ensj2017@gmail.com")
