from datetime import datetime

from ..db import db


class ClientModel(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    middle_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), unique=True, index=True)
    phone_no = db.Column(db.String(80), nullable=False, unique=True, index=True)
    address = db.Column(db.String(200), nullable=False)
    identification_no = db.Column(db.String(200), nullable=False, unique=True)
    is_active = db.Column(db.Boolean, default=True)
    is_archived = db.Column(db.Boolean, default=False)
    client_date = db.Column(db.DateTime)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("UserModel", back_populates="clients")

    cases = db.relationship("CaseModel", back_populates="client", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"{self.first_name} {self.middle_name} {self.last_name}"

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def update_db(self):
        self.last_updated = datetime.utcnow()
        db.session.commit()

    @classmethod
    def find_by_id(cls, client_id):
        """Find a client by their ID."""
        return cls.query.filter_by(id=client_id).first()

    @classmethod
    def find_by_email(cls, email):
        """Find a client by their email address."""
        return cls.query.filter_by(email=email).first()

    @classmethod
    def find_by_phone(cls, phone_no):
        """Find a client by their phone number."""
        return cls.query.filter_by(phone_no=phone_no).first()

    @classmethod
    def find_by_identification(cls, identification_no):
        """Find a client by their identification number."""
        return cls.query.filter_by(identification_no=identification_no).first()
