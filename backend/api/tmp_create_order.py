from app.database import SessionLocal
import app.models as models
from sqlalchemy.exc import IntegrityError

db = SessionLocal()
# create test user if not exists
u = db.query(models.Usuario).filter(models.Usuario.email == 'test@example.com').first()
if not u:
    try:
        u = models.Usuario(email='test@example.com', password_hash='x', nombre_completo='Test User')
        db.add(u)
        db.commit()
        print('created user', u.id)
    except IntegrityError:
        db.rollback()
        u = db.query(models.Usuario).filter(models.Usuario.email == 'test@example.com').first()
        print('existing user after race', getattr(u,'id',None))
else:
    print('existing user', u.id)

# create a pedido
p = models.Pedido(usuario_id=u.id, estado='Pendiente', total=50.0, direccion_entrega='Calle 2', telefono_contacto='0987654321', nota_especial='Prueba')
try:
    db.add(p)
    db.commit()
    print('CREATED_PEDIDO', p.id)
except Exception as e:
    db.rollback()
    print('ERROR_CREATING_PEDIDO', e)
