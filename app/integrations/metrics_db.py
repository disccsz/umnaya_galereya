import logging

from sqlalchemy import select, func, text

from app.database.models import PhotoStatuses, Photos

logger = logging.getLogger(__name__)


async def get_db_metrics_text(session) -> str:
    total = (await session.execute(
        select(func.count(Photos.id))
    )).scalar()

    done = (await session.execute(
        select(func.count(Photos.id)).where(Photos.status == PhotoStatuses.done)
    )).scalar()

    failed = (await session.execute(
        select(func.count(Photos.id)).where(Photos.status == PhotoStatuses.failed)
    )).scalar()

    pending = (await session.execute(
        select(func.count(Photos.id)).where(Photos.status == PhotoStatuses.pending)
    )).scalar()

    processing = (await session.execute(
        select(func.count(Photos.id)).where(Photos.status == PhotoStatuses.processing)
    )).scalar()

    sum_attempts = (await session.execute(
        select(func.coalesce(func.sum(Photos.attempts), 0))
        .where(Photos.status.in_([PhotoStatuses.done, PhotoStatuses.failed]))
    )).scalar()
    count_attempted = done + failed

    dur_rows = await session.execute(
        text("""
            SELECT
                COUNT(*) FILTER (WHERE EXTRACT(EPOCH FROM (pa.analysis_at - p.load_time)) <= 1)    AS le_1,
                COUNT(*) FILTER (WHERE EXTRACT(EPOCH FROM (pa.analysis_at - p.load_time)) <= 5)    AS le_5,
                COUNT(*) FILTER (WHERE EXTRACT(EPOCH FROM (pa.analysis_at - p.load_time)) <= 10)   AS le_10,
                COUNT(*) FILTER (WHERE EXTRACT(EPOCH FROM (pa.analysis_at - p.load_time)) <= 30)   AS le_30,
                COUNT(*) FILTER (WHERE EXTRACT(EPOCH FROM (pa.analysis_at - p.load_time)) <= 60)   AS le_60,
                COUNT(*) FILTER (WHERE EXTRACT(EPOCH FROM (pa.analysis_at - p.load_time)) <= 120)  AS le_120,
                COUNT(*)                                                                           AS tot,
                COALESCE(SUM(EXTRACT(EPOCH FROM (pa.analysis_at - p.load_time))), 0)               AS total_dur
            FROM photos p
            JOIN photo_analysis pa ON pa.photo_id = p.id
            WHERE p.status = 'done'
        """),
    )
    d = dur_rows.one()

    lines = [
        "# HELP photos_uploaded_total Total photos uploaded",
        "# TYPE photos_uploaded_total counter",
        f"photos_uploaded_total {total}",
        "",
        "# HELP photo_analysis_completed_total Analysis completed by status",
        "# TYPE photo_analysis_completed_total counter",
        f'photo_analysis_completed_total{{status="done"}} {done}',
        f'photo_analysis_completed_total{{status="failed"}} {failed}',
        "",
        "# HELP photo_analysis_failed_total Analysis permanently failed",
        "# TYPE photo_analysis_failed_total counter",
        f"photo_analysis_failed_total {failed}",
        "",
        "# HELP photo_analysis_duration_seconds Analysis duration",
        "# TYPE photo_analysis_duration_seconds histogram",
        f'photo_analysis_duration_seconds_bucket{{le="1"}} {d.le_1}',
        f'photo_analysis_duration_seconds_bucket{{le="5"}} {d.le_5}',
        f'photo_analysis_duration_seconds_bucket{{le="10"}} {d.le_10}',
        f'photo_analysis_duration_seconds_bucket{{le="30"}} {d.le_30}',
        f'photo_analysis_duration_seconds_bucket{{le="60"}} {d.le_60}',
        f'photo_analysis_duration_seconds_bucket{{le="120"}} {d.le_120}',
        f'photo_analysis_duration_seconds_bucket{{le="+Inf"}} {d.tot}',
        f"photo_analysis_duration_seconds_count {d.tot}",
        f"photo_analysis_duration_seconds_sum {d.total_dur}",
        "",
        "# HELP analyzer_grpc_errors_total Total gRPC analyzer retries",
        "# TYPE analyzer_grpc_errors_total counter",
        f"analyzer_grpc_errors_total {sum_attempts - count_attempted}",
        "",
        "# HELP worker_messages_processed_total Worker messages processed by result",
        "# TYPE worker_messages_processed_total counter",
        f'worker_messages_processed_total{{result="success"}} {done}',
        f'worker_messages_processed_total{{result="error"}} {failed}',
        "",
        "# HELP consumer_lag Photos waiting in queue (pending + processing)",
        "# TYPE consumer_lag gauge",
        f"consumer_lag {pending + processing}",
        "",
        "# HELP messages_in_queue Photos pending",
        "# TYPE messages_in_queue gauge",
        f"messages_in_queue {pending}",
    ]

    return "\n".join(lines)
