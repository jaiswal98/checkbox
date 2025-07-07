from fastapi import FastAPI, Query, HTTPException
from typing import List, Optional
import mysql.connector
from pydantic import BaseModel
from datetime import datetime, date

app = FastAPI()

# Pydantic model
class EditorLog(BaseModel):
    emp_id: str
    emp_name: str
    order_id: str
    open_datetime: datetime
    submit_datetime: datetime

# MySQL DB connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root@123",
        database="doc_workflow"
    )

# Enhanced Route with optional date range
@app.get(
    "/editor-logs-by-date",
    response_model=List[EditorLog],
    summary="Fetch editor logs by date or date range",
    description="""
    This endpoint returns editor logs based on:
    - a specific date (`date=YYYY-MM-DD`)
    - or a date range (`from_date` and `to_date`)
    
    You may pass either `date` OR (`from_date` and `to_date`) — not both.
    """,
    tags=["Editor Logs"],
    responses={
        404: {"description": "No logs found for the given date or range"},
        500: {"description": "Internal server or database error"}
    }
)
def get_editor_logs(
    date: Optional[date] = Query(None, description="Filter logs by a specific date"),
    from_date: Optional[date] = Query(None, description="Start of date range"),
    to_date: Optional[date] = Query(None, description="End of date range")
):
    try:
        if date and (from_date or to_date):
            raise HTTPException(status_code=400, detail="Provide either 'date' OR 'from_date' + 'to_date', not both.")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # SQL logic
        if date:
            query = """
                SELECT emp_id, emp_name, order_id, open_datetime, submit_datetime
                FROM editor_logs
                WHERE DATE(open_datetime) = %s
            """
            cursor.execute(query, (date,))
        elif from_date and to_date:
            query = """
                SELECT emp_id, emp_name, order_id, open_datetime, submit_datetime
                FROM editor_logs
                WHERE DATE(open_datetime) BETWEEN %s AND %s
            """
            cursor.execute(query, (from_date, to_date))
        else:
            raise HTTPException(status_code=400, detail="Provide either 'date' or 'from_date' and 'to_date'")

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            raise HTTPException(status_code=404, detail="No logs found for the given filter")

        return rows

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"MySQL Error: {err}")
