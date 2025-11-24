from app.database import SessionLocal
import app.models as models


def main():
    db = SessionLocal()
    email = 'test@example.com'
    user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not user:
        user = models.Usuario(email=email, password_hash='x', nombre_completo='Test User')
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f'CREATED_USER {user.id}')
    else:
        print(f'EXISTING_USER {user.id}')

    pedido = models.Pedido(usuario_id=user.id, estado='Pendiente', total=50.0, direccion_entrega='Calle 2', telefono_contacto='0987654321', nota_especial='Prueba')
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    print(f'CREATED_PEDIDO {pedido.id}')


if __name__ == '__main__':
    main()
