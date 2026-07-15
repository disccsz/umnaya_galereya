import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Enum, ForeignKey, Integer, String, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class PhotoStatuses(str, enum.Enum):
    uploading = 'uploading'
    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"



class Token(Base):
    __tablename__ = "tokens"


    data_token: Mapped[str] = mapped_column(String(255), primary_key=True)
    

    auth_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    vk_owner_user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    

    created_at_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

  
    photos = relationship("Photos", back_populates="owner_token_rel")


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    

    id_string: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    

    owner_data_token: Mapped[Optional[str]] = mapped_column(
        String(255), 
        ForeignKey("tokens.data_token"), 
        nullable=True, 
        index=True
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    is_identity_group: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
  
    standart_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    duplicate_photos = relationship("Photos", back_populates="duplicate_group_rel", foreign_keys="Photos.duplicate_group_id")
    identity_photos = relationship("Photos", back_populates="identity_group_rel", foreign_keys="Photos.identity_photo_group_id")


class Photos(Base):
    __tablename__ = "photos"


    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    id_string: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    
    object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    preview_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

  
    load_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    photo_size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    status: Mapped[PhotoStatuses] = mapped_column(Enum(PhotoStatuses, native_enum=True), default=PhotoStatuses.uploading, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_error_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_error_message: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)


    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    owner_data_token: Mapped[Optional[str]] = mapped_column(
        String(255), 
        ForeignKey("tokens.data_token"), 
        nullable=True,
        index=True
    )


    duplicate_group_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("groups.id"), 
        nullable=True,
        index=True
    )

    identity_photo_group_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("groups.id"), 
        nullable=True,
        index=True
    )

    
    owner_token_rel = relationship("Token", back_populates="photos", foreign_keys=[owner_data_token])
    duplicate_group_rel = relationship("Group", back_populates="duplicate_photos", foreign_keys=[duplicate_group_id])
    identity_group_rel = relationship("Group", back_populates="identity_photos", foreign_keys=[identity_photo_group_id])
    

    analysis = relationship("PhotoAnalysis", back_populates="photo", uselist=False, cascade="all, delete-orphan")


class PhotoAnalysis(Base):
    __tablename__ = "photo_analysis"


    photo_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("photos.id"), 
        primary_key=True
    )


    faces_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    eyes_closed_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    is_blurred: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    blur_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quality_metric: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    light_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Хэши для поиска
    perceptual_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    sha256_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # Время завершения анализа (ставится вручную кодом, не сервером)
    analysis_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Обратная связь
    photo = relationship("Photos", back_populates="analysis", uselist=False)