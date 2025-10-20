import redis
from app.core.env import settings


class RedisClient:
    """
    Redis 클라이언트 싱글톤 클래스
    - 환경변수 캐싱 전용
    - 연결 풀 관리
    """

    _instance: redis.Redis | None = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        """
        Redis 클라이언트 인스턴스 반환 (싱글톤)
        """
        if cls._instance is None:
            redis_config = {
                "host": settings.REDIS_HOST if hasattr(settings, 'REDIS_HOST') else 'redis',
                "port": settings.REDIS_PORT,
                "db": 0,  # 환경변수 전용 DB
                "decode_responses": True,  # 문자열 자동 디코딩
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
                "retry_on_timeout": True,
                "health_check_interval": 30
            }

            # Redis 비밀번호가 설정되어 있으면 추가
            if hasattr(settings, 'REDIS_PASSWORD') and settings.REDIS_PASSWORD:
                redis_config["password"] = settings.REDIS_PASSWORD

            cls._instance = redis.Redis(**redis_config)
            print("✓ Redis 클라이언트 연결 성공")
        return cls._instance

    @classmethod
    def close(cls):
        """
        Redis 연결 종료
        """
        if cls._instance is not None:
            cls._instance.close()
            cls._instance = None
            print("✓ Redis 클라이언트 연결 종료")

    @classmethod
    def test_connection(cls) -> bool:
        """
        Redis 연결 테스트
        """
        try:
            client = cls.get_client()
            client.ping()
            print("✓ Redis 연결 테스트 성공")
            return True
        except Exception as e:
            print(f"✗ Redis 연결 테스트 실패: {e}")
            return False


# 전역 Redis 클라이언트 인스턴스 반환 함수
def get_redis_client() -> redis.Redis:
    """
    FastAPI 의존성 주입을 위한 Redis 클라이언트 반환 함수
    """
    return RedisClient.get_client()
