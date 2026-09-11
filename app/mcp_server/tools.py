from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(filename: str) -> Any:
    root = Path(__file__).resolve().parents[2] / "data"
    return json.loads((root / filename).read_text(encoding="utf-8"))


def get_employee_leave_balance(employee_id: str) -> dict[str, Any]:
    employees = _load_json("employees.json")
    employee = next((item for item in employees if item["employee_id"] == employee_id), None)
    if not employee:
        return {
            "success": False,
            "data": None,
            "error_code": "EMPLOYEE_NOT_FOUND",
            "message": f"未找到员工 {employee_id}",
            "source": "employees.json",
        }
    return {
        "success": True,
        "data": {
            "employee_id": employee["employee_id"],
            "department": employee["department"],
            "level": employee["level"],
            "annual_leave_days": employee["annual_leave_days"],
            "used_leave_days": employee["used_leave_days"],
            "remaining_leave_days": employee["remaining_leave_days"],
        },
        "error_code": None,
        "message": "查询成功",
        "source": "employees.json",
    }


def calculate_reimbursement(
    expense_items: list[dict[str, Any]], employee_level: str, city_tier: str
) -> dict[str, Any]:
    limits = {
        "P1": {"住宿": 600, "交通": 300, "餐补": 150},
        "P2": {"住宿": 450, "交通": 250, "餐补": 120},
        "P3": {"住宿": 350, "交通": 200, "餐补": 100},
    }
    tier_multiplier = {"一线": 1.2, "二线": 1.0, "三线": 0.85}.get(city_tier, 1.0)
    level_limits = limits.get(employee_level, limits["P3"])
    details = []
    total = 0.0
    for item in expense_items:
        category = str(item.get("category", "其他"))
        amount = float(item.get("amount", 0))
        base_limit = level_limits.get(category, 0)
        limit = round(base_limit * tier_multiplier, 2) if base_limit else 0
        approved = min(amount, limit) if limit else 0
        details.append(
            {
                "category": category,
                "submitted": amount,
                "limit": limit,
                "approved": approved,
                "rejected": round(amount - approved, 2),
            }
        )
        total += approved
    return {
        "success": True,
        "data": {
            "employee_level": employee_level,
            "city_tier": city_tier,
            "details": details,
            "approved_total": round(total, 2),
        },
        "error_code": None,
        "message": "计算成功",
        "source": "reimbursement_rules.pdf",
    }


def get_expense_record(expense_id: str) -> dict[str, Any]:
    records = _load_json("expense_records.json")
    record = next((item for item in records if item["expense_id"] == expense_id), None)
    if not record:
        return {
            "success": False,
            "data": None,
            "error_code": "EXPENSE_NOT_FOUND",
            "message": f"未找到报销单 {expense_id}",
            "source": "expense_records.json",
        }
    return {
        "success": True,
        "data": record,
        "error_code": None,
        "message": "查询成功",
        "source": "expense_records.json",
    }


TOOL_REGISTRY = {
    "get_employee_leave_balance": get_employee_leave_balance,
    "calculate_reimbursement": calculate_reimbursement,
    "get_expense_record": get_expense_record,
}
