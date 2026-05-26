"""
services/pagination_service.py — pagination helpers
"""

PAGE_LIMIT = 50   # rows per page — matches your existing frontend


def get_page_params(args: dict) -> tuple[int, int, int]:
    """
    Extracts page, limit, offset from request args.
    Returns (page, limit, offset).
    """
    page   = max(1, int(args.get("page", 1)))
    limit  = PAGE_LIMIT
    offset = (page - 1) * limit
    return page, limit, offset


def calc_total_pages(total_rows: int, limit: int = PAGE_LIMIT) -> int:
    return max(1, (total_rows + limit - 1) // limit)