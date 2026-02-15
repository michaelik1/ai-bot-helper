from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import random
import statistics
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.types import Update

from src.bot.handlers.startup import handler_startup
from src.bot.handlers.models import handler_models
from src.bot.handlers.profile import handler_profile
from src.bot.handlers.rules_and_help import handler_rules
from src.bot.handlers.chat import handler_chat

from src.bot.services.user_manager import UserManager
from src.bot.services.api_manager import ApiManager
from src.mocks.mock_telegram_session import MockTelegramSession


# ----------------------------- helpers: updates -----------------------------

def _make_update(
    update_id: int,
    *,
    user_id: int,
    chat_id: int,
    text: str,
    message_id: int,
    entities: Optional[List[Dict[str, Any]]] = None,
) -> Update:
    payload: Dict[str, Any] = {
        "update_id": update_id,
        "message": {
            "message_id": message_id,
            "date": int(time.time()),
            "chat": {"id": chat_id, "type": "private"},
            "from": {"id": user_id, "is_bot": False, "first_name": "Load"},
            "text": text,
        },
    }
    if entities:
        payload["message"]["entities"] = entities
    return Update.model_validate(payload)


def make_start_update(update_id: int, *, user_id: int, chat_id: int) -> Update:
    return _make_update(
        update_id,
        user_id=user_id,
        chat_id=chat_id,
        text="/start",
        message_id=update_id,
        entities=[{"offset": 0, "length": 6, "type": "bot_command"}],
    )


def make_text_update(update_id: int, *, user_id: int, chat_id: int, text: str) -> Update:
    return _make_update(
        update_id,
        user_id=user_id,
        chat_id=chat_id,
        text=text,
        message_id=update_id,
    )


# ----------------------------- metrics -----------------------------

@dataclass
class Record:
    t_s: float
    user_id: int
    step: str
    latency_ms: float
    ok: bool
    error: str | None


def _pct(sorted_values: List[float], p: float) -> Optional[float]:
    if not sorted_values:
        return None
    if p <= 0:
        return sorted_values[0]
    if p >= 100:
        return sorted_values[-1]
    k = int(round((p / 100) * (len(sorted_values) - 1)))
    return sorted_values[k]


def summarize(latencies_ms: List[float], total_seconds: float, errors: int) -> Dict[str, Any]:
    lat = sorted(latencies_ms)
    ok = len(latencies_ms) - errors
    rps = ok / total_seconds if total_seconds > 0 else 0
    return {
        "total": len(latencies_ms),
        "ok": ok,
        "errors": errors,
        "seconds": total_seconds,
        "rps": rps,
        "avg_ms": statistics.mean(lat) if lat else None,
        "p50_ms": _pct(lat, 50),
        "p95_ms": _pct(lat, 95),
        "p99_ms": _pct(lat, 99),
        "max_ms": max(lat) if lat else None,
    }


def build_timeseries(records: List[Record]) -> List[Dict[str, Any]]:
    buckets: Dict[int, List[Record]] = {}
    for r in records:
        sec = int(r.t_s)
        buckets.setdefault(sec, []).append(r)

    out: List[Dict[str, Any]] = []
    for sec in sorted(buckets.keys()):
        rs = buckets[sec]
        lat = sorted([x.latency_ms for x in rs if x.ok])
        errors = sum(0 if x.ok else 1 for x in rs)
        out.append(
            {
                "t_s": sec,
                "count": len(rs),
                "errors": errors,
                "avg_ms": statistics.mean(lat) if lat else None,
                "p50_ms": _pct(lat, 50),
                "p95_ms": _pct(lat, 95),
                "p99_ms": _pct(lat, 99),
                "max_ms": max(lat) if lat else None,
            }
        )
    return out


# ----------------------------- load scenario -----------------------------

async def feed_and_measure(
    *,
    dp: Dispatcher,
    bot: Bot,
    upd: Update,
    t0: float,
    user_id: int,
    step: str,
) -> Record:
    start = time.perf_counter()
    err: str | None = None
    ok = True
    try:
        await dp.feed_update(bot, upd)
    except Exception as e:
        ok = False
        err = f"{type(e).__name__}: {e}"
    latency_ms = (time.perf_counter() - start) * 1000
    return Record(t_s=time.perf_counter() - t0, user_id=user_id, step=step, latency_ms=latency_ms, ok=ok, error=err)


async def virtual_user(
    *,
    dp: Dispatcher,
    bot: Bot,
    t0: float,
    user_id: int,
    chat_id: int,
    turns: int,
    think_time_ms: int,
    start_delay_s: float,
    record_sink: List[Record],
    csv_writer: csv.DictWriter,
    csv_lock: asyncio.Lock,
    update_id_base: int,
):
    if start_delay_s:
        await asyncio.sleep(start_delay_s)

    upd_id = update_id_base

    async def _do(step: str, upd: Update):
        rec = await feed_and_measure(dp=dp, bot=bot, upd=upd, t0=t0, user_id=user_id, step=step)
        record_sink.append(rec)
        async with csv_lock:
            csv_writer.writerow(
                {
                    "t_s": f"{rec.t_s:.6f}",
                    "user_id": rec.user_id,
                    "step": rec.step,
                    "latency_ms": f"{rec.latency_ms:.3f}",
                    "ok": int(rec.ok),
                    "error": rec.error or "",
                }
            )

    # 1 /start
    await _do("start", make_start_update(upd_id, user_id=user_id, chat_id=chat_id))
    upd_id += 1

    # 2 Новый чат FSM waiting_for_exit
    await _do("new_chat", make_text_update(upd_id, user_id=user_id, chat_id=chat_id, text="💬Новый чат"))
    upd_id += 1

    # 3 несколько сообщений в активном чате
    sample_texts = [
        "Привет!",
        "Объясни простыми словами, что такое нагрузочное тестирование?",
        "Сгенерируй короткий план урока.",
        "Напиши 3 идеи для домашнего задания.",
        "Сделай краткое резюме текста (тест).",
    ]

    for _ in range(turns):
        text = random.choice(sample_texts)
        await _do("chat_msg", make_text_update(upd_id, user_id=user_id, chat_id=chat_id, text=text))
        upd_id += 1
        if think_time_ms:
            await asyncio.sleep(think_time_ms / 1000)

    # 4 "❌Завершить чат" (clear state)
    await _do("exit_chat", make_text_update(upd_id, user_id=user_id, chat_id=chat_id, text="❌Завершить чат"))


async def run_load(
    *,
    users: int,
    turns: int,
    ramp_up_s: float,
    think_time_ms: int,
    tg_delay_ms: int,
    db_delay_ms: int,
    llm_delay_ms: int,
    out_dir: Path,
) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    raw_csv_path = out_dir / f"raw_{run_id}.csv"
    timeseries_csv_path = out_dir / f"timeseries_{run_id}.csv"
    summary_json_path = out_dir / f"summary_{run_id}.json"

    bot_key = os.getenv("TGBOT_KEY", "TEST:TOKEN")
    bot = Bot(token=bot_key, session=MockTelegramSession(delay_ms=tg_delay_ms))

    dp = Dispatcher()
    dp.include_routers(handler_startup, handler_models, handler_profile, handler_rules, handler_chat)

    UserManager.setup(mock=True, mock_delay_ms=db_delay_ms)
    ApiManager.setup(mock=True, mock_delay_ms=llm_delay_ms)

    try:
        await dp.emit_startup(bot)
    except Exception:
        pass

    records: List[Record] = []
    csv_lock = asyncio.Lock()

    t0 = time.perf_counter()
    with raw_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["t_s", "user_id", "step", "latency_ms", "ok", "error"])
        writer.writeheader()

        tasks = []
        step_delay = (ramp_up_s / users) if (users > 0 and ramp_up_s > 0) else 0.0

        for u in range(users):
            user_id = 10_000 + u
            chat_id = 20_000 + u
            start_delay_s = u * step_delay
            update_id_base = 1_000_000 + (u * 10_000)
            tasks.append(
                asyncio.create_task(
                    virtual_user(
                        dp=dp,
                        bot=bot,
                        t0=t0,
                        user_id=user_id,
                        chat_id=chat_id,
                        turns=turns,
                        think_time_ms=think_time_ms,
                        start_delay_s=start_delay_s,
                        record_sink=records,
                        csv_writer=writer,
                        csv_lock=csv_lock,
                        update_id_base=update_id_base,
                    )
                )
            )

        await asyncio.gather(*tasks)

    total_seconds = time.perf_counter() - t0
    latencies = [r.latency_ms for r in records]
    errors = sum(0 if r.ok else 1 for r in records)
    summary = summarize(latencies, total_seconds=total_seconds, errors=errors)

    ts = build_timeseries(records)
    with timeseries_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["t_s", "count", "errors", "avg_ms", "p50_ms", "p95_ms", "p99_ms", "max_ms"])
        writer.writeheader()
        for row in ts:
            writer.writerow(row)

    payload = {
        "run_id": run_id,
        "params": {
            "users": users,
            "turns": turns,
            "ramp_up_s": ramp_up_s,
            "think_time_ms": think_time_ms,
            "tg_delay_ms": tg_delay_ms,
            "db_delay_ms": db_delay_ms,
            "llm_delay_ms": llm_delay_ms,
        },
        "summary": summary,
        "files": {
            "raw_csv": str(raw_csv_path),
            "timeseries_csv": str(timeseries_csv_path),
            "summary_json": str(summary_json_path),
        },
    }
    summary_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        await dp.emit_shutdown(bot)
    except Exception:
        pass
    await bot.session.close()

    return payload


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Local load-test for aiogram bot (feed_update)")
    p.add_argument("--users", type=int, default=int(os.getenv("LOAD_USERS", "50")), help="Сколько виртуальных пользователей")
    p.add_argument("--turns", type=int, default=int(os.getenv("LOAD_TURNS", "5")), help="Сколько сообщений в чате на пользователя")
    p.add_argument("--ramp-up-s", type=float, default=float(os.getenv("LOAD_RAMP_UP_S", "0")), help="Плавный старт пользователей (секунды)")
    p.add_argument("--think-time-ms", type=int, default=int(os.getenv("LOAD_THINK_MS", "0")), help="Пауза между сообщениями пользователя")

    p.add_argument("--tg-delay-ms", type=int, default=int(os.getenv("MOCK_TG_DELAY_MS", "0")), help="Задержка Telegram API мока")
    p.add_argument("--db-delay-ms", type=int, default=int(os.getenv("MOCK_BD_DELAY_MS", "0")), help="Задержка БД мока")
    p.add_argument("--llm-delay-ms", type=int, default=int(os.getenv("MOCK_LLM_DELAY_MS", "0")), help="Задержка LLM/API мока")

    p.add_argument("--out-dir", type=str, default=os.getenv("LOAD_OUT_DIR", "load_results"), help="Куда сохранять CSV/JSON")
    return p.parse_args()


async def _amain() -> None:
    load_dotenv()
    args = parse_args()

    out = await run_load(
        users=args.users,
        turns=args.turns,
        ramp_up_s=args.ramp_up_s,
        think_time_ms=args.think_time_ms,
        tg_delay_ms=args.tg_delay_ms,
        db_delay_ms=args.db_delay_ms,
        llm_delay_ms=args.llm_delay_ms,
        out_dir=Path(args.out_dir),
    )

    print(json.dumps({"run_id": out["run_id"], "summary": out["summary"], "files": out["files"]}, ensure_ascii=False, indent=2))


def main() -> None:
    try:
        asyncio.run(_amain())
    except KeyboardInterrupt:
        print("Keyboard interrupt")


if __name__ == "__main__":
    main()
