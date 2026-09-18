from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from app.models.schemas import DailyReportResponse, MonthlyReportResponse, ProfitReportResponse
from app.core.security import require_role
from app.services.report_service import (
    calculate_daily_report, calculate_monthly_report, calculate_profit_report,
    generate_pdf_report, generate_excel_report
)

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/daily", response_model=DailyReportResponse)
def get_daily_report(current_user: dict = Depends(require_role("owner"))):
    owner_id = current_user["uid"]
    return calculate_daily_report(owner_id)

@router.get("/monthly", response_model=MonthlyReportResponse)
def get_monthly_report(current_user: dict = Depends(require_role("owner"))):
    owner_id = current_user["uid"]
    return calculate_monthly_report(owner_id)

@router.get("/profit", response_model=ProfitReportResponse)
def get_profit_report(current_user: dict = Depends(require_role("owner"))):
    owner_id = current_user["uid"]
    return calculate_profit_report(owner_id)

@router.get("/export/pdf")
def export_pdf(current_user: dict = Depends(require_role("owner"))):
    owner_id = current_user["uid"]
    pdf_bytes = generate_pdf_report(owner_id)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=fleet_report.pdf"}
    )

import io # Ensure io is imported for StreamingResponse BytesIO

@router.get("/export/excel")
def export_excel(current_user: dict = Depends(require_role("owner"))):
    owner_id = current_user["uid"]
    excel_bytes = generate_excel_report(owner_id)
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=fleet_report.xlsx"}
    )
