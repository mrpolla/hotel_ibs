from backend.app import db

class Chain(db.Model):
    __tablename__ = 'chains'
    
    chain_id = db.Column(db.Integer, primary_key=True, nullable=False)
    chain_name = db.Column(db.Text)
    
    hotels = db.relationship("Hotel", back_populates="chain")

class Hotel(db.Model):
    __tablename__ = 'hotels'
    
    hotel_id = db.Column(db.Integer, primary_key=True, nullable=False)
    hotel_name = db.Column(db.Text)
    chain_id = db.Column(db.Integer, db.ForeignKey('chains.chain_id'))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    chain = db.relationship("Chain", back_populates="hotels")
    images = db.relationship("Image", back_populates="hotel")

class Image(db.Model):
    __tablename__ = 'images'
    
    image_id = db.Column(db.Text, primary_key=True, nullable=False)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotels.hotel_id'))
    image_url = db.Column(db.Text)
    
    hotel = db.relationship("Hotel", back_populates="images")
    tags = db.relationship("ImageTag", back_populates="image")

    def __repr__(self):
        return f'<Image {self.image_url}>'

class ImageTag(db.Model):
    __tablename__ = 'image_tags'
    
    image_id = db.Column(db.Integer, db.ForeignKey('images.image_id'), primary_key=True, nullable=False)
    tag_name = db.Column(db.Text, primary_key=True, nullable=False)
    confidence_score = db.Column(db.Float)
    
    image = db.relationship("Image", back_populates="tags")
