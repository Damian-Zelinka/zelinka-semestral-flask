from models import Role, db
from config import app

def create_roles():
    roles = [
        {'name': 'administrator', 'description': 'Superuser with full access'},
        {'name': 'moderator', 'description': 'Can edit events and moderate registrations'},
        {'name': 'user', 'description': 'Regular user who can view and register for events'}
    ]
    
    for role_data in roles:
        existing_role = Role.query.filter_by(name=role_data['name']).first()
        if not existing_role:
            role = Role(name=role_data['name'], description=role_data['description'])
            db.session.add(role)
    
    db.session.commit()

if __name__ == "__main__":
    with app.app_context():
        create_roles()
        print("Roles created successfully.")
