from uuid import UUID

from app.core.redis import redis_client
from app.ai.insight.schema import AIInsights


class InsightCacheService:

    TTL = 60 * 60 * 6  # 6 hours

    @staticmethod
    def _key(user_id: UUID) -> str:
        return f"dashboard:insights:{user_id}"

    @classmethod
    def get(
        cls,
        user_id: UUID,
    ) -> AIInsights | None:

        cached = redis_client.get(cls._key(user_id))

        if cached is None:
            return None

        return AIInsights.model_validate_json(cached)

    @classmethod
    def set(
        cls,
        user_id: UUID,
        insights: AIInsights,
    ) -> None:

        redis_client.setex(
            cls._key(user_id),
            cls.TTL,
            insights.model_dump_json(),
        )

    @classmethod
    def invalidate(
        cls,
        user_id: UUID,
    ) -> None:

        redis_client.delete(cls._key(user_id))
