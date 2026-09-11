from app.mcp_server.tools import calculate_reimbursement, get_employee_leave_balance


def test_leave_balance_success():
    result = get_employee_leave_balance("E1001")
    assert result["success"] is True
    assert result["data"]["remaining_leave_days"] == 6


def test_leave_balance_not_found():
    result = get_employee_leave_balance("E9999")
    assert result["success"] is False
    assert result["error_code"] == "EMPLOYEE_NOT_FOUND"


def test_reimbursement_limit():
    result = calculate_reimbursement([{"category": "住宿", "amount": 500}], "P2", "二线")
    assert result["data"]["approved_total"] == 450
