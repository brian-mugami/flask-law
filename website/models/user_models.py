import uuid
from datetime import datetime
from time import time

from flask import request, url_for
from flask_login import UserMixin
from passlib.handlers.pbkdf2 import pbkdf2_sha256

from ..db import db
from ..libs.send_email import Mailgun

CONFIRMTIMEDELTA = 3600


class UserModel(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), nullable=False, unique=True, index=True)
    password = db.Column(db.String(200), nullable=False)
    phone_no = db.Column(db.String(200), nullable=False, unique=True)
    is_active = db.Column(db.Boolean, default=True)
    image = db.Column(db.String(200))
    is_archived = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    date_registered = db.Column(db.DateTime)
    date_archived = db.Column(db.DateTime)
    date_unarchived = db.Column(db.DateTime)
    update_date = db.Column(db.DateTime)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow())
    user_type = db.Column(
        db.Enum("admin", "super_admin", "advocate", "associate", "intern", "lawyer", "client", "secretary",
                name="user_type"),
        nullable=False)
    confirmation = db.relationship("ConfirmationModel", lazy="dynamic", back_populates="user",
                                   cascade="all, delete-orphan")
    clients = db.relationship("ClientModel", lazy="dynamic", back_populates="user")
    user_notes = db.relationship("CaseNoteModel", lazy="dynamic", back_populates="user")
    cases = db.relationship("CaseModel", lazy="dynamic", back_populates="user")
    case_details = db.relationship("CaseDetailModel", lazy="dynamic", back_populates="user")
    assigned_cases = db.relationship('CaseModel', secondary="case_attorneys", back_populates='attorneys')
    attachments = db.relationship("CaseAttachmentModel", back_populates="user", lazy="dynamic")

    def __repr__(self):
        return f"{self.user_type}- {self.first_name} {self.last_name}"

    @classmethod
    def find_by_id(cls, _id) -> "UserModel":
        return cls.query.get_or_404(_id)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def check_pwd(self, password):
        is_password_correct = pbkdf2_sha256.verify(password, self.password)
        return is_password_correct

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def update_db(self):
        self.update_date = datetime.utcnow()
        db.session.commit()

    @property
    def most_recent_confirmation(self) -> "ConfirmationModel":
        return self.confirmation.order_by(db.desc(ConfirmationModel.expire_at)).first()

    @classmethod
    def find_by_email(cls, email) -> "UserModel":
        return cls.query.filter_by(email=email).first()

    @classmethod
    def find_by_phone_no(cls, phone_no) -> "UserModel":
        return cls.query.filter_by(phone_no=phone_no).first()

    def send_email(self, ):
        subject = "Registration Confirmation"
        link = request.url_root[:-1] + url_for("auth_blp.confirmation",
                                               confirm_id=self.most_recent_confirmation.id)
        text = f"Click here to confirm your registration: {link}"
        html = f"<html> Please click the link to confirm your registration: <a href={link}> Link </a> </html>"

        Mailgun.send_email(self.email, subject, text, html)

    def send_pass_reset_email(self):
        subject = "Password Reset"
        link = request.url_root[:-1] + url_for("auth_blp.reset_pass", id=self.id)
        text = f"Click here to change your password: {link}"
        html = f"<html> Please click the link to change your password: <a href={link}> Link </a> </html>"

        Mailgun.send_email(self.email, subject, text, html)


class ConfirmationModel(db.Model):
    __tablename__ = "confirmations"
    id = db.Column(db.String(50), primary_key=True)
    expire_at = db.Column(db.Integer, nullable=False)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("UserModel", back_populates="confirmation")

    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.id = uuid.uuid4().hex
        self.expire_at = int(time()) + CONFIRMTIMEDELTA

    @classmethod
    def find_by_id(cls, _id: str) -> "ConfirmationModel":
        return cls.query.filter_by(id=_id).first()

    @property
    def expired(self) -> bool:
        return time() > self.expire_at

    def force_to_expire(self):
        if not self.expired:
            self.expire_at = int(time())
            self.save_to_db()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
