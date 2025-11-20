# 📁 CONFIG.PY - HƯỚNG DẪN CHI TIẾT
====================================

## 🎯 **TỔNG QUAN HỆ THỐNG CẤU HÌNH**

File `config.py` sử dụng **Pydantic Settings** để quản lý tất cả cấu hình ứng dụng một cách type-safe và validated.

### **🔄 Luồng Loading Configuration:**
```
.env file → Starlette Config → Pydantic Classes → Validation → Global Instance
```

---

## 📋 **1. APP METADATA SETTINGS**

```python
class AppSettings(BaseSettings):
    APP_NAME: str = "FastAPI app"           # Tên ứng dụng
    APP_DESCRIPTION: str | None = None      # Mô tả (OpenAPI)
    APP_VERSION: str | None = None          # Version (OpenAPI)
    LICENSE_NAME: str | None = None         # License info
    CONTACT_NAME: str | None = None         # Contact name
    CONTACT_EMAIL: str | None = None        # Contact email
```

**Sử dụng:** Hiển thị trong `/docs` và API metadata.

---

## 🔐 **2. AUTHENTICATION & SECURITY**

```python
class CryptSettings(BaseSettings):
    SECRET_KEY: SecretStr                    # JWT signing key (bắt buộc)
    ALGORITHM: str = "HS256"                # JWT algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30   # Access token: 30 phút
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7      # Refresh token: 7 ngày
```

**Security Notes:**
- `SecretStr` ẩn giá trị khi print/log
- Đổi `SECRET_KEY` trong production
- HS256 là symmetric encryption (dùng chung key)

---

## 🗃️ **3. DATABASE CONFIGURATIONS**

### **PostgreSQL (Recommended for Production):**
```python
class PostgresSettings(DatabaseSettings):
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres" 
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432              # PostgreSQL default port
    POSTGRES_DB: str = "postgres"
    
    # Auto-generated URI
    POSTGRES_URI: str = f"{user}:{pass}@{server}:{port}/{db}"
    POSTGRES_ASYNC_PREFIX: str = "postgresql+asyncpg://"
```

### **SQLite (Development/Testing):**
```python
class SQLiteSettings(DatabaseSettings):
    SQLITE_URI: str = "./sql_app.db"        # File path
    SQLITE_ASYNC_PREFIX: str = "sqlite+aiosqlite:///"
```

### **MySQL (Alternative):**
```python
class MySQLSettings(DatabaseSettings):
    MYSQL_PORT: int = 5432  # ⚠️ Note: MySQL default là 3306!
    # ... other MySQL settings
```

---

## 👤 **4. INITIAL ADMIN USER**

```python
class FirstUserSettings(BaseSettings):
    ADMIN_NAME: str = "admin"
    ADMIN_EMAIL: str = "admin@admin.com"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "!Ch4ng3Th1sP4ssW0rd!"  # ⚠️ ĐỔI NGAY!
```

**Tự động tạo superuser khi startup database.**

---

## 💾 **5. REDIS SERVICES**

### **Cache Redis:**
```python
class RedisCacheSettings(BaseSettings):
    REDIS_CACHE_HOST: str = "localhost"
    REDIS_CACHE_PORT: int = 6379
    REDIS_CACHE_URL: str = f"redis://{host}:{port}"
```

### **Queue Redis (Background Tasks):**
```python
class RedisQueueSettings(BaseSettings):
    REDIS_QUEUE_HOST: str = "localhost"
    REDIS_QUEUE_PORT: int = 6379
```

### **Rate Limiting Redis:**
```python
class RedisRateLimiterSettings(BaseSettings):
    REDIS_RATE_LIMIT_HOST: str = "localhost"
    REDIS_RATE_LIMIT_PORT: int = 6379
    REDIS_RATE_LIMIT_URL: str = f"redis://{host}:{port}"
```

**Note:** Có thể dùng cùng Redis instance cho tất cả services trong development.

---

## ⏱️ **6. RATE LIMITING**

```python
class DefaultRateLimitSettings(BaseSettings):
    DEFAULT_RATE_LIMIT_LIMIT: int = 10      # 10 requests
    DEFAULT_RATE_LIMIT_PERIOD: int = 3600   # per 3600 seconds (1 hour)
```

**Tier-based Rate Limiting:**
- Free: 10/hour
- Premium: 100/hour  
- Enterprise: 1000/hour

---

## 👨‍💼 **7. CRUD ADMIN INTERFACE**

```python
class CRUDAdminSettings(BaseSettings):
    CRUD_ADMIN_ENABLED: bool = True         # Bật/tắt admin
    CRUD_ADMIN_MOUNT_PATH: str = "/admin"   # URL path
    
    # Security
    CRUD_ADMIN_ALLOWED_IPS_LIST: list[str] | None = None
    CRUD_ADMIN_MAX_SESSIONS: int = 10
    CRUD_ADMIN_SESSION_TIMEOUT: int = 1440  # 24 hours
    
    # Redis integration (optional)
    CRUD_ADMIN_REDIS_ENABLED: bool = False
    # ... Redis settings
```

**Features:**
- Auto-generated admin panel
- IP whitelisting
- Session management
- Event tracking

---

## 🌍 **8. ENVIRONMENT MANAGEMENT**

```python
class EnvironmentOption(Enum):
    LOCAL = "local"          # Development
    STAGING = "staging"      # Testing
    PRODUCTION = "production" # Live

class EnvironmentSettings(BaseSettings):
    ENVIRONMENT: EnvironmentOption = EnvironmentOption.LOCAL
```

**Environment Behaviors:**
- **LOCAL:** Full API docs, debug mode
- **STAGING:** Docs chỉ cho superuser
- **PRODUCTION:** No docs, secure, optimized

---

## 🎭 **9. GLOBAL SETTINGS INSTANCE**

```python
class Settings(
    AppSettings,
    PostgresSettings,  # Primary DB
    CryptSettings,
    FirstUserSettings,
    RedisCacheSettings,
    # ... all other settings classes
):
    pass

settings = Settings()  # Global instance
```

**Multiple Inheritance:** Kết hợp tất cả settings thành 1 object.

---

## 📝 **10. ENVIRONMENT VARIABLES (.env)**

```bash
# App Info
APP_NAME="My FastAPI App"
APP_VERSION="1.0.0"
CONTACT_EMAIL="admin@example.com"

# Database
POSTGRES_USER="myuser"
POSTGRES_PASSWORD="mypassword"
POSTGRES_SERVER="localhost"
POSTGRES_DB="myapp"

# Security
SECRET_KEY="your-super-secret-key-here"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_CACHE_HOST="localhost"
REDIS_QUEUE_HOST="localhost"
REDIS_RATE_LIMIT_HOST="localhost"

# Admin
ADMIN_PASSWORD="ChangeThisPassword123!"

# Environment
ENVIRONMENT="local"
```

---

## 🔧 **11. SỬ DỤNG SETTINGS**

```python
from app.core.config import settings

# Access any setting
app_name = settings.APP_NAME
db_url = f"{settings.POSTGRES_ASYNC_PREFIX}{settings.POSTGRES_URI}"
is_prod = settings.ENVIRONMENT == EnvironmentOption.PRODUCTION

# Secret values
jwt_secret = settings.SECRET_KEY.get_secret_value()  # Unmask SecretStr
```

---

## ⚠️ **12. SECURITY BEST PRACTICES**

1. **Đổi SECRET_KEY** trong production
2. **Đổi ADMIN_PASSWORD** mặc định
3. **Sử dụng HTTPS** (SESSION_SECURE_COOKIES=True)
4. **IP whitelisting** cho admin interface
5. **Environment-specific secrets**
6. **Không commit .env** vào git

---

## 🔄 **13. CONFIGURATION LOADING ORDER**

1. **Environment Variables** (.env file)
2. **Class Defaults** (fallback values)
3. **Type Validation** (Pydantic)
4. **Secret Protection** (SecretStr)
5. **Global Instance** (settings object)

---

## 🎯 **SUMMARY**

Config system này cung cấp:
- ✅ **Type Safety:** Pydantic validation
- ✅ **Environment Management:** Multi-environment support  
- ✅ **Security:** Secret protection, validation
- ✅ **Flexibility:** Multiple database options
- ✅ **Scalability:** Redis clustering support
- ✅ **Developer Experience:** Auto-completion, documentation