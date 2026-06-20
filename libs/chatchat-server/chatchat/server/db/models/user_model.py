from sqlalchemy import Boolean, Column, DateTime, String, func

from chatchat.server.db.base import Base


class UserModel(Base):
    __tablename__ = "user"

    id = Column(String(32), primary_key=True, comment="用户ID")
    username = Column(String(100), unique=True, nullable=False, comment="用户名")
    hashed_password = Column(String(255), nullable=False, comment="密码哈希")
    email = Column(String(255), comment="邮箱")
    full_name = Column(String(100), comment="姓名")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否超级管理员")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}', is_active={self.is_active})>"
