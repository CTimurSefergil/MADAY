import os
from fastapi import FastAPI, UploadFile, Form, File
from datetime import datetime, date
import ai_analyzer
import database
import image_information
from fastapi import HTTPException
from typing import List

app = FastAPI()

os.makedirs("static", exist_ok=True)


@app.post("/upload")
async def upload_image(
        files: List[UploadFile] = File(...),
        user_id: str = Form(...),
        timestamp: str = Form(default=None)
):
    results = []
    errors = []

    safe_timestamp = timestamp or datetime.now().isoformat()

    for index, file in enumerate(files):
        try:
            file_content = await file.read()

            file_name = f"{user_id}_{safe_timestamp.replace(':', '-')}_{index}.jpg"
            file_path = f"static/{file_name}"

            with open(file_path, "wb") as buffer:
                buffer.write(file_content)

            capture_time = image_information.get_capture_time(file_path)

            try:
                analysis = ai_analyzer.analyze_image(file_path)
            except Exception as e:
                errors.append({"file": file.filename, "error": f"AI analiz hatası: {str(e)}"})
                os.remove(file_path)
                continue

            try:
                database.save_analysis(
                    user_id=user_id,
                    capture_time=capture_time,
                    activity=analysis.get("activity", "unknown"),
                    objects=analysis.get("objects", []),
                    environment=analysis.get("environment", "unknown"),
                    confidence_scores=analysis.get("confidence_scores", {
                        "activity": 1,
                        "objects": 1,
                        "environment": 1
                    }),
                    needs_clarification=analysis.get("needs_clarification", True)
                )
            except Exception as e:
                errors.append({"file": file.filename, "error": f"Veritabanı hatası: {str(e)}"})
                os.remove(file_path)
                continue

            os.remove(file_path)

            results.append({
                "filename": file.filename,
                "status": "success",
                "analysis": analysis,
                "timestamp": capture_time
            })

        except Exception as e:
            errors.append({"file": file.filename, "error": f"İşleme hatası: {str(e)}"})

    return {
        "status": "success" if not errors else "partial_success" if results else "error",
        "processed": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }


@app.get("/daily/{user_id}/{target_date}")
async def get_daily_summary(user_id: str, target_date: str):
    try:
        try:
            parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            date_str = target_date
        except ValueError:
            raise HTTPException(400, detail="Invalid date format. Use YYYY-MM-DD")

        analyses = database.get_daily_analyses(user_id, date_str)

        if not analyses:
            raise HTTPException(404, detail="No data found for this date")

        summary = ai_analyzer.generate_daily_summary(analyses)

        database.save_daily_summary(user_id, date_str, summary)
        database.mark_analyses_deleted(user_id, date_str)

        return {
            "status": "success",
            "summary": summary,
            "original_count": len(analyses)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))