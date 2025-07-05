import os
from typing import Optional

class Settings:
    # Database Configuration
    DATABASE_TYPE: str = os.getenv("DATABASE_TYPE", "sqlite")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./local_database.db")
    
    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    SESSION_TIMEOUT_HOURS: int = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
    
    # File Storage
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "./uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    
    # API Keys (for later phases)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    @classmethod
    def validate(cls):
        """Validate required settings"""
        if not cls.SECRET_KEY or cls.SECRET_KEY == "dev-secret-key-change-in-production":
            print("⚠️  Warning: Using default secret key. Change in production!")
        
        if not os.path.exists(cls.UPLOAD_FOLDER):
            os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
            print(f"✓ Created upload folder: {cls.UPLOAD_FOLDER}")

# Global settings instance
settings = Settings() 