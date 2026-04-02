# Copyright (c) 2026, Arkan Labs and contributors
# auracrm/scripts/bench_health_check.py
# bench execute auracrm.scripts.bench_health_check.run_full_check

import subprocess
import frappe
from frappe import _


def run_full_check():
    """
    Comprehensive bench health-check. Returns a dict with results.
    bench execute auracrm.scripts.bench_health_check.run_full_check
    """
    results = {
        "redis": _check_redis(),
        "database": _check_database(),
        "missing_tables": _check_missing_tables(),
        "zombie_processes": _kill_zombie_processes(),
        "scheduler": _check_scheduler(),
        "disk_space": _check_disk_space(),
    }

    all_ok = all(v.get("status") == "ok" for v in results.values())
    results["overall"] = "✅ All checks passed" if all_ok else "⚠️ Some checks failed"

    for key, val in results.items():
        status = val.get("status", "") if isinstance(val, dict) else ""
        icon = "✅" if status == "ok" else ("⚠️" if status == "warning" else "❌" if status == "error" else "ℹ️")
        msg = val.get("message", val) if isinstance(val, dict) else val
        print(f"  {icon} {key}: {msg}")

    return results


def _check_redis():
    """Verify Redis connectivity."""
    try:
        cache = frappe.cache()
        cache.set_value("_health_check", "ok")
        val = cache.get_value("_health_check")
        cache.delete_value("_health_check")
        if val == "ok":
            return {"status": "ok", "message": "Redis responding"}
        return {"status": "error", "message": "Redis read/write mismatch"}
    except Exception as e:
        return {"status": "error", "message": f"Redis error: {str(e)}"}


def _check_database():
    """Verify DB connectivity and query performance."""
    try:
        start = frappe.utils.now_datetime()
        frappe.db.sql("SELECT 1")
        elapsed = (frappe.utils.now_datetime() - start).total_seconds()
        if elapsed > 1:
            return {"status": "warning", "message": f"DB slow: {elapsed:.2f}s"}
        return {"status": "ok", "message": f"DB responding ({elapsed:.3f}s)"}
    except Exception as e:
        return {"status": "error", "message": f"DB error: {str(e)}"}


def _check_missing_tables():
    """Check for DocTypes that are missing their database tables."""
    missing = []
    try:
        # Get all AuraCRM and CAPS DocTypes
        doctypes = frappe.db.sql("""
            SELECT name FROM `tabDocType`
            WHERE module IN ('AuraCRM', 'CAPS')
            AND is_virtual = 0
            AND issingle = 0
        """, as_dict=True)

        for dt in doctypes:
            table_name = f"tab{dt['name']}"
            exists = frappe.db.sql(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = %s AND table_schema = DATABASE()",
                table_name,
            )
            if not exists or exists[0][0] == 0:
                missing.append(dt["name"])

        if missing:
            return {"status": "warning", "message": f"Missing tables: {', '.join(missing)}"}
        return {"status": "ok", "message": f"All {len(doctypes)} tables present"}
    except Exception as e:
        return {"status": "error", "message": f"Check error: {str(e)}"}


def _kill_zombie_processes():
    """Detect and report zombie bench processes."""
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True, text=True, timeout=5,
        )
        zombies = [
            line for line in result.stdout.split("\n")
            if "defunct" in line.lower() or "<defunct>" in line
        ]
        if zombies:
            return {"status": "warning", "message": f"{len(zombies)} zombie process(es) found"}
        return {"status": "ok", "message": "No zombie processes"}
    except Exception as e:
        return {"status": "error", "message": f"Process check error: {str(e)}"}


def _check_scheduler():
    """Check if scheduler is active."""
    try:
        is_active = frappe.utils.scheduler.is_scheduler_inactive()
        if is_active:
            return {"status": "warning", "message": "Scheduler is INACTIVE"}
        return {"status": "ok", "message": "Scheduler active"}
    except Exception as e:
        return {"status": "error", "message": f"Scheduler check error: {str(e)}"}


def _check_disk_space():
    """Check available disk space."""
    try:
        result = subprocess.run(
            ["df", "-h", "/"],
            capture_output=True, text=True, timeout=5,
        )
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:
            parts = lines[1].split()
            usage_pct = int(parts[4].replace("%", "")) if len(parts) >= 5 else 0
            if usage_pct > 90:
                return {"status": "error", "message": f"Disk {usage_pct}% full!"}
            elif usage_pct > 75:
                return {"status": "warning", "message": f"Disk {usage_pct}% used"}
            return {"status": "ok", "message": f"Disk {usage_pct}% used"}
        return {"status": "warning", "message": "Could not parse disk info"}
    except Exception as e:
        return {"status": "error", "message": f"Disk check error: {str(e)}"}
