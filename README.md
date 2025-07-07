# checkbox
A user can fill the document with the help of tkinter exe file. We can see the log of users whoever have opened the file and made the changes in it.

# 📘 FastAPI-Based Editor Log Extraction API

A lightweight REST API built with **FastAPI** to extract and filter **editor logs** from a MySQL database. Supports querying by a specific date or a date range to track document activity efficiently.

## ✅ Features

- Fetch editor logs by:
  - A single date: `?date=YYYY-MM-DD`
  - A date range: `?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD`
- Returns logs with:
  - `emp_id`, `emp_name`, `order_id`, `open_datetime`, and `submit_datetime`
- Built-in Swagger UI documentation at `/docs`
- Error handling for missing parameters, bad inputs, and no data found
- Ready for integration with dashboards or frontend filters

## 🚀 Tech Stack

- **FastAPI** (Python 3.x)
- **MySQL** for backend storage
- **Pydantic** for schema validation
- **Uvicorn** as the ASGI server

## 🔧 Setup Instructions

1. Install dependencies:

```bash
pip install fastapi uvicorn mysql-connector-python
