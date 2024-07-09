from datetime import datetime

from ..db import db


class CaseModel(db.Model):
    __tablename__ = "cases"

    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(80), unique=True, nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum("open", "closed", "pending", name="status_type"), default="open", nullable=False)
    case_type = db.Column(
        db.Enum('Criminal', 'Civil', 'Commercial', 'Administrative', 'Bankruptcy', 'Environmental', 'Human Rights',
                'Immigration', 'Consumer Protection', 'Tax', 'Military', name='case_types'), nullable=False)
    case_description = db.Column(db.Text, nullable=True)
    filed_date = db.Column(db.Date, nullable=False)
    court_date = db.Column(db.Date, nullable=True)
    resolution_date = db.Column(db.Date, nullable=True)
    resolution = db.Column(db.String(200), nullable=True)
    priority = db.Column(db.Enum("high", "medium", "low", name="priority_type"), default="medium", nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    user = db.relationship("UserModel", back_populates="cases")
    client = db.relationship("ClientModel", back_populates="cases")
    case_notes = db.relationship("CaseNoteModel", back_populates="case", lazy="dynamic", cascade="all, delete-orphan")
    case_details = db.relationship("CaseDetailModel", back_populates="case", cascade="all, delete-orphan")
    attorneys = db.relationship('UserModel', secondary="case_attorneys", back_populates='assigned_cases')
    attachments = db.relationship("CaseAttachmentModel", back_populates="case", lazy="dynamic",
                                  cascade="all, delete-orphan")

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
    def find_by_id(cls, id):
        return cls.query.get(id)

    @classmethod
    def find_by_case_number(cls, case_number):
        return cls.query.filter_by(case_number=case_number).first()


class CaseDetailModel(db.Model):
    __tablename__ = "case_details"
    id = db.Column(db.Integer, primary_key=True)
    judge_name = db.Column(db.String(120), nullable=False)
    court_type = db.Column(
        db.Enum('supreme court of kenya', 'court of appeal', 'high court', 'employment and labour relations court',
                'environment and land court', 'magistrates court', 'kadhi\'s court',
                'courts martial', 'tribunal', name='court_types'), nullable=False)
    court_location = db.Column(db.String(200), nullable=True)
    court_description = db.Column(db.String(200), nullable=True)
    case_hearing_date = db.Column(db.Date, nullable=True)
    case_judgment = db.Column(db.Text, nullable=True)
    case_outcome = db.Column(db.String(120), nullable=True)
    assigned_prosecutor = db.Column(db.String(120), nullable=True)
    evidence_details = db.Column(db.Text, nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    case = db.relationship("CaseModel", back_populates="case_details")
    user = db.relationship("UserModel", back_populates="case_details")

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
    def find_by_id(cls, id):
        return cls.query.get(id)

    @classmethod
    def find_by_case_id(cls, id):
        return cls.query.filter_by(case_id=id).first()


class CaseNoteModel(db.Model):
    __tablename__ = "case_notes"

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    note = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)
    reference_date = db.Column(db.DateTime)
    case = db.relationship("CaseModel", back_populates="case_notes")
    user = db.relationship("UserModel", back_populates="user_notes")

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
    def find_by_case_id(cls, id):
        return cls.query.filter_by(case_id=id).order_by(cls.reference_date.desc())

    @classmethod
    def find_by_id(cls, id):
        return cls.query.get(id)


class CaseAttachmentModel(db.Model):
    __tablename__ = "case_attachments"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    attachment_filename = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    file_url = db.Column(db.String(200), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    last_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)
    case = db.relationship("CaseModel", back_populates="attachments")
    user = db.relationship("UserModel", back_populates="attachments")

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
    def find_by_case_id(cls, id):
        return cls.query.filter_by(case_id=id).order_by(cls.uploaded_at.desc())

    @classmethod
    def find_by_id(cls, id):
        return cls.query.get(id)


class CaseAttorneyModel(db.Model):
    __tablename__ = "case_attorneys"

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('case_id', 'user_id', ),
    )

    @classmethod
    def find_by_ids(cls, user_id, case_id):
        return cls.query.filter_by(user_id=user_id, case_id=case_id).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
