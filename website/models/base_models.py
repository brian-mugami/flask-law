from datetime import datetime

from ..db import db


class RoleModel(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    update_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)

    @classmethod
    def find_by_name(cls, name):
        return cls.query.filter_by(name=name).first()

    @classmethod
    def find_by_id(cls, id):
        return cls.query.get(id)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def update_db(self):
        self.update_date = datetime.utcnow()
        db.session.commit()

    def make_active(self):
        self.is_active = True
        self.update_db()

    def make_inactive(self):
        self.is_active = False
        self.update_db()
