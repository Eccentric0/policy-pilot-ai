from __future__ import annotations

from .tools import (
    calculate_reimbursement as calculate_reimbursement_impl,
    get_employee_leave_balance as get_employee_leave_balance_impl,
    get_expense_record as get_expense_record_impl,
)

try:
    try:
        from mcp.server.fastmcp import FastMCP as _MCPServer
    except ModuleNotFoundError:
        from mcp.server.mcpserver import MCPServer as _MCPServer

    mcp = _MCPServer("Enterprise Expense Tools", version="0.1.0")

    @mcp.tool(name="get_employee_leave_balance")
    def employee_leave_balance(employee_id: str) -> dict:
        """查询员工剩余年假，只读操作。"""
        return get_employee_leave_balance_impl(employee_id)

    @mcp.tool(name="calculate_reimbursement")
    def reimbursement_calculator(
        expense_items: list[dict], employee_level: str, city_tier: str
    ) -> dict:
        """按照职级和城市等级计算报销额度，只读操作。"""
        return calculate_reimbursement_impl(expense_items, employee_level, city_tier)

    @mcp.tool(name="get_expense_record")
    def expense_record(expense_id: str) -> dict:
        """查询模拟报销记录，只读操作。"""
        return get_expense_record_impl(expense_id)

except ImportError:  # pragma: no cover - permits local smoke tests without MCP installed
    mcp = None


def main() -> None:
    if mcp is None:
        raise RuntimeError("请安装 mcp[cli] 后运行 MCP Server")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
