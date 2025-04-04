# services/base.py
from sqlmodel import Session, select, SQLModel
from typing import TypeVar, Generic, Type, List, Optional
from utils import db_operation_handler

T = TypeVar('T', bound=SQLModel)

class BaseService(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model
    
    @db_operation_handler
    async def get_by_id(self, db: Session, id: str) -> Optional[T]:
        """Get a record by ID"""
        return db.exec(select(self.model).where(self.model.id == id)).first()
    
    @db_operation_handler
    async def get_all(self, db: Session) -> List[T]:
        """Get all records"""
        return db.exec(select(self.model)).all()
    
    @db_operation_handler
    async def create(self, db: Session, obj_in: SQLModel) -> T:
        """Create a new record"""
        db_obj = self.model.from_orm(obj_in) if not isinstance(obj_in, self.model) else obj_in
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    @db_operation_handler
    async def update(self, db: Session, id: str, obj_in: SQLModel) -> Optional[T]:
        """Update a record"""
        db_obj = await self.get_by_id(db, id)
        if not db_obj:
            return None
            
        obj_data = obj_in.dict(exclude_unset=True)
        for key, value in obj_data.items():
            setattr(db_obj, key, value)
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    @db_operation_handler
    async def delete(self, db: Session, id: str) -> bool:
        """Delete a record by ID"""
        db_obj = await self.get_by_id(db, id)
        if db_obj:
            db.delete(db_obj)
            db.commit()
            return True
        return False