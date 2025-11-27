"""
PopPins II - 데이터베이스 설정 모듈

이 모듈은 SQLAlchemy를 사용한 데이터베이스 연결 및 세션 관리를 담당합니다.

주요 기능:
- SQLite 데이터베이스 연결 설정
- SQLAlchemy Base 클래스 정의 (모델 상속용)
- 데이터베이스 세션 생성 및 관리

데이터베이스:
- SQLite 사용 (파일 기반, 개발/소규모 프로덕션용)
- 파일 위치: ./history.db (프로젝트 루트)
- 프로덕션 환경에서는 PostgreSQL 등으로 변경 권장

작성자: PopPins II 개발팀
버전: 1.0.0
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ============================================================================
# 데이터베이스 연결 설정
# ============================================================================
# SQLite 데이터베이스 URL
# 형식: sqlite:///./파일경로
# ./history.db는 프로젝트 루트 디렉토리에 생성됨
SQLALCHEMY_DATABASE_URL = "sqlite:///./history.db"

# SQLAlchemy 엔진 생성
# check_same_thread=False: FastAPI의 비동기 특성상 여러 스레드에서
# 같은 연결을 사용할 수 있도록 설정 (SQLite 기본값은 True)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# ============================================================================
# 세션 팩토리 생성
# ============================================================================
# autocommit=False: 자동 커밋 비활성화 (명시적 commit() 필요)
# autoflush=False: 자동 플러시 비활성화 (성능 최적화)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ============================================================================
# Base 클래스
# ============================================================================
# 모든 SQLAlchemy 모델이 상속받을 Base 클래스
# 이 클래스를 상속하면 자동으로 테이블 매핑이 생성됨
Base = declarative_base()

# ============================================================================
# 데이터베이스 세션 의존성 함수
# ============================================================================
def get_db():
    """
    FastAPI 의존성 주입을 위한 데이터베이스 세션 생성 함수.
    
    FastAPI의 Depends()와 함께 사용되어 각 요청마다 새로운 DB 세션을 생성하고
    요청 종료 시 자동으로 세션을 닫습니다.
    
    Yields:
        Session: SQLAlchemy 데이터베이스 세션
    
    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            # db를 사용하여 데이터베이스 쿼리 수행
            items = db.query(Item).all()
            return items
        # 함수 종료 시 자동으로 db.close() 호출됨
    
    Note:
        - yield를 사용하는 이유: FastAPI가 요청 종료 시 finally 블록을 실행하기 위함
        - 세션을 닫지 않으면 메모리 누수 및 연결 풀 고갈 가능
    """
    db = SessionLocal()
    try:
        yield db  # 요청 처리 중 세션 사용
    finally:
        db.close()  # 요청 종료 시 세션 닫기 (리소스 정리)
